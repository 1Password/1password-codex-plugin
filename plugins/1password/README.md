# 1Password Codex Plugin

This plugin connects Codex to the 1Password desktop app's local MCP server for 1Password Developer Environments.

## MCP Server

The plugin starts the 1Password MCP server via the `1password-mcp` alias, which
the 1Password desktop app installs on your `PATH` (supported on macOS, Windows,
and Linux):

```json
{
  "mcpServers": {
    "1password": {
      "command": "1password-mcp",
      "args": []
    }
  }
}
```

The MCP server requires the 1Password desktop app with **Integrate with MCP clients**
turned on under **Settings > Developer**. If the checkbox is disabled by an
administrator, ask your administrator to check **Policies > Sharing and permissions > Agentic permissions > Local MCP server**.
Each client connection and environment access can require approval in the desktop app.

On macOS 27 Golden Gate, also allow the app you run Codex in to access 1Password
app data: open **System Settings** > **Privacy & Security** > **Files & Folders**,
select the app, and turn on the setting that starts with **"Data shared by 1Password"**.
Then quit and reopen the app.

## Exposed Tools

- `authenticate`
- `list_environments`
- `create_environment`
- `rename_environment`
- `list_variables`
- `append_variables`
- `create_local_env_file`
- `list_local_env_files`

## Documentation

- https://www.1password.dev/environments
- https://www.1password.dev/environments/local-env-file
- https://www.1password.dev/environments/mcp-codex-server