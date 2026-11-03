# Changelog

All notable changes to this plugin are documented here. A new entry is added when you push a release branch; see [Releasing](README.md#releasing).

## [0.3.1] - 2026-11-03

### Fixes
- Added a setup step for macOS 27: allow the app you run Codex in to access 1Password app data under **System Settings > Privacy & Security > Files & Folders**. (#13)
- Updated docs and the skill to say "secrets" instead of "variables", and to use the current tool names, `list_secrets` and `append_secrets`. (#15)

## [0.3.0] - 2026-10-23

### Features
- Renamed the plugin to "1Password Developer Tools" in the plugin directory.

### Fixes
- Updated setup steps to turn on **Integrate with MCP clients** under **Settings > Developer** in the 1Password desktop app. (#6)
- Updated where administrators turn on the local MCP server: **Policies > Sharing and permissions > Agentic permissions > Local MCP server**. (#6)
