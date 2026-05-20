# 1Password Codex Plugin

This local plugin connects Codex to the 1Password desktop app's local MCP server for 1Password Developer Environments.

## MCP Server

The plugin starts the bundled macOS binary:

```json
{
  "mcpServers": {
    "1password": {
      "command": "/Applications/1Password.app/Contents/MacOS/onepassword-mcp",
      "args": []
    }
  }
}
```

The MCP server requires the 1Password desktop app with the Labs MCP server experiment enabled. Each client connection and environment access can require approval in the desktop app.

## Exposed Tools

- `authenticate`
- `list_environments`
- `create_environment`
- `rename_environment`
- `list_variables`
- `append_variables`
- `create_local_env_file`
- `list_local_env_files`

## Documentation Checked

- https://www.1password.dev/environments
- https://www.1password.dev/environments/local-env-file
- MCP resources exposed by the local server: `1password://docs/getting-started` and `1password://docs/environments-guide`
