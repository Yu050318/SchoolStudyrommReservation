const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

const cwd = __dirname
const node = 'D:\\NodeJs\\node.exe'
const vite = path.join(cwd, 'node_modules', 'vite', 'bin', 'vite.js')
const out = fs.openSync(path.join(cwd, 'vite-dev.log'), 'w')
const err = fs.openSync(path.join(cwd, 'vite-dev.err.log'), 'w')

const child = spawn(node, [vite, '--host', '127.0.0.1'], {
  cwd,
  detached: true,
  stdio: ['ignore', out, err],
  windowsHide: true,
})

child.unref()
console.log(child.pid)
