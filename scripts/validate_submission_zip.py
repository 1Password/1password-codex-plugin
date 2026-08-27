#!/usr/bin/env python3
"""Check a skills-only submission ZIP against OpenAI's plugin validation rules.

Mirrors https://developers.openai.com/codex/plugin-submission-errors so a bad
bundle fails here instead of in the submission portal. Stdlib only.

Usage: scripts/validate_submission_zip.py dist/1password-skill-submission.zip
"""

import json
import re
import struct
import sys
import zipfile

CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Other",
}
MANIFEST_DIRS = (".codex-plugin", ".agent-plugin", ".claude-plugin")
# field -> max length at final submission (stricter than the draft-validation cap)
INTERFACE_LIMITS = {
    "displayName": 30,
    "shortDescription": 30,
    "longDescription": 4000,
    "developerName": 80,
}
# Per the Agent Skills spec, minus `metadata`: OpenAI rejects it because it does
# not configure the skill interface -- that belongs in agents/openai.yaml.
SKILL_FRONTMATTER = {"name", "description", "license", "compatibility", "allowed-tools"}
OPENAI_YAML_SECTIONS = {"interface", "policy", "dependencies"}
OPENAI_YAML_INTERFACE = {
    "display_name", "short_description", "icon_small", "icon_large",
    "brand_color", "default_prompt",
}

errors: list[str] = []
warnings: list[str] = []


def png_size(blob):
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", blob[16:24])


def svg_size(blob):
    head = blob[:2000].decode("utf-8", "replace")
    tag = re.search(r"<svg\b[^>]*>", head, re.S)
    if not tag:
        return None
    dims = []
    for attr in ("width", "height"):
        m = re.search(rf'{attr}\s*=\s*["\']([^"\']+)["\']', tag.group(0))
        if not m:
            return None
        val = m.group(1).strip().removesuffix("px").strip()
        try:
            dims.append(float(val))
        except ValueError:
            return None  # "100%", "auto", em units...
    return tuple(dims)


def parse_yaml_section(text, section):
    """Read one flat `section:` block of key/value pairs. Enough for openai.yaml."""
    out, inside = {}, False
    for line in text.splitlines():
        if re.match(rf"^{section}:\s*$", line):
            inside = True
            continue
        if not inside:
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            break  # next top-level key
        m = re.match(r"^\s+([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def check_image(zf, base, label, rel):
    """base is the directory the path is relative to, with a trailing slash."""
    if not rel.startswith("./"):
        errors.append(f"{label} must start with './' (got {rel!r})")
        return
    if ".." in rel.split("/") or rel.startswith("/"):
        errors.append(f"{label} must not contain a '..' traversal segment ({rel!r})")
        return
    path = f"{base}{rel[2:]}"
    try:
        blob = zf.read(path)
    except KeyError:
        errors.append(f"{label} points at a missing file: {rel} (expected {path})")
        return

    if len(blob) > 5 * 1024 * 1024:
        errors.append(f"{label} exceeds the 5 MiB image limit")

    lower = rel.lower()
    if lower.endswith(".svg"):
        size = svg_size(blob)
        if size is None:
            errors.append(
                f"{label} ({rel}) needs numeric square width/height on <svg> "
                "-- percentage or missing dimensions fail validation"
            )
            return
    elif lower.endswith(".png"):
        size = png_size(blob)
        if size is None:
            errors.append(f"{label} ({rel}) is not a readable PNG")
            return
    else:
        warnings.append(f"{label} ({rel}): dimensions not checked by this script")
        return

    w, h = size
    if w != h:
        errors.append(f"{label} ({rel}) must be square, got {w:g}x{h:g}")
    if not (48 <= w <= 4096):
        errors.append(f"{label} ({rel}) must be 48-4096 px, got {w:g}")


def check_openai_yaml(zf, skill_dir, skill_name, names):
    """Validate the optional agents/openai.yaml that carries skill interface settings."""
    path = f"{skill_dir}/agents/openai.yaml"
    if path not in names:
        return
    text = zf.read(path).decode("utf-8", "replace")

    tops = {m.group(1) for m in re.finditer(r"^([A-Za-z_][\w-]*):", text, re.M)}
    for unknown in sorted(tops - OPENAI_YAML_SECTIONS):
        warnings.append(f"{path}: unrecognized top-level section {unknown!r}")

    iface = parse_yaml_section(text, "interface")
    for unknown in sorted(set(iface) - OPENAI_YAML_INTERFACE):
        warnings.append(f"{path}: unrecognized interface key {unknown!r}")

    for field in ("icon_small", "icon_large"):
        if iface.get(field):
            check_image(zf, f"{skill_dir}/", f"{path}:{field}", iface[field])

    color = iface.get("brand_color")
    if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        errors.append(f"{path}: brand_color must be six-digit hex, got {color!r}")

    desc = iface.get("short_description")
    if desc and not 25 <= len(desc) <= 64:
        warnings.append(
            f"{path}: short_description is {len(desc)} chars; 25-64 scans best"
        )

    prompt = iface.get("default_prompt")
    if prompt and f"${skill_name}" not in prompt:
        warnings.append(
            f"{path}: default_prompt should name the skill as ${skill_name}"
        )


def check_skill(zf, path, plugin_name, names):
    body = zf.read(path).decode("utf-8", "replace")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", body, re.S)
    if not m:
        errors.append(f"{path}: missing YAML frontmatter")
        return
    fm = m.group(1)

    keys = {k.group(1) for k in re.finditer(r"^([A-Za-z_][\w-]*):", fm, re.M)}
    if "metadata" in keys:
        errors.append(
            f"{path}: remove 'metadata' from the frontmatter -- it does not configure "
            "the skill interface; put supported interface settings under 'interface' "
            "in agents/openai.yaml"
        )
    for unknown in sorted(keys - SKILL_FRONTMATTER - {"metadata"}):
        warnings.append(f"{path}: unrecognized frontmatter field {unknown!r}")

    fields = {
        k: re.search(rf"^{k}:\s*(.+?)\s*$", fm, re.M) for k in ("name", "description")
    }
    if not fields["name"] or not fields["description"]:
        errors.append(f"{path}: frontmatter needs both 'name' and 'description'")
        return

    name = fields["name"].group(1).strip()
    desc = fields["description"].group(1).strip()
    folder = path.split("/")[-2]

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append(
            f"{path}: name {name!r} must be <=64 chars, lowercase alphanumeric and "
            "single hyphens, not leading/trailing"
        )
    if name != folder:
        errors.append(f"{path}: name {name!r} must match its folder {folder!r}")
    if not 1 <= len(desc) <= 1024:
        errors.append(f"{path}: description is {len(desc)} chars (limit 1024)")
    if len(f"{plugin_name}-{name}") > 64:
        errors.append(f"{path}: combined plugin+skill identifier exceeds 64 chars")

    check_openai_yaml(zf, path.rsplit("/", 1)[0], name, names)


def main(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        if zf.testzip() is not None:
            errors.append("archive is corrupt")
        names = [n for n in zf.namelist() if not n.startswith("__MACOSX/")]

        if len(names) > 5000:
            errors.append(f"{len(names)} entries exceeds the 5,000 limit")
        total = sum(zf.getinfo(n).file_size for n in names)
        if total > 512 * 1024 * 1024:
            errors.append("uncompressed size exceeds 512 MB")
        for n in names:
            if ".." in n.split("/"):
                errors.append(f"path traversal in entry: {n}")
            if zf.getinfo(n).file_size > 100 * 1024 * 1024:
                errors.append(f"{n} exceeds the 100 MiB per-file limit")

        # Exactly one plugin root: archive root, or one top-level directory.
        tops = {n.split("/")[0] for n in names}
        if any(f"{d}/plugin.json" in names for d in MANIFEST_DIRS):
            root = ""
        elif len(tops) == 1:
            root = f"{tops.pop()}/"
        else:
            errors.append(
                "ZIP must contain exactly one plugin root -- found multiple top-level "
                f"entries: {sorted(tops)}"
            )
            return report()

        manifest_path = next(
            (f"{root}{d}/plugin.json" for d in MANIFEST_DIRS if f"{root}{d}/plugin.json" in names),
            None,
        )
        if not manifest_path:
            errors.append(
                "Plugin manifest not found -- add .codex-plugin/plugin.json at the ZIP "
                "root or inside its only top-level directory"
            )
            return report()

        try:
            manifest = json.loads(zf.read(manifest_path))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{manifest_path} is not valid UTF-8 JSON: {exc}")
            return report()

        # Skills-only exclusions.
        for key in ("mcpServers", "apps"):
            if key in manifest:
                errors.append(f"skills-only bundle must not declare {key!r} in the manifest")
        for junk in (".mcp.json", ".app.json"):
            if f"{root}{junk}" in names:
                errors.append(f"skills-only bundle must not include {junk}")

        interface = manifest.get("interface", {})
        if "screenshots" in interface:
            errors.append("skills-only bundle must not declare interface.screenshots")

        name = manifest.get("name", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) or len(name) > 64:
            errors.append(f"plugin name {name!r} is invalid")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+].+)?", manifest.get("version", "")):
            errors.append(f"version {manifest.get('version')!r} is not semver")
        if len(manifest.get("description", "")) > 1024:
            errors.append("plugin description exceeds 1024 chars")
        if len(manifest.get("author", {}).get("name", "")) > 120:
            errors.append("author.name exceeds 120 chars")

        for field, limit in INTERFACE_LIMITS.items():
            val = interface.get(field)
            if not val or not val.strip():
                errors.append(f"interface.{field} is required")
            elif len(val) > limit:
                errors.append(
                    f"interface.{field} is {len(val)} chars (limit {limit}): {val!r}"
                )
        if interface.get("category") not in CATEGORIES:
            errors.append(
                f"interface.category {interface.get('category')!r} is not approved; "
                f"use one of {sorted(CATEGORIES)}"
            )

        caps = interface.get("capabilities", [])
        if len(caps) > 20 or any(len(c) > 120 for c in caps):
            errors.append("interface.capabilities: max 20 entries, 120 chars each")
        prompts = interface.get("defaultPrompt", [])
        if len(prompts) > 3 or any(len(p) > 128 for p in prompts):
            errors.append("interface.defaultPrompt: max 3 entries, 128 chars each")

        for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL", "supportURL"):
            url = interface.get(field)
            if url and (not url.startswith("https://") or len(url) > 1024):
                errors.append(f"interface.{field} must be HTTPS and <=1024 chars")
        for field in ("brandColor", "brandColorDark"):
            color = interface.get(field)
            if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                errors.append(f"interface.{field} must be six-digit hex, got {color!r}")

        for field in ("logo", "composerIcon"):
            if interface.get(field):
                check_image(zf, root, f"interface.{field}", interface[field])

        skills = [
            n for n in names
            if re.fullmatch(rf"{re.escape(root)}skills/[^/]+/SKILL\.md", n, re.I)
        ]
        if not skills:
            errors.append("skills-only bundle needs at least one skills/<skill>/SKILL.md")
        for path in skills:
            check_skill(zf, path, name, names)

        stray = [
            n for n in names
            if re.search(r"/skills/[^/]+/.*SKILL\.md$", f"/{n}", re.I) and n not in skills
        ]
        if stray:
            errors.append(f"exactly one SKILL.md per skill folder; also found: {stray}")

        print(f"Bundle: {root or '(archive root)'}  manifest: {manifest_path}")
        print(f"Skills: {len(skills)}  entries: {len(names)}  uncompressed: {total / 1024:.1f} KB")

    return report()


def report():
    for w in warnings:
        print(f"  warning: {w}")
    if errors:
        print(f"\nFAILED ({len(errors)} error{'s' if len(errors) > 1 else ''}):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nPASSED: bundle satisfies the skills-only submission rules.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
