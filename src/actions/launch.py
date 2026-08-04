import subprocess
import shutil
import sys
import os
import tomlkit
from invoke import run
from pathlib import Path

def action_launch(logger, opts, config):
    logger.info("Performing pre-flight checks...")
    
    env = os.environ.copy()

    CONFIG_GAME = config.get("game")
    CONFIG_GAME_DIR = Path(opts.game_dir or CONFIG_GAME.get("path")).expanduser()

    # game directory sanity check
    if not CONFIG_GAME_DIR.exists():
        logger.fatal(f"The game folder ({CONFIG_GAME_DIR}) does not exist! Maybe you forgot to set the directory in the configuration file or command arguments?")
        sys.exit(1)
    env.update({ "WINEPREFIX": str(CONFIG_GAME_DIR) })
    logger.debug(f"Using game directory: {CONFIG_GAME_DIR}")

    CONFIG_GAMEMODE = CONFIG_GAME.get("gamemode") or opts.gamemode

    CONFIG_GRAPHICS = CONFIG_GAME.get("graphics")
    CONFIG_GRAPHICS_SHADERS = CONFIG_GRAPHICS.get("shaders")
    
    gpu_vendors = []
    if opts.override_gpu_vendor:
        gpu_vendors.append(opts.override_gpu_vendor)
    else:
        VENDORS = { "0x10de": "nvidia", "0x1002": "amd", "0x8086": "intel" }
        for vendor_file in Path("/sys/class/drm").glob("card*/device/vendor"):
            vendor = vendor_file.read_text().strip()
            if vendor in VENDORS:
                gpu_vendors.append(VENDORS[vendor])
    
    if "nvidia" in gpu_vendors:
        # NVIDIA shader settings.
        shader_size_raw = str(CONFIG_GRAPHICS_SHADERS.get("cache_size", "")).strip().lower()
        units = {"g": 1024 ** 3, "m": 1024 ** 2}
        try:
            shader_size = int(float(shader_size_raw[:-1]) * units[shader_size_raw[-1]])
        except (IndexError, KeyError, ValueError):
            logger.warning(
                f"Invalid NVIDIA shader cache size {shader_size_raw!r}; using the driver default"
            )
            shader_size = None

        nvidia_shader_env = {
            # Avoid clearing cache when restarting the game
            "__GL_SHADER_DISK_CACHE": "1",
            "__GL_SHADER_DISK_CACHE_SKIP_CLEANUP": "1",
            "__GL_SHADER_DISK_CACHE_PATH": f"{CONFIG_GAME_DIR}/shader_cache",
            "PROTON_FSR4_UPGRADE": "1" # Prevent downloading AMD FSR drivers when we're clearly running a non-AMD GPU
        }
        if shader_size is not None:
            nvidia_shader_env["__GL_SHADER_DISK_CACHE_SIZE"] = str(shader_size)
        env.update(nvidia_shader_env)
        logger.debug("Applied NVIDIA shader settings")

    env.update({
        "MESA_SHADER_CACHE_DIR": f"{CONFIG_GAME_DIR}/shader_cache",
        "MESA_SHADER_CACHE_MAX_SIZE": str(CONFIG_GRAPHICS_SHADERS.get("cache_size", "")),
    })
    logger.debug("Applied Mesa (AMD/Intel/Noveau) shader settings")
    
    CONFIG_PROTON = CONFIG_GAME.get("proton")
    CONFIG_PROTON_ENABLED =  opts.proton or CONFIG_PROTON.get("enabled")
    if CONFIG_PROTON_ENABLED:
        if not shutil.which("umu-run"):
            logger.fatal("umu-run is required but was not found on the system")
            sys.exit(127)
        else: 
            logger.debug("umu-run is present on the system")
        logger.info("Launching game with Proton")
        CONFIG_PROTON_FIXES = opts.proton_fixes or CONFIG_PROTON.get("fixes")
        CONFIG_PROTON_SYNC =  opts.proton_sync or CONFIG_PROTON.get("sync")
        CONFIG_PROTON_RENDERER = CONFIG_PROTON.get("renderer")
        CONFIG_PROTON_RENDERER_OPENGL = opts.proton_renderer_opengl or CONFIG_PROTON_RENDERER.get("opengl")

        match (opts.proton_fixes or CONFIG_PROTON.get("fixes")):
            case "starcitizen":
                env.update({ "GAMEID": "umu-starcitizen" })
                logger.debug("\"umu-starcitizen\" proton fixes will be applied")
            case "default":
                logger.debug("Default proton fixes will be applied")
            case "none":
                env.update({ "PROTONFIXES_DISABLE": "1" })
                logger.debug("No proton fixes will be applied")
            case _:
                logger.warn(f"Unknown proton fixes value: {CONFIG_PROTON_FIXES}")

        if CONFIG_PROTON_RENDERER_OPENGL:
            env.update({ "PROTON_USE_WINED3D": "1" })
            logger.debug("Using WINED3D (OpenGL) Proton renderer")
        else:
            logger.debug("Using DXVK (Vulkan) Proton renderer")

        match (CONFIG_PROTON_SYNC):
            case "ntsync":
                env.update({ "PROTON_NO_NTSYNC": "0", "PROTON_NO_FSYNC": "1", "PROTON_NO_ESYNC": "1" })
                logger.debug("Using NTSYNC sync implementation")
            case "fsync":
                env.update({ "PROTON_NO_NTSYNC": "1", "PROTON_NO_FSYNC": "0", "PROTON_NO_ESYNC": "1" })
                logger.debug("Using FSYNC sync implementation")
            case "esync":
                # Some runners (i.e. umu's default runner) still only support esync
                env.update({ "PROTON_NO_NTSYNC": "1", "PROTON_NO_FSYNC": "1", "PROTON_NO_ESYNC": "0" })
                logger.debug("Using ESYNC sync implementation")
            case _:
                logger.debug("Sync implementation not specified or unknown, ignoring & using default")

        def proton_runner_resolve():
            runner = opts.proton_runner or CONFIG_PROTON.get("runner")

            if not runner:
                logger.debug("umu's default proton runner will be used")
                return

            proton_paths = [
                Path("/usr/share/steam/compatibilitytools.d"),
                Path("/usr/lib/steam/compatibilitytools.d"),
                Path.home() / ".steam/root/compatibilitytools.d",
                Path.home() / ".local/share/Steam/compatibilitytools.d",
                Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam/compatibilitytools.d",
            ]

            runners = {}

            for path in proton_paths:
                if path.exists():
                    for runner_path in path.iterdir():
                        if runner_path.is_dir():
                            runners[runner_path.name] = runner_path

            logger.debug(f"Found Proton runners: {list(runners)}")

            if runner in runners:
                proton_path = runners[runner]
            else:
                proton_path = Path(runner).expanduser().resolve()

            proton_binary = proton_path / "proton"

            if not proton_binary.is_file() or not os.access(proton_binary, os.X_OK):
                raise FileNotFoundError(f"Invalid Proton runner: {proton_path}")

            env.update({"PROTONPATH": str(proton_path)})
            logger.debug(f"{runner} Proton runner will be used")

        proton_runner_resolve()
    else:
        logger.info("Launching game with Wine")
        CONFIG_WINE = config.get("wine") or {}
        CONFIG_WINE_RUNNER = opts.runner or CONFIG_WINE.get("runner")
        with (CONFIG_GAME_DIR / "wine_runners/runners.toml").open("rb") as f:
            wine_runners = tomlkit.load(f)
        if CONFIG_WINE_RUNNER not in wine_runners:
            logger.fatal(f"Wine runner '{CONFIG_WINE_RUNNER}' not found in runners.toml")
            sys.exit(1)
        WINE_RUNNER = CONFIG_GAME_DIR / "wine_runners" / wine_runners[CONFIG_WINE_RUNNER]["folder"] / "bin/wine"
        logger.debug(f"{CONFIG_WINE_RUNNER} Wine runner will be used")
    env.update({ "WINEDLLOVERRIDES": "winemenubuilder.exe=d" })
    logger.debug(f"Environment: {env}")

    logger.info("Liftoff!")
    logger.debug("Launching game.")
    if opts.verbose:
        print("=" * shutil.get_terminal_size().columns)

    # MARK: run game
    process = subprocess.Popen(
        [
            *(["gamemoderun"] if CONFIG_GAMEMODE else []),
            *(["umu-run"] if CONFIG_PROTON_ENABLED else [WINE_RUNNER]),
            #f"{CONFIG_GAME_DIR}/drive_c/Program Files/Roberts Space Industries/RSI Launcher/RSI Launcher.exe"
            # Using the Windows path tends to be more reliable
            "C:\\Program Files\\Roberts Space Industries\\RSI Launcher\\RSI Launcher.exe"
        ],
        env=env,
        stdout=subprocess.DEVNULL if not opts.verbose else None,
        stderr=subprocess.DEVNULL if not opts.verbose else None,
    )
    try:
        result = process.wait()
    except KeyboardInterrupt:
        logger.warning("Game closed by user")
        process.terminate()
        return

    sys.exit(result)