const { app, BrowserWindow, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

const PYTHON_PORT = 19876
const PROJECT_ROOT = path.join(__dirname, '..')

let mainWindow = null
let pythonProcess = null

// ── 启动 Python FastAPI ──────────────────────────
function startPythonBackend() {
  const venvPython = path.join(PROJECT_ROOT, 'backend', 'venv', 'bin', 'python3')

  pythonProcess = spawn(venvPython, ['-m', 'backend.src.app'], {
    cwd: PROJECT_ROOT,
    env: { ...process.env, DEBUG: 'false', PYTHONPATH: PROJECT_ROOT },
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  pythonProcess.stdout.on('data', (d) => { /* 忽略正常输出 */ })
  pythonProcess.stderr.on('data', (d) => { /* 忽略 */ })
  pythonProcess.on('error', (err) => console.error('Python 启动失败:', err))
}

// ── 等待后端就绪 ──────────────────────────────────
function waitForBackend(timeout = 15000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = () => {
      http.get(`http://127.0.0.1:${PYTHON_PORT}/api/v1/health`, (res) => {
        if (res.statusCode === 200) resolve()
        else if (Date.now() - start > timeout) reject(new Error('后端启动超时'))
        else setTimeout(check, 500)
      }).on('error', () => {
        if (Date.now() - start > timeout) reject(new Error('后端启动超时'))
        else setTimeout(check, 500)
      })
    }
    check()
  })
}

// ── 创建窗口 ──────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    title: 'DevAssistant',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // 加载 Vue 构建产物
  const distPath = path.join(PROJECT_ROOT, 'frontend', 'dist', 'index.html')
  mainWindow.loadFile(distPath)

  // macOS: 关闭窗口不退出
  mainWindow.on('closed', () => { mainWindow = null })
}

// ── 应用生命周期 ──────────────────────────────────
app.whenReady().then(async () => {
  startPythonBackend()

  // 显示 loading 或等待
  try {
    await waitForBackend(20000)
  } catch {
    dialog.showErrorBox('启动失败', '后端服务启动超时，请检查 Python 环境')
    app.quit()
    return
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
    pythonProcess = null
  }
})
