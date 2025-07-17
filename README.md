# Deadlock Ability Swapper

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A script to quickly swap hero abilities for ability draft.

![Screenshot](./Assets/Screenshot_1.png)

## Installation

### Prerequisites

- [Python](https://www.python.org/downloads) (3.12 or later)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Source 2 Viewer](https://valveresourceformat.github.io/)
- [fzf](https://junegunn.github.io/fzf/installation/) (must be installed and available in PATH)

### Steps

1. Clone this repository

```sh
git clone https://github.com/Artemon121/deadlock-ability-swapper
cd deadlock-ability-swapper
```

2. Install dependencies

```sh
poetry install
```

## Usage

1. Open `Deadlock/game/citadel/pak01_dir.vpk` in Source 2 Viewer, then decompile & export `scripts/heroes.vdata` and `scripts/abilities.vdata`
2. Copy `config.example.toml`, rename it to `config.toml` and fill out all settings in it
3. Run the script (it may take some time to load):

```sh
poetry run python app.py
```

Controls:

- Arrow Keys: Navigate
- `f`: Search heroes
- `ENTER`: Change value under cursor
- `l`: Toggle localization
- `Ctrl+S`: Save changes
- `Ctrl+Q`: Quit

4. Compile and pack the generated files like with any other Deadlock mod. I recommend using [DeadPacker](https://github.com/Artemon121/DeadPacker).

### Example DeadPacker config

```toml
# Copy "abilities.vdata" and "heroes.vdata"
[[step]]
[step.copy]
from = 'L:\project8\ability_draft\modded'
to = 'L:\rCSDK10\content\citadel_addons\ability_draft\scripts'

# Copy "resource" folder
[[step]]
[step.copy]
from = 'L:\project8\ability_draft\modded\resource'
to = 'L:\rCSDK10\game\citadel_addons\ability_draft\resource'

# Compile vdata files
[[step]]
[step.compile]
resource_compiler_path = 'L:\rCSDK10\game\bin\win64\resourcecompiler.exe'
addon_content_directory = 'L:\rCSDK10\content\citadel_addons\ability_draft'

[[step]]
[step.close_deadlock]

# Create a vpk
[[step]]
[step.pack]
input_directory = 'L:\rCSDK10\game\citadel_addons\ability_draft'
output_path = 'L:\SteamLibrary\steamapps\common\Deadlock\game\citadel\addons\pak98_dir.vpk'
exclude = ["cache_*.soc", "tools_thumbnail_cache.bin"]

# Launch Deadlock on the hero testing map
[[step]]
[step.launch_deadlock]
launch_params = "-dev -convars_visible_by_default -noassert -no_prewarm_map +exec autoexec +map new_player_basics"
```

## Limitations

- Some unreleased abilities might crash the game
- Some abilities work only on their original heroes (e.g. Bebop Uppercut, Ivy Ult)
- Setting a non-weapon ability as a weapon and vice versa does not work
- Vyper needs to have her passive because it's unlocked by default
