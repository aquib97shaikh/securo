import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const bridge = fileURLToPath(new URL('./mcp-stdio-bridge.mjs', import.meta.url))

function ndjson(obj) {
  return `${JSON.stringify(obj)}\n`
}

function parseNdjson(text) {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line))
}

function spawnBridge(env) {
  return spawn(process.execPath, [bridge], {
    env: { ...process.env, ...env },
    stdio: ['pipe', 'pipe', 'pipe'],
  })
}

async function readReply(child, timeoutMs = 800) {
  const stdout = []
  child.stdout.on('data', (c) => stdout.push(c))
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    const replies = parseNdjson(Buffer.concat(stdout).toString('utf8'))
    if (replies.length > 0) return replies
    await new Promise((resolve) => setTimeout(resolve, 25))
  }
  return parseNdjson(Buffer.concat(stdout).toString('utf8'))
}

test('answers initialize locally over newline-delimited JSON', async () => {
  const child = spawnBridge({
    SECURO_MCP_URL: 'http://127.0.0.1:9/mcp',
    SECURO_MCP_TOKEN: 'Bearer test-token',
  })
  child.stdin.write(
    ndjson({
      jsonrpc: '2.0',
      id: 0,
      method: 'initialize',
      params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'test' } },
    }),
  )
  const replies = await readReply(child)
  child.stdin.end()
  await once(child, 'exit')
  assert.equal(replies.length, 1)
  assert.equal(replies[0].id, 0)
  assert.equal(replies[0].result.serverInfo.name, 'securo-builtin')
  assert.equal(replies[0].result.protocolVersion, '2024-11-05')
})

test('forwards tools/list over HTTP and replies as NDJSON', async () => {
  const seen = []
  const server = createServer((req, res) => {
    let raw = ''
    req.on('data', (c) => {
      raw += c
    })
    req.on('end', () => {
      seen.push({
        auth: req.headers.authorization,
        body: JSON.parse(raw),
      })
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(
        JSON.stringify({
          jsonrpc: '2.0',
          id: 2,
          result: { tools: [{ name: 'list_accounts' }] },
        }),
      )
    })
  })
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  const { port } = server.address()

  const child = spawnBridge({
    SECURO_MCP_URL: `http://127.0.0.1:${port}/mcp`,
    SECURO_MCP_TOKEN: 'Bearer test-token',
  })
  child.stdin.write(ndjson({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }))
  const replies = await readReply(child)
  child.stdin.end()
  await once(child, 'exit')
  server.close()

  assert.equal(replies.length, 1)
  assert.deepEqual(replies[0].result.tools, [{ name: 'list_accounts' }])
  assert.equal(seen[0].auth, 'Bearer test-token')
  assert.equal(seen[0].body.method, 'tools/list')
})
