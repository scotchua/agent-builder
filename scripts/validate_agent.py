#!/usr/bin/env python3
"""Check the agent files the agent-builder skill created, in plain words.

Usage:
    python3 validate_agent.py PATH [PATH ...]

A file named SKILL.md (or a folder holding one) is checked as a skill, any other
.md file as a Claude helper (subagent), and a .toml file as a Codex custom agent.
Each file is also checked for anything that looks like a password or key; the
suspected value itself is never printed. That check is best effort: it matches
common patterns and will not catch every leaked password or key.

Standard library only. Python 3.9 or later; 3.11 or later also checks Codex TOML.
Exit code 1 if any ERROR was found, otherwise 0.
"""

import re
import sys
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_SKILL_BODY_LINES = 500

CLAUDE_MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
CLAUDE_MODES = {"default", "acceptEdits", "auto", "dontAsk", "bypassPermissions", "plan"}
CODEX_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
CODEX_SANDBOXES = {"read-only", "workspace-write", "danger-full-access"}

SECRET_PATTERNS = [
    ("an OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("a GitHub token", re.compile(r"\b(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("a Slack token", re.compile(r"\bxox[bp]-[A-Za-z0-9-]{10,}")),
    ("an AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # A setting at the start of a line (optionally after -, #, >, *, export, or a quote),
    # so prose such as "never set api_key: ..." in the middle of a sentence is not flagged.
    ("a password or key setting", re.compile(
        r"(?i)^\s*(?:[-#>*]\s*)?(?:export\s+)?[\"']?(password|passwd|api[_-]?key|apikey|secret|token)[\"']?"
        r"\s*[:=]\s*(?![<\[$])\S{8,}")),
    # The same setting inside an inline mapping on one line: {"token": "..."} or {name: x, token: ...}.
    # Quoted syntax in prose, a table cell, or backticks, or a comma in a sentence, has no { before it.
    ("a password or key setting", re.compile(
        r"(?i)\{(?:[^{}]*,)?\s*[\"']?(password|passwd|api[_-]?key|apikey|secret|token)[\"']?"
        r"\s*[:=]\s*[\"']?(?![<\[$])[^\s\"',}]{8,}")),
]
BLOCK_INDICATORS = {"|", ">", "|-", ">-", "|+", ">+"}


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        self.files = 0
        self.lines = []

    def error(self, where, msg):
        self.errors += 1
        self.lines.append("ERROR: %s: %s" % (where, msg))

    def warning(self, where, msg):
        self.warnings += 1
        self.lines.append("WARNING: %s: %s" % (where, msg))

    def ok(self, where):
        self.lines.append("OK: %s looks fine." % where)


def parse_frontmatter(text):
    """Return (fields, body, problem). problem is None, 'missing', or 'unclosed'."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text, "missing"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, "", "unclosed"
    fields = {}
    problems = []
    block = lines[1:end]
    i = 0
    while i < len(block):
        line = block[i]
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m or line[:1] in (" ", "\t"):
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        if key in fields:
            problems.append("`%s` appears twice in the frontmatter; keep one." % key)
        if value[:1] in ("\"", "'") and (len(value) < 2 or value[-1] != value[0]):
            problems.append("the value of `%s` opens a quote that is never closed." % key)
        i += 1
        follow = []
        while i < len(block) and (block[i][:1] in (" ", "\t") or block[i].strip() == ""):
            follow.append(block[i])
            i += 1
        if value in BLOCK_INDICATORS:
            parts = [l.strip() for l in follow if l.strip()]
            fields[key] = ("\n" if value.startswith("|") else " ").join(parts)
        elif value == "" and follow and all(l.strip().startswith("- ") or not l.strip() for l in follow):
            fields[key] = [unquote(l.strip()[2:].strip()) for l in follow if l.strip()]
        elif value == "" and follow:
            fields[key] = " ".join(l.strip() for l in follow if l.strip())
        else:
            fields[key] = unquote(value)
    body = "\n".join(lines[end + 1:])
    fields["__problems__"] = problems
    return fields, body, None


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def check_name(report, where, name):
    if not isinstance(name, str) or not name:
        report.error(where, "`name` is missing.")
        return False
    good = True
    if len(name) > MAX_NAME:
        report.error(where, "`name` is %d characters; the limit is %d." % (len(name), MAX_NAME))
        good = False
    if re.search(r"[^a-z0-9-]", name):
        report.error(where, "`name` can only use lowercase letters, digits, and hyphens.")
        good = False
    if name.startswith("-"):
        report.error(where, "`name` cannot start with a hyphen.")
        good = False
    if name.endswith("-"):
        report.error(where, "`name` cannot end with a hyphen.")
        good = False
    if "--" in name:
        report.error(where, "`name` cannot contain two hyphens in a row.")
        good = False
    return good


def check_description(report, where, desc):
    if not isinstance(desc, str) or not desc.strip():
        report.error(where, "`description` is missing or empty; it is what decides when the agent is used.")
        return
    if len(desc) > MAX_DESCRIPTION:
        report.error(where, "`description` is %d characters; the limit is %d." % (len(desc), MAX_DESCRIPTION))


def check_skill(report, path, text):
    where = str(path)
    fields, body, problem = parse_frontmatter(text)
    if problem == "missing":
        report.error(where, "no frontmatter; the file must start with a line of three hyphens (---).")
        return
    if problem == "unclosed":
        report.error(where, "the frontmatter is never closed; add a line of three hyphens (---) after it.")
        return
    for msg in fields.pop("__problems__", []):
        report.error(where, msg)
    name = fields.get("name")
    folder = path.resolve().parent.name
    if check_name(report, where, name) and name != folder:
        report.error(where, "`name` is \"%s\" but the folder is \"%s\"; they must match." % (name, folder))
    check_description(report, where, fields.get("description"))
    body_lines = len(body.splitlines())
    if body_lines > MAX_SKILL_BODY_LINES:
        report.warning(where, "the instructions are %d lines; over %d, move reference material into separate files."
                       % (body_lines, MAX_SKILL_BODY_LINES))


def check_subagent(report, path, text):
    where = str(path)
    fields, body, problem = parse_frontmatter(text)
    if problem == "missing":
        report.error(where, "no frontmatter; the file must start with a line of three hyphens (---).")
        return
    if problem == "unclosed":
        report.error(where, "the frontmatter is never closed; add a line of three hyphens (---) after it.")
        return
    for msg in fields.pop("__problems__", []):
        report.error(where, msg)
    name = fields.get("name")
    if check_name(report, where, name) and name != path.stem:
        report.warning(where, "`name` is \"%s\" but the file is \"%s\"; matching them avoids confusion."
                       % (name, path.name))
    check_description(report, where, fields.get("description"))
    model = fields.get("model")
    if model and model not in CLAUDE_MODELS and not str(model).startswith("claude-"):
        report.warning(where, "model \"%s\" is not one this checker knows; confirm it in your app." % model)
    effort = fields.get("effort")
    if effort and effort not in CLAUDE_EFFORTS:
        report.warning(where, "effort \"%s\" is not one this checker knows; confirm it in your app." % effort)
    mode = fields.get("permissionMode")
    if mode == "bypassPermissions":
        report.error(where, "permissionMode bypassPermissions turns off safety prompts; this skill never uses it. "
                            "Use default, or allow only the specific safe actions.")
    elif mode and mode not in CLAUDE_MODES:
        report.warning(where, "permissionMode \"%s\" is not one this checker knows; confirm it in your app." % mode)
    if "tools" not in fields:
        report.warning(where, "no `tools` list, so it can use every tool the main session can; list only what the job needs.")
    else:
        tools = fields["tools"]
        names = tools if isinstance(tools, list) else [t.strip() for t in str(tools).split(",")]
        names = [n.split("(")[0].strip() for n in names]
        if "Agent" in names:
            report.warning(where, "`tools` includes Agent, so this helper can start other helpers; leave it out unless the job needs that.")
        if "Bash" in names:
            report.warning(where, "`tools` includes Bash, so this helper can run any command; leave it out unless the job needs that.")
    if not body.strip():
        report.warning(where, "there are no instructions after the frontmatter.")


def check_toml(report, path, text):
    where = str(path)
    if tomllib is None:
        report.warning(where, "could not be checked: Python 3.11 or later is needed to read TOML files.")
        return
    try:
        data = tomllib.loads(text)
    except (ValueError, TypeError) as exc:
        report.error(where, "is not valid TOML (%s)." % type(exc).__name__)
        return
    for key in ("name", "description", "developer_instructions"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            report.error(where, "`%s` is required and must be a non-empty text value in quotes." % key)
    name = data.get("name")
    if isinstance(name, str) and name.strip() and name != path.stem:
        report.warning(where, "`name` is \"%s\" but the file is \"%s\"; matching them avoids confusion."
                       % (name, path.name))
    effort = data.get("model_reasoning_effort")
    if effort is not None and effort not in CODEX_EFFORTS:
        report.warning(where, "model_reasoning_effort \"%s\" is not one this checker knows; confirm it in Codex." % effort)
    sandbox = data.get("sandbox_mode")
    if sandbox == "danger-full-access":
        report.error(where, "sandbox_mode danger-full-access gives it full access to your computer; this skill never uses it. "
                            "Use read-only or workspace-write.")
    elif sandbox is not None and sandbox not in CODEX_SANDBOXES:
        report.warning(where, "sandbox_mode \"%s\" is not one this checker knows; confirm it in Codex." % sandbox)


def check_secrets(report, path, text):
    for number, line in enumerate(text.split("\n"), start=1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                report.error(str(path), "line %d looks like it contains %s. Remove it and use the app's own "
                                        "credential or connector setup instead." % (number, label))
                break


def check_path(report, raw):
    path = Path(raw)
    if path.is_dir():
        path = path / "SKILL.md"
    if not path.is_file():
        report.error(raw, "does not exist.")
        return
    if path.name == "SKILL.md":
        kind = check_skill
    elif path.suffix == ".md":
        kind = check_subagent
    elif path.suffix == ".toml":
        kind = check_toml
    else:
        report.error(str(path), "unsupported file; this checker reads SKILL.md, helper .md, and Codex .toml files.")
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        report.error(str(path), "could not be read.")
        return
    report.files += 1
    before = (report.errors, report.warnings)
    kind(report, path, text)
    check_secrets(report, path, text)
    if (report.errors, report.warnings) == before:
        report.ok(str(path))


def main(argv=None, out=None):
    argv = sys.argv[1:] if argv is None else argv
    out = out or sys.stdout
    if not argv:
        out.write(__doc__.split("\n\n")[1].strip() + "\n")
        return 2
    report = Report()
    for raw in argv:
        check_path(report, raw)
    for line in report.lines:
        out.write(line + "\n")
    out.write("Checked %d file(s): %d error(s), %d warning(s).\n" % (report.files, report.errors, report.warnings))
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
