import { describe, expect, it } from 'vitest'

import { clientConfigFor, rewriteLoopbackUrl } from './mcp-client-config'

describe('rewriteLoopbackUrl', () => {
  it('rewrites localhost to 127.0.0.1 so Node does not pick IPv6', () => {
    expect(rewriteLoopbackUrl('http://localhost:8765/mcp')).toBe('http://127.0.0.1:8765/mcp')
  })

  it('leaves a non-loopback host unchanged', () => {
    expect(rewriteLoopbackUrl('https://securo.example.com/mcp')).toBe(
      'https://securo.example.com/mcp',
    )
  })
})

describe('clientConfigFor', () => {
  it('emits a stdio mcp-remote block for Claude Desktop', () => {
    const parsed = JSON.parse(
      clientConfigFor('claude-desktop', 'http://localhost:8765/mcp', 'test-token'),
    )
    const server = parsed.mcpServers.securo
    expect(server.command).toBe('npx')
    expect(server.args).toEqual([
      '-y',
      'mcp-remote',
      'http://127.0.0.1:8765/mcp',
      '--allow-http',
      '--transport',
      'http-only',
      '--header',
      'Authorization:${SECURO_MCP_TOKEN}',
    ])
    expect(server.env.SECURO_MCP_TOKEN).toBe('Bearer test-token')
    expect(server.url).toBeUndefined()
  })

  it('uses cmd /c npx on Windows so Program Files is not split', () => {
    const parsed = JSON.parse(
      clientConfigFor('claude-desktop', 'http://localhost:8765/mcp', 'test-token', {
        windows: true,
      }),
    )
    const server = parsed.mcpServers.securo
    expect(server.command).toBe('cmd')
    expect(server.args[0]).toBe('/c')
    expect(server.args[1]).toBe('npx')
    expect(server.args).toContain('http://127.0.0.1:8765/mcp')
  })

  it('omits --allow-http for https Claude Desktop URLs', () => {
    const parsed = JSON.parse(
      clientConfigFor('claude-desktop', 'https://securo.example.com/mcp', 'tok'),
    )
    expect(parsed.mcpServers.securo.args).not.toContain('--allow-http')
  })

  it('keeps url + headers for Cursor / Claude Code', () => {
    const parsed = JSON.parse(
      clientConfigFor('cursor', 'http://localhost:8765/mcp', 'test-token'),
    )
    expect(parsed.mcpServers.securo).toEqual({
      url: 'http://localhost:8765/mcp',
      headers: { Authorization: 'Bearer test-token' },
    })
  })
})
