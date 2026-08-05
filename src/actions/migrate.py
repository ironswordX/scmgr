import os
import tomlkit
from pathlib import Path
from tomlkit import dump as toml_dump

from .install import generate_default_config # avoid redefining what we already have

def get_latest_runner(runners_dir):
    prefix = "lug-wine-tkg-git-"
    runners = []
    for runner in runners_dir.iterdir():
        if not runner.is_dir():
            continue
        if runner.name.startswith(prefix):
            version = runner.name.removeprefix(prefix)
            try:
                version_tuple = tuple(map(int, version.replace("-", ".").split(".")))
            except ValueError:
                continue
            runners.append((version_tuple, version, runner))
    if not runners:
        return None
    return max(runners, key=lambda x: x[0])

def action_migrate(logger, opts, config):
    logger.info(f"Migrating the Star Citizen installation in {opts.game_dir}")

    game_dir = Path(opts.game_dir)

    logger.info("Migrating runners...")
    logger.debug("Renaming directory...")
    os.rename(game_dir / "runners", game_dir / "wine_runners")
    logger.debug("Generating runners.toml ...")
    latest_runner = get_latest_runner(game_dir / "wine_runners")
    if latest_runner is None:
        logger.error("No lug-wine runner found")
        return
    _, latest_runner_ver, latest_runner_path = latest_runner
    runner_data = {
        "lug-wine": {
            "version": latest_runner_ver,
            "folder": f"lug-wine-tkg-git-{latest_runner_ver}"
        }
    }
    logger.debug("Writing runners.toml ...")
    with open(game_dir / "wine_runners/runners.toml", "w") as f:
        toml_dump(runner_data, f)
    
    logger.info("Setting up config file...")
    config_file = opts.config.expanduser()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    if config_file.exists():
        logger.warn("Configuration file already exists, skipping!")
    else:    
        config_file.write_text(generate_default_config(game_dir), encoding="utf-8")

    logger.info("All set!  Run `scmgr launch` to start.")