# scmgr
`scmgr` is a command-line tool for managing and launching Star Citizen installations.

## Migrating from lug-helper
Migrating from `lug-helper` is relatively simple, as all you have to do is tell the launcher to use the already existing wine prefix. For a single launch, you can specify the location of the prefix:
```
scmgr launch --game-dir <your-wine-prefix>
```

Additionally, instead of specifying `--game-dir` every launch, you can also create a configuration file for `scmgr` to use. Create a config file at `~/.config/scmgr.toml` with the [default configuration](config.example.toml), and change `path` under `[game]` to the path of your wine prefix. After which, you can simply run `scmgr launch`, and it'll automatically grab the prefix path.

## Installing
`scmgr` can be installed using one of two ways.
- **Python package**
    - ✅ Easy to manage/update
    - ⚠️ May not work on some systems with externally managed Python packages
- **Standalone binary**
    - ✅ Works on systems with externally managed Python packages
    - ❌ Requires manual updates

### Python package
```bash
git clone https://github.com/ironswordX/scmgr.git
cd scmgr
pip install .
```
`scmgr` can now be used from the command line.
> NOTE: When building as a Python package in a venv, `scmgr` will NOT be available outside of the venv unless you move it.

### Standalone binary
```bash
git clone https://github.com/ironswordX/scmgr.git
cd scmgr
pip install -r standalone-reqs.txt
pyinstaller scmgr.spec
```
This will build a standalone executable at `dist/scmgr`, which you can move to a directory in your PATH for convenience (i.e. `/usr/bin`, `/usr/local/bin`, `~/.local/bin`, etc etc.)