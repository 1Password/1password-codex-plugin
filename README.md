# 1Password Codex Plugin

This repository contains a Codex plugin that connects Codex to the
1Password desktop app's local MCP server for 1Password Developer Environments.

The plugin lets Codex help with secure project environment setup, such as
listing Developer Environments, inspecting variable names, adding variables, and
creating local `.env` mounts. Secret values remain controlled by 1Password and
are never shared with Codex.

Note: This plugin currently only supports MacOS

#### Documentation
https://www.1password.dev/environments/mcp-codex-server

## What's Included

- `plugins/1password/.codex-plugin/plugin.json` - Codex plugin metadata and UI
  configuration.
- `plugins/1password/.mcp.json` - MCP server configuration for the 1Password
  desktop app's bundled `onepassword-mcp` binary.
- `plugins/1password/skills/1password-environments/SKILL.md` - Codex skill
  instructions for using 1Password Developer Environments.
- `plugins/1password/assets/` - Plugin icon and logo assets.
- `.agents/plugins/marketplace.json` - Local marketplace entry that points Codex
  at `plugins/1password`.

## Prerequisites

- macOS with the 1Password desktop app installed.
- 1Password Labs MCP server experiment enabled in the desktop app.
- Access to a 1Password account with Developer Environments enabled.

The MCP server is expected at:

```text
/Applications/1Password.app/Contents/MacOS/onepassword-mcp
```

## Using the Plugin

Once installed or enabled in Codex, you can ask for tasks like:

- "List my 1Password Environments"
- "Create a local .env mount here"
- "Show me the variable names in my project environment"
- "Add a placeholder variable for my OpenAI API key"

The 1Password desktop app may prompt for approval when Codex connects to the MCP
server or accesses an Environment.

## Exposed MCP Tools

The plugin exposes these 1Password MCP tools to Codex:

- `authenticate`
- `list_environments`
- `create_environment`
- `rename_environment`
- `list_variables`
- `append_variables`
- `create_local_env_file`
- `list_local_env_files`

## License

MIT. See [LICENSE](LICENSE).
