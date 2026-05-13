# YTray

A lightweight YouTube/YouTube Music player that lives in the Windows system tray.

## Features

- Sits in the **system tray** — no taskbar clutter
- Compact browser window pops up on tray click
- **Global shortcuts** work even when minimised:
  - `Ctrl+Alt+Space` — Play / Pause
  - `Ctrl+Alt+→` — Next track
  - `Ctrl+Alt+←` — Restart track (or previous if already at start)
- Persistent login — YouTube session is remembered between launches
- Pin mode to keep the window visible
- Works with YouTube Music and regular YouTube

## Requirements

- Windows 10/11
- Node.js v18+ and npm — https://nodejs.org

## Quick start (dev)

```bash
npm install
npm start
```

## Build portable .exe

```bash
python deploy_YTray.py
```

Output: `YTray-<version>.exe` in the same folder as the script. Build folder is automatically cleaned up.

## Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Alt+Space` | Play / Pause |
| `Ctrl+Alt+→` | Next track |
| `Ctrl+Alt+←` | Restart / Previous track |

## Version history

| Version | Changes |
|---|---|
| 1.3.0 | Global shortcuts fixed (Chromium throttle flags), next/restart shortcuts added |
| 1.2.0 | Background throttling fix attempt (bg/popup split — reverted) |
| 1.1.0 | Fixed malformed PNG icon |
| 1.0.0 | Initial release |
