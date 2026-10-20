<h1 align="center">scmgr</h1>

`scmgr` is a command-line tool for managing and launching Star Citizen installations on Linux. Notably, you can configure launch arguments [without having to tinker with bash](https://wiki.starcitizen-lug.org/Tips-and-Tricks#how-to-edit-the-launch-script).

<h2 align="center">Features</h2>

scmgr has a handful of user-friendly features, as well as behind-the-scenes improvements.

✅ = Fully implemented

🟠 = Partially implemented

❌ = Not implemented

|| scmgr | lug-helper | DIY launcher 
|-|-|-|-|
| CLI tool | ✅ | ❌ | 🟠 |
| Config file(s) | ✅ | ❌ | ❌ |
| Proton OOTB support | ✅ | ❌ | ❌ |
| Built-in diagnostics<sup>1</sup> | ❌ | ✅ | ❌ |
| GPU-specific configuration | ✅ | ❌ | ❌ |
| Ease of use | ✅ | 🟠 | ❌ |
| Maturity | 🟠 | ✅ | ❌ |
| User customizeability | 🟠 | ✅ | ❌ |

<small><sup>1</sup>Diagnostics is a planned feature for scmgr 1.3.0</small>

<h2 align="center">Installation</h2>
Installing scmgr is relatively straightforward, as it's just a Python project at it's core.

<h3>Clone the repo</h3>

```
git clone https://github.com/ironswordX/scmgr.git && cd scmgr
```

(Optional) Setup a venv as well (and source it in your shell):
```sh
python3 -m venv .venv
```

<h3>Build as a binary (RECOMMENDED)</h3>

```sh
pip install -r standalone-reqs.txt
pyinstaller scmgr.spec
```
This will create a standalone `scmgr` binary located at `dist/scmgr`, which you can put into a folder of your choosing, as long as it's in your PATH. For user installations, you can put it in `~/.local/bin/`

<h3>Install as a Python package</h3>

```sh
pip install .
```
You can now use the `scmgr` command. Installing scmgr this way is not recommended, as it can lead to dependency breakage when updating.

<small>(Note: if you installed this in a venv, the command will NOT be available outside the venv.)</small>

<h2 align="center">Set-up</h2>
Setting up a new instance can either be done completely by scmgr, or scmgr can migrate an existing lug-helper installation.

<h3>New Installation</h3>
Creating a new installation is extremely simple, as it's just one command. scmgr takes care of the rest for you!

```sh
scmgr install game_dir
```

You can set `game_dir` to whatever path you want, assuming your user has read and write permissions to the parent directory.

<h3>Migrating an existing installation (from lug-helper)</h3>

As of `1.2.0-alpha.1`, scmgr has natively supported migrating existing installations of Star Citizen from lug-helper into the format that it expects. Migration is also relatively straightforward, as it's one command, and the launcher takes care of the rest for you!

```sh
scmgr migrate path/to/existing/install
```

<h2 align="center">Launching</h2>
Launching Star Citizen with scmgr is easy as cake! Just one convenient command, like installation:

```sh
scmgr launch
```

If you decide to tinker around with temporary launch arguments, you can run `scmgr launch --help` for a full list of them.

<h2 align="center">Configuration</h2>

Modifying your configuration for scmgr/Star Citizen is relatively simple. All of your game launch options are stored in `~/.config/scmgr.toml`. An example configuration with explanations for what each option does can be found in [config.example.toml](config.example.toml).

<h2 align="center">FAQ</h2>

What does scmgr stand for?
> scmgr stands for **s**tar **c**itizen **m**ana**g**e**r**, I chose that name since I believe it accurately reflects the project both in its current state and its future goals.

Why python?
> Python is available on most, if not all, Linux distros. This makes it compatible with the majority of Linux systems, and allows the project to be easily developed.

Is scmgr stable to use? Will it break?
> For the most part, it is stable. So far, I haven't encountered any major issues asside from those I've already disclosed (i.e. the `--game-dir` issue in 1.2.0-alpha.2). 
>
> Of course, different setups may behave differently and/or cause issues, especially when using versions marked as alpha. If it does, feel free to open a GitHub issue on it.

Why did you make scmgr?
> Well, there are a handful of different reasons why. Most obviously, given that this is a configuration-driven launcher, I felt the need to create an alternative Star Citizen launcher that was easier for the players than the developers to use. lug-helper's launcher is, notoriously, [literally just a bash script](https://github.com/starcitizen-lug/lug-helper/blob/main/lib/sc-launch.sh). This brings its own pros and cons, and I believe the cons outweigh the pros for the average Joe that just wants to play his game.
>
> On a side note, my interest in developing this project spiked particularly when I was banned from the LUG discord for seemingly no reason. The only explanation that I was given was that I "continued an argument," which more or less just sounded like an egotistical power trip. But that's just my two cents, more of how the project started rather than an "x was made because y community bad" argument.