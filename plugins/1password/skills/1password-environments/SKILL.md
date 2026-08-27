---
name: 1password-environments
description: Manage 1Password Developer Environments and local .env mounts through the local 1Password MCP server, without exposing secret values. Use when the user asks to set up environment variables for a repo, store or configure API keys and secrets in 1Password, mount or create a local .env file from 1Password, inspect 1Password Environment variable names, or work with the 1Password MCP server.
license: MIT
compatibility: Requires the 1Password desktop app (macOS, Windows, or Linux) with the MCP server enabled in Developer settings, and a client configured to run the local 1password-mcp MCP server. Local .env mounts are supported on macOS and Linux only.
---

# 1Password Environments

Use the local 1Password MCP server for all environment variable configuration. Its tools return variable names, never secret values, so secrets stay in 1Password.

## Use When

- The user mentions 1Password Environments, 1Password Developer Environments, the 1Password MCP server, or local `.env` files from 1Password.
- The user asks to set up, mount, create, or sync a project `.env` file from a secret manager and 1Password is available.
- The user asks to configure repo environment variables, API keys, tokens, credentials, or secrets securely with 1Password.
- The user wants to list or compare Environment variable names without exposing secret values.

Do not use this skill for unrelated password-manager tasks, arbitrary local `.env` file parsing, or non-1Password secret stores unless the user asks to migrate that configuration into 1Password.

## Requirements

This skill depends on the local 1Password MCP server. If its tools are not available in the current session, help the user finish setup instead of improvising:

1. Install the 1Password desktop app and enable the MCP server in Settings > Developer. On business accounts, the setting is unavailable until an administrator enables the feature in the "Sharing & Permissions" policies section of the admin dashboard.
2. The desktop app installs the `1password-mcp` alias on the `PATH` (supported on macOS, Windows, and Linux).
3. Configure the client to launch `1password-mcp` as a local MCP server. For Codex, add this to `~/.codex/config.toml`:

   ```toml
   [mcp_servers.1password]
   command = "1password-mcp"
   ```

The 1Password desktop app asks the user to approve each client connection, and environment access can require additional approval.

## Tools

The local server exposes these tools:

- `authenticate`: authenticate with the 1Password desktop app and return the account ID.
- `list_environments`: list Developer Environments for an account.
- `create_environment`: create a new Developer Environment.
- `rename_environment`: rename an existing Developer Environment.
- `list_variables`: list variable names in an Environment without returning values.
- `append_variables`: add or update Environment variables.
- `create_local_env_file`: mount an Environment as a local `.env` file on macOS or Linux.
- `list_local_env_files`: list local `.env` mounts for an Environment.

It also exposes these documentation resources:

- `1password://docs/getting-started`
- `1password://docs/environments-guide`

## Workflow

1. Call `authenticate` first when you do not already have an account ID for this turn. The 1Password desktop app will ask the user to approve the connection.
2. Use `accountId` for subsequent calls. Server docs may spell the returned value as `account_id`; MCP tool calls use camelCase parameters such as `accountId` and `environmentId`.
3. Call `list_environments` with the returned `accountId` before operating on an Environment, unless the user already provided a current `environmentId`.
4. If the target Environment is ambiguous, ask the user which Environment to use instead of guessing.
5. Use the `environmentId` returned by the server for environment-level calls.
6. Prefer `list_variables` when the user wants to inspect an Environment. It returns names only, not secret values.
7. Use `append_variables` only when the user explicitly asks to add or update variables.
8. Use `create_local_env_file` for local `.env` mounts on macOS or Linux, and pass the absolute `mountPath` the user wants.
9. Use `list_local_env_files` to check existing local mounts before creating a duplicate.

## Common Flows

### Mount 1Password as this repo's `.env`

1. Call `authenticate`.
2. Call `list_environments`.
3. Ask the user to choose an Environment if the request does not identify one clearly.
4. Call `list_local_env_files` for the selected Environment to avoid duplicate mounts.
5. If the user says "here", "this repo", or "this project", use the current workspace's absolute `.env` path as `mountPath`.
6. Call `create_local_env_file` with `accountId`, `environmentId`, `environmentName`, and the absolute `mountPath`.
7. Report the mount path and Environment name, but do not read the mounted `.env` file to verify it.

### Inspect variables

1. Call `authenticate`.
2. Call `list_environments` unless the user already gave an `environmentId`.
3. Use the `environmentId` returned by the server for environment-level calls.
4. Call `list_variables` and summarize variable names only.

### Add or update variables

1. Confirm the user explicitly wants to create or update variables, and collect any missing names or values.
2. Call `authenticate` and resolve the target Environment.
3. Prefer calling `list_variables` first so you can tell whether the requested variable names already exist.
4. Call `append_variables` using the active MCP tool schema exactly as exposed in the current session.
5. When the active schema accepts structured variable objects, use `{ "name": "API_KEY", "value": "...", "concealed": true }` for secrets and `concealed: false` only for non-sensitive values such as URLs or feature flags.
6. When the active schema exposes `variables` as `string[]`, do not send unsupported object fields. Use the string format required by that schema, and ask for clarification if the user's requested variable format is ambiguous.

## Error Handling

- If authentication or environment access fails, tell the user the 1Password desktop app may need approval, unlocking, or account access.
- If the MCP tools are unavailable, follow the Requirements section above to help the user enable and configure the local MCP server.
- Local `.env` mounts are documented for macOS and Linux only.

## Safety

- Do not reveal, log, or echo secret values.
- Do not read a mounted `.env` file just to verify it exists; use the MCP tools instead.
- Ask before creating or modifying Environment variables unless the user's request is already explicit.
- Treat local `.env` mounts as sensitive even though 1Password does not persist plaintext secret contents to disk.
- If a user pasted a secret into the chat, avoid repeating it back; refer to it by variable name.

## Notes

- Official docs: https://www.1password.dev/environments and https://www.1password.dev/environments/mcp-codex-server
- This skill is also distributed as part of the 1Password Codex plugin (https://github.com/1Password/1password-codex-plugin), which configures the MCP server automatically.
