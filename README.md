# 1Password Codex Plugin

This repository contains a Codex plugin that connects Codex to the
1Password desktop app's local MCP server for 1Password Developer Environments.

The plugin lets Codex help with secure project environment setup, such as
listing Developer Environments, inspecting variable names, adding variables, and
creating local `.env` mounts. Secret values remain controlled by 1Password and
are never shared with Codex.

Note: This plugin supports macOS, Windows, and Linux.

#### Documentation
https://www.1password.dev/environments/mcp-codex-server

## What's Included

- `plugins/1password/.codex-plugin/plugin.json` - Codex plugin metadata and UI
  configuration.
- `plugins/1password/.mcp.json` - MCP server configuration for the 1Password
  desktop app's bundled `1password-mcp` binary.
- `plugins/1password/skills/1password-environments/SKILL.md` - Codex skill
  instructions for using 1Password Developer Environments.
- `plugins/1password/skills/1password-environments/agents/openai.yaml` - Skill
  interface settings (display name, icons, brand color). These belong here
  rather than in `SKILL.md` frontmatter, which only carries the skill's `name`,
  `description`, and other Agent Skills spec fields.
- `plugins/1password/assets/` - Plugin icon and logo assets.
- `.agents/plugins/marketplace.json` - Local marketplace entry that points Codex
  at `plugins/1password`.
- `scripts/package-skill-submission.sh` - Builds the ZIP for a "Skills Only"
  submission to the OpenAI plugin directory.
- `scripts/validate_submission_zip.py` - Checks a built ZIP against OpenAI's
  submission rules.

## Prerequisites

- macOS, Windows, or Linux with the 1Password desktop app installed.
- The MCP server enabled in the desktop app under Settings > Developer.
- Access to a 1Password account with Developer Environments enabled. On
  business accounts, an administrator must first enable the feature in the
  "Sharing & Permissions" policies section of the admin dashboard.

The MCP server runs via the `1password-mcp` alias, which the 1Password
desktop app installs on your `PATH`:

```text
1password-mcp
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

## Packaging for Submission

To build the ZIP for a **Skills Only** submission to the OpenAI plugin
directory:

```bash
./scripts/package-skill-submission.sh
```

This writes `dist/1password-skill-submission.zip` and validates it before
exiting. Upload that file in the submission portal.

A skills-only bundle may not declare `mcpServers`, `.mcp.json`, `apps`,
`.app.json`, or `interface.screenshots`, but this repo keeps `.mcp.json` so the
plugin still works as a local install. The script resolves that by staging a
copy and stripping those pieces there, so your working tree is never modified.

Two structural rules cause most rejections, and the script handles both:

- The ZIP must contain exactly one plugin root, so `.codex-plugin/plugin.json`
  sits either at the ZIP root or inside its only top-level directory. Zipping
  the repo root fails (several top-level entries), and so does zipping a bare
  skill folder (no manifest).
- Do not use Finder's "Compress" to build the archive by hand; it adds
  `__MACOSX` entries.

To check an archive that was built some other way:

```bash
python3 scripts/validate_submission_zip.py dist/1password-skill-submission.zip
```

Note that a skills-only listing installs the skill but does not configure the
MCP server, so users follow the Requirements section of
[SKILL.md](plugins/1password/skills/1password-environments/SKILL.md) to enable
it themselves. Submitting the MCP server through the directory instead would
require a production HTTPS server URL with domain verification, which does not
apply to a local stdio server.

## License

MIT. See [LICENSE](LICENSE).
