export type McpClientId = 'claude-desktop' | 'cursor' | 'openai'

export function rewriteLoopbackUrl(url: string): string {
  try {
    const parsed = new URL(url)
    if (parsed.hostname === 'localhost') {
      parsed.hostname = '127.0.0.1'
    }
    return parsed.toString()
  } catch {
    return url
  }
}

export function clientConfigFor(
  client: McpClientId,
  url: string,
  token: string,
  options?: { windows?: boolean },
): string {
  switch (client) {
    case 'claude-desktop': {
      // Claude Desktop's claude_desktop_config.json is stdio-only. A
      // `url`/`headers` block is skipped as invalid.
      //
      // On Windows, bare `npx` is resolved to
      // `C:\Program Files\nodejs\npx.cmd` and launched unquoted through
      // cmd.exe, which fails as `'C:\Program' is not recognized`. `cmd /c
      // npx` keeps the executable name short so PATH lookup stays quoted.
      const httpUrl = rewriteLoopbackUrl(url)
      const remoteArgs = ['-y', 'mcp-remote', httpUrl]
      if (httpUrl.startsWith('http://')) {
        remoteArgs.push('--allow-http')
      }
      remoteArgs.push(
        '--transport',
        'http-only',
        '--header',
        'Authorization:${SECURO_MCP_TOKEN}',
      )
      const windows = options?.windows === true
      return JSON.stringify(
        {
          mcpServers: {
            securo: windows
              ? {
                  command: 'cmd',
                  args: ['/c', 'npx', ...remoteArgs],
                  env: { SECURO_MCP_TOKEN: `Bearer ${token}` },
                }
              : {
                  command: 'npx',
                  args: remoteArgs,
                  env: { SECURO_MCP_TOKEN: `Bearer ${token}` },
                },
          },
        },
        null,
        2,
      )
    }
    case 'cursor':
      return JSON.stringify(
        {
          mcpServers: {
            securo: {
              url,
              headers: { Authorization: `Bearer ${token}` },
            },
          },
        },
        null,
        2,
      )
    case 'openai':
      return JSON.stringify(
        {
          type: 'mcp',
          server_label: 'securo',
          server_url: url,
          headers: { Authorization: `Bearer ${token}` },
          require_approval: 'never',
        },
        null,
        2,
      )
    default: {
      const _exhaustive: never = client
      throw new Error(`unknown MCP client: ${_exhaustive}`)
    }
  }
}
