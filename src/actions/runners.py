import sys
import json
import tarfile
from pathlib import Path
from urllib import request
from tomlkit import dump as toml_dump
from tempfile import TemporaryDirectory

def runner_update(logger, opts, config):
    # im highkey too lazy to rewrite this so this is just straight outta src/actions/install.py
    with TemporaryDirectory(prefix="scmgr-") as _tmp_dir:
        logger.info("Downloading latest lug-wine runner...")
        tmp_dir = Path(_tmp_dir)
        logger.debug(f"Temporary directory created at {tmp_dir}")
        game_dir = Path(opts.game_dir or config.get("game").get("path")).expanduser()
        runner_data = {}
        logger.debug("Fetching latest runner data...")
        latest_runner_manifest_raw = request.urlopen("https://api.github.com/repos/starcitizen-lug/lug-wine/releases/latest")
        latest_runner_manifest = json.load(latest_runner_manifest_raw)
        runner_data["lug-wine"] = {
            "version": latest_runner_manifest["name"]
        }
        logger.debug("Downloading runner tarball...")
        # just in case github messes with the ordering in the json data
        latest_runner = next(
            asset for asset in latest_runner_manifest["assets"]
            if asset["name"].startswith("lug-wine-tkg-git-")
        )
        runner_data["lug-wine"]["folder"] = latest_runner["name"].removesuffix(".tar.gz")
        latest_runner_tarball_file = tmp_dir / latest_runner["name"]
        request.urlretrieve(latest_runner["browser_download_url"], latest_runner_tarball_file)
        logger.debug("Extracting runner...")
        with tarfile.open(latest_runner_tarball_file, "r:gz") as tar:
            tar.extractall(game_dir / "wine_runners")
        logger.debug("Writing to runners.toml ...")
        with open(game_dir / "wine_runners/runners.toml", "w") as f:
            toml_dump(runner_data, f)
        
        logger.info("Done!")

def action_runners(logger, opts, config):
    match opts.runner_action:
        # MARK: action: update
        case "update":
            runner_update(logger, opts, config)
        case _:
            logger.fatal("Unknown runner action")
            sys.exit(1)