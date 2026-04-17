# Snake Game

[![Validate](https://github.com/heshamrabea445-lab/Snake_Game/actions/workflows/validate.yml/badge.svg)](https://github.com/heshamrabea445-lab/Snake_Game/actions/workflows/validate.yml)

A polished desktop take on Snake built with Python and Pygame, with animated UI, expressive sprite work, audio feedback, and a release-ready Windows build pipeline.

![Snake demo](media/snake-demo.gif)

[Instant Preview](#instant-preview) | [Play in Browser](https://heshamrabea445-lab.github.io/Snake_Game/) | [Download Windows Build](https://github.com/heshamrabea445-lab/Snake_Game/releases/latest) | [Run From Source](#run-from-source)

## Instant Preview

The GIF above shows the current launch flow and movement directly from the repository page.

If you just want to play, use the Windows release ZIP. Running from source is mainly for developers who want the Python version.

The live browser version runs on GitHub Pages. GitHub can link to that page from the README, but it cannot embed the live game inline inside the README itself.

## Highlights

- Smooth continuous movement with buffered turns instead of tile-by-tile snapping
- Smooth starter card and waiting cue flow instead of a bare launch screen
- Expressive snake presentation with mouth, tongue, eye, death, and collision effects
- Turn, eat, and collision audio feedback
- Fast two-step boot path that gets the first frame on screen quickly
- Asset loading that works both from source and from packaged Windows builds
- GitHub Actions validation and Windows release packaging

## Screenshots

![Starter card](media/snake-launch.png)

![Waiting screen](media/snake-waiting.png)

## Controls

| Action | Keys |
| --- | --- |
| Move | Arrow keys or `WASD` |
| Start from waiting screen | Any direction key |
| Start from launch card | `R` or click Play |
| Restart after death | `R` or click Play |
| Toggle fullscreen | `F` |
| Toggle mute | Click volume icon |
| Quit | `Esc` or click `X` |

## Download the Windows Build

The Windows ZIP is the easiest way to play.

### `snake-game-windows.zip`

1. Open the [latest release](https://github.com/heshamrabea445-lab/Snake_Game/releases/latest)
2. Download `snake-game-windows.zip`
3. Extract the ZIP
4. Open the extracted `Snake_Game` folder
5. Launch `Snake Game.exe`, or run `Install Shortcuts.ps1` to create Start Menu and Desktop shortcuts

Important:
- Keep `Snake Game.exe` inside the extracted `Snake_Game` folder with its `_internal` directory
- Use this build for normal Windows play, Start Menu shortcuts, and taskbar pinning
- Do not run the intermediate executable from `build/`; that folder is only a temporary packaging artifact

## Run From Source

This path assumes you already have Python installed.

- Python 3.13+
- A desktop environment that can open a Pygame window
- If you do not already have Python and only want to play, use the Windows ZIP above instead
- If you need Python for development, use the official installer from [python.org](https://www.python.org/downloads/) instead of linking directly to a raw `python.exe`

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Optional virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Start the game

```bash
python main.py
```

## Technical Highlights

- Single-file game architecture with structured helper sections for startup, assets, input, animation, and rendering
- Packaged asset loading that supports both source execution and frozen builds
- Headless smoke test coverage for boot, starter card flow, and core runtime assets
- GitHub Actions workflows for validation and Windows release packaging
- One-folder PyInstaller build for a more reliable Windows distribution

## Repository Layout

```text
Snake_Game/
|-- audio/                  # Sound effects and music assets
|-- docs/                   # GitHub Pages browser version
|-- images/                 # UI and board image assets
|-- media/                  # README GIF and screenshots
|-- scripts/                # Validation and Windows packaging utilities
|-- sprites/                # Character and effect sprite sheets
|-- .github/workflows/      # CI and release automation
|-- main.py                 # Game entry point
|-- requirements.txt        # Runtime dependency
`-- snake_game.spec         # Windows packaging definition
```

## Validation

To run the lightweight local validation pass:

```bash
python -m py_compile main.py
python scripts/smoke_test.py
```

To rebuild the Windows release artifact locally:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package_windows.ps1
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
