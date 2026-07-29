import os
import sys
import yaml
import asyncio
import subprocess
import contextlib
from pathlib import Path
from urllib import request
from urllib.parse import quote as url_sanitize
from hashlib import sha512
from base64 import b64decode
from tempfile import TemporaryDirectory
#from mkwineprefix import create_wine_prefix

from invoke import run

def generate_default_config(install_dir):
    return f"""[game]
path = "{Path(install_dir).expanduser()}"

[game.proton]
# Specify a proton runner to use. If left blank, UMU-Proton will be used.
runner = ""
# Specify what proton fixes to apply
# starcitizen = Apply the Star Citizen proton fixes
# default = Apply the default proton fixes
# none = Do not apply any proton fixes (NOT RECOMMENDED!)
fixes = "starcitizen"
sync = "ntsync"

[game.proton.renderer]
# false = Use DXVK (Vulkan); true = Use WINED3D (OpenGL)
opengl = false

[game.graphics.shaders]
# Specify the cache size.
cache_size = "10G"
    """

def action_install(logger, opts, config):
    logger.debug("Creating temp directory...")
    with TemporaryDirectory(prefix="scmgr-") as _tmp_dir:
        tmp_dir = Path(_tmp_dir)
        logger.debug(f"Temporary directory created at {tmp_dir}")

        game_dir = Path(opts.game_dir).expanduser()
        if Path(game_dir).exists():
            logger.fatal(f"The game folder ({str(game_dir)}) already exists!")
            sys.exit(1)

        logger.info("Downloading installer...")
        logger.debug("Fetching latest installer from https://install.robertsspaceindustries.com/rel/2/latest.yml")
        try:
            with request.urlopen("https://install.robertsspaceindustries.com/rel/2/latest.yml") as response:
                latest_manifest = yaml.safe_load(response.read().decode("utf-8"))
        except Exception as e:
            logger.fatal(f"Failed to fetch launcher manifest: {e}")
            sys.exit(1)
        logger.debug(f"Found metadata for launcher ver {latest_manifest["version"]}")
        installer_url = (f"https://install.robertsspaceindustries.com/rel/2/{url_sanitize(latest_manifest["files"][0]["url"])}")
        installer_file = Path(tmp_dir / "installer.exe")
        logger.debug(f"Downloading installer file {installer_url} to {str(tmp_dir)}/installer.exe")
        #request.urlretrieve(installer_url, tmp_dir / "installer.exe")
        installer_sha512 = sha512()
        with request.urlopen(installer_url) as response:
            with installer_file.open("wb") as f:
                while chunk := response.read(1024 ** 2):
                    f.write(chunk)
                    installer_sha512.update(chunk)

        logger.debug("Checking installer hash...")
        if (
            installer_sha512.digest() != b64decode(latest_manifest["files"][0]["sha512"])
            or installer_file.stat().st_size != int(latest_manifest["files"][0]["size"])
        ):
            logger.fatal("Installer hash does not match the manifest's provided hash! Refusing to install.")
            sys.exit(1)
        logger.debug("Hashes match! Continuing with installation")

        logger.info("Initializing wine...")

        logger.debug("Setting environment vars...")
        env = os.environ.copy()
        env.update({ "WINEPREFIX": str(game_dir) })
        logger.debug("Creating wine prefix...")
        Path(game_dir.parent).mkdir(parents=True, exist_ok=True)
        run("wineboot --init", hide=not opts.verbose, env=env)

        logger.info("Adding required wine components...")
        tricks = ["arial", "tahoma", "powershell", "win11"]
        if opts.install_dxvk_nvapi:
            tricks.append("dxvk_nvapi")
        else:
            tricks.append("dxvk")
        run(f"winetricks -q {" ".join(tricks)}", hide=not opts.verbose, env=env)

        logger.debug("Adding installer env vars...")
        env.update({ "WINEDLLOVERRIDES": "dxwebsetup.exe,dotNetFx45_Full_setup.exe,winemenubuilder.exe=d" })
        logger.info("Running installer...")
        run(f"wine \"{str(installer_file)}\" /S", hide=not opts.verbose, env=env)

        logger.info("Setting up configuration file...")
        config_file = opts.config.expanduser()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        if config_file.exists():
            logger.warn("Configuration file already exists, skipping!")
        else:    
            config_file.write_text(generate_default_config(game_dir), encoding="utf-8")

        logger.info("All set! Run `scmgr launch` to start.")
