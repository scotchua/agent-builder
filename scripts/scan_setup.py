#!/usr/bin/env python3
"""Read-only inventory of a person's Claude and Codex setup, for the agent-builder skill.

Prints names, one-line descriptions, schedules, instruction headings, and a summary of
agent-related settings. Skill and agent files are read only up to the end of their
frontmatter; settings files are read whole (at most 64 KB) so they can be parsed, but
environment values, keys, hook commands, and prompts are never printed. It never opens
credential files, chat history, or memory stores. The allowlist below is the whole list of
what it reads; everything else is skipped.

Usage:
    python3 scan_setup.py                 # personal setup only
    python3 scan_setup.py --project DIR   # also scan one project folder

Standard library only. Python 3.8 or later; 3.11 or later also reads Codex TOML fields. Works on macOS, Linux, and Windows.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:  # Python 3.11+. Without it, TOML files are listed by file name only (fail closed).
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

MAX_BYTES = 64 * 1024
MAX_DESC = 240
MAX_ITEMS = 60
MAX_HEADINGS = 25
VOICE_WORDS = re.compile(r"\b(brand|voice|tone|style|letterhead|writing|house style)\b", re.I)

# Only files with these exact names (or, for agent folders, these suffixes) are ever opened,
# and the check is made on the link's final destination, so a link named SKILL.md that points
# at a key file is refused.
ALLOWED_NAMES = {"SKILL.md", "AGENTS.md", "CLAUDE.md", "settings.json", "config.toml",
                 "automation.toml", "installed_plugins.json"}
ALLOWED_SUFFIXES = {".md", ".toml"}
DENIED_PARTS = re.compile(r"(^|[\\/])(\.ssh|\.gnupg|\.aws|\.azure|\.kube|\.docker|keychains?|"
                          r"auth\.json|\.claude\.json|\.env[^\\/]*|[^\\/]*credential[^\\/]*|"
                          r"[^\\/]*secret[^\\/]*|[^\\/]*token[^\\/]*|id_[^\\/]*|[^\\/]*\.(pem|key|p12|pfx))$|"
                          r"(^|[\\/])(\.ssh|\.gnupg|\.aws|keychains?|memory|memories|sessions|archived_sessions|"
                          r"transcripts|history|shell_snapshots)([\\/]|$)", re.I)
NOTES = []


def private_roots():
    """Folders that hold chat history or memory. Nothing under them is ever opened."""
    home = Path.home()
    roots = [home / ".claude" / "projects", home / ".codex" / "sessions",
             home / ".codex" / "archived_sessions", home / ".codex" / "memories"]
    out = []
    for r in roots:
        try:
            out.append(r.resolve())
        except (OSError, RuntimeError):
            pass
    return out


def note(msg):
    if msg not in NOTES:
        NOTES.append(msg)


def safe_target(path, agent_file=False):
    """Resolved destination if it is an allowed kind of file, else None.

    Checked before anything is opened. SKILL.md and agent files may link to any
    Markdown or TOML file (some people keep the real file elsewhere), but never
    into a credential, memory, session, or history location."""
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not real.is_file():
        return None
    ok_name = real.name in ALLOWED_NAMES or (agent_file and real.suffix in ALLOWED_SUFFIXES)
    in_private = any(root == real or root in real.parents for root in private_roots())
    if not ok_name or in_private or DENIED_PARTS.search(str(real)):
        note("refused to open %s (link destination is not an allowed file)" % path)
        return None
    return real


def read_head(path, agent_file=False):
    """Read at most MAX_BYTES of an allowed small text file, or None."""
    real = safe_target(path, agent_file)
    if real is None:
        return None
    try:
        with open(real, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read(MAX_BYTES + 1)
    except OSError:
        note("could not read %s" % path)
        return None
    if len(text) > MAX_BYTES:
        note("only the first %d KB of %s were read" % (MAX_BYTES // 1024, path))
        text = text[:MAX_BYTES]
    return text


def read_frontmatter(path):
    """Read a Markdown file only up to the end of its frontmatter, or None.

    Stops at the closing '---' line, so the body of a skill or agent is never read."""
    real = safe_target(path, agent_file=True)
    if real is None:
        return None
    lines, size = [], 0
    try:
        with open(real, "r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
            if first.strip() != "---":
                return ""
            lines.append(first)
            for line in fh:
                size += len(line)
                if size > MAX_BYTES:
                    note("frontmatter of %s is over %d KB; it was not read in full" % (path, MAX_BYTES // 1024))
                    break
                lines.append(line)
                if line.strip() == "---":
                    break
    except OSError:
        note("could not read %s" % path)
        return None
    return "".join(lines)


def capped(items, where):
    items = sorted(items)
    if len(items) > MAX_ITEMS:
        note("%s has %d entries; only the first %d were listed" % (where, len(items), MAX_ITEMS))
    return items[:MAX_ITEMS]


def clip(text):
    text = " ".join(str(text).split())
    return text if len(text) <= MAX_DESC else text[: MAX_DESC - 3] + "..."


def frontmatter(text):
    """Return name and description from YAML frontmatter, without a YAML library."""
    if not text or not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].splitlines()
    out, key, buf = {}, None, []
    for line in block:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key in ("name", "description"):
                out[key] = " ".join(buf).strip()
            key, first = m.group(1), m.group(2).strip()
            buf = [] if first in ("|", ">", "|-", ">-", "") else [first.strip("\"'")]
        elif key and line.startswith(" "):
            buf.append(line.strip())
    if key in ("name", "description"):
        out[key] = " ".join(buf).strip()
    return {k: clip(v) for k, v in out.items() if v}


def toml_keys(text, keys, where):
    """Top-level string keys from a TOML file. Fails closed without a real TOML parser."""
    if text is None:
        return {}
    if tomllib is None:
        note("TOML files were listed by name only; Python 3.11 or later is needed to read %s safely" % where)
        return {}
    try:
        data = tomllib.loads(text)
    except (ValueError, TypeError):
        note("could not parse %s" % where)
        return {}
    return {k: clip(v) for k, v in data.items() if k in keys and isinstance(v, str)}


def headings(path):
    text = read_head(path)
    if text is None:
        return None
    hs = [l.strip() for l in text.splitlines() if re.match(r"^#{1,3}\s", l)]
    return hs[:MAX_HEADINGS]


def list_skills(folder):
    items = []
    if not folder.is_dir():
        return items
    for d in capped(folder.iterdir(), str(folder)):
        if not d.is_dir() or not (d / "SKILL.md").exists():
            continue
        if safe_target(d / "SKILL.md", agent_file=True) is None:
            continue  # refused: noted, and not listed as an installed skill
        fm = frontmatter(read_frontmatter(d / "SKILL.md"))
        items.append({"name": fm.get("name", d.name), "description": fm.get("description", "")})
    return items


def list_md_agents(folder):
    items = []
    if not folder.is_dir():
        return items
    for f in capped(folder.glob("*.md"), str(folder)):
        if safe_target(f, agent_file=True) is None:
            continue  # refused or unreadable: not listed
        fm = frontmatter(read_frontmatter(f))
        items.append({"name": fm.get("name", f.stem), "description": fm.get("description", "")})
    return items


def list_toml_agents(folder):
    items = []
    if not folder.is_dir():
        return items
    for f in capped(folder.glob("*.toml"), str(folder)):
        if safe_target(f, agent_file=True) is None:
            continue  # refused or unreadable: not listed
        kv = toml_keys(read_head(f, agent_file=True),
                       {"name", "description", "model", "model_reasoning_effort", "sandbox_mode"}, str(f))
        kv.setdefault("name", f.stem)
        items.append(kv)
    return items


def claude_settings(path):
    """Permission mode, rule counts, extra folders, hook event names. Never env or helpers."""
    text = read_head(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return {"note": "present but not readable as JSON"}
    perms = data.get("permissions") or {}
    return {
        "defaultMode": perms.get("defaultMode"),
        "allow_rules": len(perms.get("allow") or []),
        "ask_rules": len(perms.get("ask") or []),
        "deny_rules": len(perms.get("deny") or []),
        "additionalDirectories": perms.get("additionalDirectories") or data.get("additionalDirectories") or [],
        "hook_events": sorted((data.get("hooks") or {}).keys()),
    }


def scheduled_claude(folder):
    items = []
    if not folder.is_dir():
        return items
    for d in capped(folder.iterdir(), str(folder)):
        fm = frontmatter(read_frontmatter(d / "SKILL.md")) if d.is_dir() else {}
        if fm:
            items.append(fm)
    return items


def scheduled_codex(folder):
    items = []
    if not folder.is_dir():
        return items
    for d in capped(folder.iterdir(), str(folder)):
        if not d.is_dir():
            continue
        kv = toml_keys(read_head(d / "automation.toml"), {"name", "status", "rrule", "kind"}, str(d))
        items.append(kv or {"name": d.name})
    return items


def claude_plugins(path):
    """Skills and agents shipped inside installed Claude Code plugins (names only)."""
    text = read_head(path)
    if text is None:
        return []
    try:
        data = json.loads(text).get("plugins", {})
    except (ValueError, AttributeError):
        return []
    out = []
    plugins_root = path.parent.resolve()
    seen = set()
    for plugin_id in capped(data.keys(), "installed plugins"):
        installs = data[plugin_id]
        installs = installs if isinstance(installs, list) else [installs]
        if not installs:
            note("plugin %s has no install records; nothing listed for it" % plugin_id)
        prefix = plugin_id.split("@")[0]
        for inst in installs:
            raw = inst.get("installPath", "") if isinstance(inst, dict) else ""
            try:
                root = Path(raw).resolve(strict=True) if raw else None
            except (OSError, RuntimeError):
                root = None
            if not root or not root.is_dir() or plugins_root not in root.parents:
                note("skipped an install of plugin %s (install path missing or outside the plugins folder)" % plugin_id)
                continue
            if root in seen:
                continue
            seen.add(root)
            skills = list_skills(root / "skills")
            agents = list_md_agents(root / "agents")
            out.append({
                "plugin": prefix,
                "scope": inst.get("scope"),
                "skills": [dict(s, name=prefix + ":" + s["name"]) for s in skills],
                "agents": [dict(a, name=prefix + ":" + a["name"]) for a in agents],
            })
    return out


def scan(project):
    home = Path.home()
    report = {"claude": {}, "codex": {}, "project": {}}
    c = report["claude"]
    c["skills"] = list_skills(home / ".claude" / "skills")
    c["plugins"] = claude_plugins(home / ".claude" / "plugins" / "installed_plugins.json")
    c["agents"] = list_md_agents(home / ".claude" / "agents")
    c["scheduled_tasks"] = scheduled_claude(home / ".claude" / "scheduled-tasks")
    c["instructions_headings"] = headings(home / ".claude" / "CLAUDE.md")
    c["settings"] = claude_settings(home / ".claude" / "settings.json")
    x = report["codex"]
    x["skills"] = list_skills(home / ".agents" / "skills") + list_skills(home / ".codex" / "skills")
    x["agents"] = list_toml_agents(home / ".codex" / "agents")
    x["scheduled_tasks"] = scheduled_codex(home / ".codex" / "automations")
    x["instructions_headings"] = headings(home / ".codex" / "AGENTS.md")
    x["defaults"] = toml_keys(read_head(home / ".codex" / "config.toml"),
                              {"model", "model_reasoning_effort", "sandbox_mode", "approval_policy"},
                              "~/.codex/config.toml")
    if project:
        p = Path(project).expanduser()
        pr = report["project"]
        pr["path"] = str(p)
        pr["claude_skills"] = list_skills(p / ".claude" / "skills")
        pr["claude_agents"] = list_md_agents(p / ".claude" / "agents")
        pr["claude_settings"] = claude_settings(p / ".claude" / "settings.json")
        pr["codex_skills"] = list_skills(p / ".agents" / "skills")
        pr["codex_agents"] = list_toml_agents(p / ".codex" / "agents")
        pr["CLAUDE.md_headings"] = headings(p / "CLAUDE.md")
        pr["AGENTS.md_headings"] = headings(p / "AGENTS.md")
    voice = []
    plugin_skills = [s for p in c["plugins"] for s in p["skills"]]
    for group in (c["skills"], plugin_skills, x["skills"], report["project"].get("claude_skills", []),
                  report["project"].get("codex_skills", [])):
        for s in group:
            if VOICE_WORDS.search(s.get("name", "") + " " + s.get("description", "")):
                voice.append(s["name"])
    report["possible_brand_or_voice_skills"] = sorted(set(voice))
    report["scan_notes"] = NOTES or ["complete: nothing skipped or truncated"]
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", help="optional project folder to include")
    args = ap.parse_args()
    json.dump(scan(args.project), sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
