#!/usr/bin/env node
/**
 * Stdio ↔ HTTP bridge for Claude Desktop.
 *
 * Claude Desktop (and the official MCP TypeScript SDK) speak
 * newline-delimited JSON on stdio — the same framing GoatFarm uses —
 * not LSP Content-Length headers. This process is launched as
 * `node <this-file>` so Windows does not trip over `npx` in
 * `C:\Program Files`.
 *
 * Env:
 *   SECURO_MCP_URL    e.g. http://127.0.0.1:8765/mcp
 *   SECURO_MCP_TOKEN  e.g. Bearer <jwt>
 */
import { writeSync } from 'node:fs'

// Localhost must not go through a user HTTP proxy — that hangs for ~60s
// and matches Claude's initialize cancel timeout.
for (const key of ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']) {
  delete process.env[key]
}

const url = process.env.SECURO_MCP_URL
const token = process.env.SECURO_MCP_TOKEN

if (!url || !token) {
  console.error('SECURO_MCP_URL and SECURO_MCP_TOKEN are required')
  process.exit(1)
}

function writeMessage(obj) {
  writeSync(1, `${JSON.stringify(obj)}\n`)
}

function writeError(id, code, message) {
  writeMessage({ jsonrpc: '2.0', id: id ?? null, error: { code, message } })
}

function handleLocal(message) {
  if (message.method === 'initialize') {
    writeMessage({
      jsonrpc: '2.0',
      id: message.id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'securo-builtin', version: '0.1.0' },
      },
    })
    return true
  }
  if (message.method === 'ping') {
    writeMessage({ jsonrpc: '2.0', id: message.id, result: {} })
    return true
  }
  if (typeof message.method === 'string' && message.method.startsWith('notifications/')) {
    return true
  }
  return false
}

async function forward(message) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: token,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(message),
  })
  if (res.status === 204 || res.status === 202) return null
  const text = await res.text()
  if (!text) return null
  return JSON.parse(text)
}

function handleMessage(message) {
  if (handleLocal(message)) return
  const isNotification = message.id === undefined
  forward(message)
    .then((reply) => {
      if (isNotification) return
      if (reply) writeMessage(reply)
      else writeError(message.id, -32603, 'empty response from Securo MCP')
    })
    .catch((err) => {
      console.error('securo mcp bridge:', err)
      if (!isNotification) {
        writeError(message.id, -32603, String(err.message || err))
      }
    })
}

let buffer = ''
process.stdin.setEncoding('utf8')
process.stdin.on('data', (chunk) => {
  buffer += chunk
  for (;;) {
    const nl = buffer.indexOf('\n')
    if (nl === -1) return
    const line = buffer.slice(0, nl).replace(/\r$/, '').trim()
    buffer = buffer.slice(nl + 1)
    if (!line) continue
    try {
      handleMessage(JSON.parse(line))
    } catch (err) {
      console.error('securo mcp bridge: bad stdio line', err)
    }
  }
})

process.stdin.on('end', () => process.exit(0))
process.stdin.resume()
