import subprocess
import shutil
import sys
import os
from pathlib import Path

def action_launch(logger, opts, config):
    sg.one_line_progress_meter("Starting game...", 1, 5, "testing", no_button=True, orientation="h")
    logger.info("Performing pre-flight checks...")
    if not shutil.which("umu-run"):
        logger.fatal("umu-run is required but was not found on the system")
        sys.exit(127)
    else: 
        logger.debug("umu-run is present on the system")
    
    env = os.environ.copy()

    CONFIG_GAME = config.get("game")
    CONFIG_GAME_DIR = Path(opts.game_dir or CONFIG_GAME.get("path")).expanduser()

    # game directory sanity check
    if not CONFIG_GAME_DIR.exists():
        logger.fatal(f"The game folder ({CONFIG_GAME_DIR}) does not exist! Maybe you forgot to set the directory in the configuration file or command arguments?")
        sys.exit(1)
    env.update({ "WINEPREFIX": str(CONFIG_GAME_DIR) })
    logger.debug(f"Using game directory: {CONFIG_GAME_DIR}")

    CONFIG_GRAPHICS = CONFIG_GAME.get("graphics")
    CONFIG_GRAPHICS_SHADERS = CONFIG_GRAPHICS.get("shaders")
    
    gpu_vendors = []
    if opts.override_gpu_vendor:
        found.append(opts.override_gpu_vendor)
    else:
        VENDORS = { "0x10de": "nvidia", "0x1002": "amd", "0x8086": "intel" }
        for vendor_file in Path("/sys/class/drm").glob("card*/device/vendor"):
            vendor = vendor_file.read_text().strip()
            if vendor in VENDORS:
                gpu_vendors.append(VENDORS[vendor])
    
    if "nvidia" in gpu_vendors:
        # NVIDIA shader settings.
        shader_size_raw = CONFIG_GRAPHICS_SHADERS.get('cache_size').strip().lower()
        UNITS = { "g": 1024 ** 3, "m": 1024 ** 2 }
        if shader_size_raw[-1] in UNITS:
            shader_size = int(float(shader_size_raw[:-1]) * UNITS[shader_size_raw[-1]])

        env.update({
            # Avoid clearing cache when restarting the game
            "__GL_SHADER_DISK_CACHE": "1",
            "__GL_SHADER_DISK_CACHE_SKIP_CLEANUP": "1",
            "__GL_SHADER_DISK_CACHE_PATH": f"{CONFIG_GAME_DIR}/shader_cache",
            "__GL_SHADER_DISK_CACHE_SIZE": f"{shader_size}" 
        })
        logger.debug("Applied NVIDIA shader settings")
    else:
        # Mesa shader settings. (AMD/Intel)
        env.update({
            "MESA_SHADER_CACHE_DIR": f"{CONFIG_GAME_DIR}/shader_cache",
            "MESA_SHADER_CACHE_MAX_SIZE": f"{CONFIG_GRAPHICS_SHADERS.get('shader_cache')}"
        })
        logger.debug("Applied Mesa (AMD/Intel) shader settings")
    
    CONFIG_PROTON = CONFIG_GAME.get("proton")
    CONFIG_PROTON_FIXES = opts.proton_fixes or CONFIG_PROTON.get("fixes")
    CONFIG_PROTON_SYNC = opts.proton_sync or CONFIG_PROTON.get("sync")
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

    logger.info("Liftoff!")
    logger.debug("Launching game.")
    print("=" * shutil.get_terminal_size().columns)

    # MARK: run game
    proton_runner_resolve()
    env.update({ "WINEDLLOVERRIDES": "nvcuda=n,winemenubuilder.exe=d" })
    process = subprocess.Popen(
        [
            "umu-run",
            f"{CONFIG_GAME_DIR}/drive_c/Program Files/Roberts Space Industries/RSI Launcher/RSI Launcher.exe"
        ],
        env=env
    )
    try:
        result = process.wait()
    except KeyboardInterrupt:
        logger.warning("Game closed by user")
        process.terminate()
        return

    sys.exit(result.returncode)