# YTray — Agent Instructions

This file tells Claude (or any AI agent) everything needed to work on and deploy this project autonomously.

## What this project is

YTray is a lightweight Electron app that runs in the Windows system tray and plays YouTube / YouTube Music. It uses a single `BrowserWindow` containing a `<webview>` tag. Global shortcuts are registered via Electron's `globalShortcut` API and execute JavaScript directly into the webview's guest `webContents`.

## Repo structure

```
YTray/
├── main.js          # Electron main process — tray, window, shortcuts
├── index.html       # Renderer — webview + UI chrome
├── icon.png         # 256x256 RGBA PNG tray icon (generated via Pillow)
├── package.json     # npm manifest — version lives here
├── deploy_YTray.py  # Self-contained one-click builder (see below)
├── README.md        # User-facing docs
├── LICENSE          # MIT
├── .gitignore
└── AGENTS.md        # This file
```

## Key architecture decisions

- **Single window** — the webview lives inside the popup window, not a separate background window. Background throttling is prevented via three Chromium command-line flags in `main.js` (lines 4-7). Do not revert to a two-window architecture.
- **Global shortcuts → guest webContents** — `webContents.getAllWebContents()` finds the webview's guest process by type. JS is executed there directly, not via IPC to the renderer.
- **backgroundThrottling: false** on the BrowserWindow plus the app-level switches are both required. Remove either and shortcuts stop working when minimised.
- **Persistent session** — the webview uses `partition="persist:ytray"` so YouTube login survives restarts.

## Versioning rules

- Version is stored in `package.json` → `"version"`
- Increment the **minor** version (`1.x.0`) for every meaningful change
- Current version at last edit: **1.4.0**
- After editing any source file, re-embed into `deploy_YTray.py` (see below)

## How to make changes

1. Edit the relevant source file (`main.js`, `index.html`, etc.)
2. Bump the minor version in `package.json`
3. Re-run the embed step to bake updated files into `deploy_YTray.py`:

```python
# Re-embed all source files into deploy_YTray.py
import base64, json, re
from pathlib import Path

files_to_embed = ['main.js', 'index.html', 'icon.png', 'package.json',
                  'README.md', 'LICENSE', '.gitignore', 'AGENTS.md']
embedded = {}
for f in files_to_embed:
    with open(f, 'rb') as fh:
        embedded[f] = base64.b64encode(fh.read()).decode()

deploy = Path('deploy_YTray.py').read_text()
new_block = 'FILES = ' + json.dumps(embedded, indent=4)
deploy = re.sub(r'FILES = \{.*?\}', new_block, deploy, flags=re.DOTALL)

# Also update default version
version = json.loads(Path('package.json').read_text())['version']
deploy = re.sub(r'--version", default="[\d.]+"', f'--version", default="{version}"', deploy)

Path('deploy_YTray.py').write_text(deploy)
```

4. Validate: `python3 -c "import ast; ast.parse(open('deploy_YTray.py').read()); print('OK')"`
5. Commit and push (deploy script handles this — see below)

## deploy_YTray.py — what it does

Single Python file, no dependencies beyond Node.js on the machine.

1. Extracts all source files from embedded base64 into `_ytray_build/`
2. Injects `electron-builder` config into `package.json`
3. Runs `npm install` if `node_modules` not present
4. Builds portable `.exe` via `npx electron-builder --win --x64`
5. Moves `YTray-<version>.exe` to the script's directory
6. Deletes `_ytray_build/` entirely
7. Optionally pushes all repo files to GitHub via the API

## GitHub push

The deploy script prompts to push to GitHub after building. It uses the GitHub API directly (no git binary needed). It will:
- Create the repo at `github.com/granterogers/YTray` if it doesn't exist
- Push/update all repo files in one commit
- Token is read from `GITHUB_TOKEN` env var, or prompted interactively

To push without building:
```bash
python deploy_YTray.py --skip-build
```

## Shortcut reference

| Shortcut | Function | JS target |
|---|---|---|
| `Ctrl+Alt+Space` | Play / Pause | `video.play()` / `video.pause()` |
| `Ctrl+Alt+→` | Next track | `[data-testid="next-button"]` click, fallback Shift+N |
| `Ctrl+Alt+←` | Restart / Prev | `video.currentTime = 0`, or prev button if < 3s |

## Known issues / gotchas

- YouTube Music periodically updates its DOM — if next/prev button selectors break, update the `data-testid` values in `main.js`
- The `useragent` override in `index.html` is required — without it YouTube may serve a degraded experience
- On first build, Electron (~100 MB) downloads automatically via electron-builder
- `shell: true` is required for `npm`/`npx` on Windows (they are `.cmd` files)
