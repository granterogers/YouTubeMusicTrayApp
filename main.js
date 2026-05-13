const { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, webContents } = require('electron');
const path = require('path');

// Prevent background throttling globally — this is the key fix
app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');
app.commandLine.appendSwitch('disable-backgrounding-occluded-windows');

let tray = null;
let win = null;

const SHORTCUT = 'CommandOrControl+Alt+Space';
const WIDTH = 460;
const HEIGHT = 600;

function createWindow() {
  win = new BrowserWindow({
    width: WIDTH,
    height: HEIGHT,
    show: false,
    frame: false,
    resizable: true,
    skipTaskbar: true,
    alwaysOnTop: false,
    backgroundColor: '#0f0f0f',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webviewTag: true,
      backgroundThrottling: false,
    }
  });

  win.loadFile('index.html');
  win.isPinned = false;

  win.on('blur', () => {
    if (!win.isPinned) win.hide();
  });

  // Never actually close — just hide
  win.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      win.hide();
    }
  });
}

function showWindow() {
  const { screen } = require('electron');
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const tb = tray.getBounds();

  let x = Math.round(tb.x + tb.width / 2 - WIDTH / 2);
  let y = tb.y > height / 2 ? tb.y - HEIGHT - 4 : tb.y + tb.height + 4;
  x = Math.max(0, Math.min(x, width - WIDTH));
  y = Math.max(0, Math.min(y, height - HEIGHT));

  win.setBounds({ x, y, width: WIDTH, height: HEIGHT });
  win.show();
  win.focus();
}

function toggleWindow() {
  win.isVisible() ? win.hide() : showWindow();
}

const PLAY_JS = `(function(){
  const v = document.querySelector('video');
  if (v) { v.paused ? v.play() : v.pause(); return !v.paused; }
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', keyCode: 75, bubbles: true }));
  return null;
})()`;

// Next track: click YT Music next button, fallback Shift+N
const NEXT_JS = `(function(){
  const btn = document.querySelector('[data-testid="next-button"], ytmusic-player-bar #next-button');
  if (btn) { btn.click(); return true; }
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'N', shiftKey: true, keyCode: 78, bubbles: true }));
  return false;
})()`;

// Restart track (or prev if already at start)
const RESTART_JS = `(function(){
  const v = document.querySelector('video');
  if (v) {
    if (v.currentTime > 3) { v.currentTime = 0; return 'restarted'; }
    const btn = document.querySelector('[data-testid="prev-button"], ytmusic-player-bar #prev-button');
    if (btn) { btn.click(); return 'prev'; }
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'P', shiftKey: true, keyCode: 80, bubbles: true }));
    return 'prev-shortcut';
  }
  return null;
})()`;

function getGuest() {
  if (!win) return null;
  const winId = win.webContents.id;
  return webContents.getAllWebContents()
    .find(wc => wc.id !== winId && wc.getType() === 'webview') || null;
}

function togglePlayPause() { const g = getGuest(); if (g) g.executeJavaScript(PLAY_JS).catch(() => {}); }
function nextTrack()        { const g = getGuest(); if (g) g.executeJavaScript(NEXT_JS).catch(() => {}); }
function restartOrPrev()    { const g = getGuest(); if (g) g.executeJavaScript(RESTART_JS).catch(() => {}); }

function createTray() {
  try {
    tray = new Tray(path.join(__dirname, 'icon.png'));
  } catch (e) {
    tray = new Tray(nativeImage.createEmpty());
  }
  tray.setToolTip('YTray');

  const menu = Menu.buildFromTemplate([
    { label: '▶/⏸  Play / Pause',  accelerator: 'Ctrl+Alt+Space', click: togglePlayPause },
    { label: '⏭   Next Track',       accelerator: 'Ctrl+Alt+Right', click: nextTrack },
    { label: '⏮   Restart / Prev',   accelerator: 'Ctrl+Alt+Left',  click: restartOrPrev },
    { type: 'separator' },
    { label: '📌 Pin Window', type: 'checkbox', checked: false,
      click: (item) => { win.isPinned = item.checked; if (item.checked) showWindow(); }
    },
    { type: 'separator' },
    { label: '🎵 YouTube Music', click: () => { win.webContents.send('navigate', 'https://music.youtube.com'); showWindow(); } },
    { label: '📺 YouTube',       click: () => { win.webContents.send('navigate', 'https://www.youtube.com');   showWindow(); } },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); } }
  ]);

  tray.setContextMenu(menu);
  tray.on('click', toggleWindow);
  tray.on('double-click', toggleWindow);
}

const { ipcMain } = require('electron');
ipcMain.on('pin-changed', (e, pinned) => { if (win) win.isPinned = pinned; });

app.whenReady().then(() => {
  app.setAppUserModelId('com.ytray.app');
  if (process.platform === 'darwin') app.dock.hide();

  createWindow();
  createTray();

  const shortcuts = [
    [SHORTCUT,                       togglePlayPause, 'Play/Pause'],
    ['CommandOrControl+Alt+Right',   nextTrack,       'Next track'],
    ['CommandOrControl+Alt+Left',    restartOrPrev,   'Restart/Prev'],
  ];
  for (const [combo, fn, label] of shortcuts) {
    const ok = globalShortcut.register(combo, fn);
    if (!ok) console.warn(`Shortcut failed to register: ${label} (${combo})`);
  }
});

app.on('before-quit', () => { app.isQuitting = true; });
app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('window-all-closed', (e) => { if (!app.isQuitting) e.preventDefault(); });
