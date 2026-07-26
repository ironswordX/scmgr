VERSION = "1.0.0"

import argparse
import tomlkit
from pathlib import Path
from logs import logger as create_logger
from actions.install import action_install
from actions.launch import action_launch
import PySimpleGUI as sg

def merge_config(default, override):
    for key, value in override.items():
        if isinstance(value, dict) and key in default:
            merge_config(default[key], value)
        else:
            default[key] = value
    return default

def main():
    parser = argparse.ArgumentParser(
        prog="scmgr",
        description="Star Citizen Manager",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )

    # MARK: opts: global
    opts_general = parser.add_argument_group("General Options")
    opts_general.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    opts_general.add_argument("-v", "--verbose", action="store_true", default=False, help="Enable verbose output")
    opts_general.add_argument("-c", "--config", type=Path, default=Path.home() / ".config/scmgr.toml", help="Path to configuration file")

    actions = parser.add_subparsers(dest="action", title="Actions")

    # MARK: action def: install
    actions_install = actions.add_parser("install", help="Install Star Citizen")
    actions_install.set_defaults(func=action_install, action="install")
    actions_install.add_argument("game_dir", default="~/Games/star-citizen", help="Specify the game directory for installation\n(Default: ~/Games/star-citizen)")
    actions_install.add_argument("--install-dxvk-nvapi", action="store_true", default=False, help="Add support for NVIDIA-specific features (i.e. DLSS)")

    # MARK: action def: launch
    actions_launch = actions.add_parser("launch", help="Launch Star Citizen")
    actions_launch.set_defaults(func=action_launch, action="launch")

    launch_opts_game = actions_launch.add_argument_group("Game Configuration")
    launch_opts_game.add_argument("--game-dir", type=Path, help="Use an alternate Star Citizen installation location")

    launch_opts_hardware = actions_launch.add_argument_group("Hardware")
    launch_opts_hardware.add_argument("--override-gpu-vendor", choices=["intel", "amd", "nvidia"], help="Override automatic GPU vendor detection (useful in unusual configurations)")

    launch_opts_proton = actions_launch.add_argument_group("Proton Configuration")
    launch_opts_proton.add_argument("-r", "--proton-runner", help="Proton runner to use (either a directory or a runner name)")

    launch_opt_protonfixes_options = {
        "starcitizen": "Apply the `umu-starcitizen` proton fixes.",
        "default": "Apply the default proton fixes.",
        "none": "Do not apply any proton fixes.",
    }

    launch_opts_proton.add_argument(
        "--proton-fixes",
        choices=launch_opt_protonfixes_options,
        help="Specify what proton fixes to apply:\n" +
        "\n".join(f"\t{k}: {v}" for k, v in launch_opt_protonfixes_options.items())
    )

    launch_opts_proton.add_argument("--proton-renderer-opengl", action="store_true", help="Use the legacy WINED3D (OpenGL) renderer for Proton")
    launch_opts_proton.add_argument("--proton-sync", choices=["ntsync", "fsync"], help="Switch between the NTSYNC and FSYNC")

    opts = parser.parse_args()

    logger = create_logger(opts.verbose)

    # MARK: default config
    config = {
        "game": {
            "path": "~/Games/star-citizen/",
            "proton": {
                "fixes": "starcitizen",
                "sync": "ntsync",
                "renderer": {
                    "opengl": False
                }
            },
            "graphics": {
                "shaders": {
                    "cache_size": "10G"
                }
            }
        }
    }

    # MARK: load config
    if opts.config.exists():
        with opts.config.open("rb") as f:
            user_config = tomlkit.load(f)
            config = merge_config(config, user_config)
            logger.debug("Loaded config file")

    elif opts.action != "install":
        logger.warning("Configuration file does not exist! All parameters will use their default values.")
    
    return opts.func(logger, opts, config)

if __name__ == "__main__":
    main()