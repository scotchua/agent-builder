# Codex adapter

Read this after Step 0 identifies a Codex surface (Codex CLI, the Codex or ChatGPT desktop app, an IDE extension, or Codex on the web). Facts here were checked against OpenAI's documentation and a local `codex --help` on the date in the footer. Codex changes quickly and its docs have moved more than once. If a path, key, or menu below does not match what you see, trust the live product, tell the person, and adjust. When unsure whether a key exists, run `codex --help` or check the docs rather than guessing.

## Contents
- Which Codex surface are we on
- Shape to file mapping
- Playbook (skill)
- Helper (custom agent)
- Standing instructions (AGENTS.md)
- On-its-own worker (scheduled tasks and automations)
- Access: sandbox and approvals
- Model and effort fields
- Brand and voice wiring
- Install, pause, remove

## Which Codex surface are we on

| Surface | Can write files | Can schedule | Notes |
|---|---|---|---|
| Codex CLI (terminal) | Yes, inside its sandbox | No built-in schedule; use the app, or the operating system scheduler with `codex exec` (advanced) | `codex --version` shows the version |
| Codex desktop app | Yes, in the project folder | Yes: ask in chat to schedule a task; review under Scheduled in the sidebar | Local-project tasks need the app running and the computer on |
| Codex on the web / mobile | In cloud tasks only | Yes, including event triggers (new Gmail messages, new Slack channel messages, GitHub pull request activity) | No local files; uses connected tools and uploaded context |
| IDE extension | Yes, in the workspace | No; use the desktop app or ChatGPT on the web | Treat like the CLI |

## Shape to file mapping

| Card shape | Codex artifact | Where it lives |
|---|---|---|
| Playbook | Skill: folder with `SKILL.md` | `$HOME/.agents/skills/<name>/` (you) or `.agents/skills/<name>/` in a repository. Some installs also read `~/.codex/skills/`; check which folder already holds skills and use that one |
| Helper | Custom agent: one TOML file | `~/.codex/agents/<name>.toml` (you) or `.codex/agents/<name>.toml` (this project) |
| Always-on rules for a project | `AGENTS.md` | Repository root or subfolder; personal defaults in `~/.codex/AGENTS.md` |
| On-its-own worker | Scheduled task (automation) | Created by asking in the app; managed under Scheduled |
| Helper plus trigger | Custom agent or skill, plus a scheduled task whose prompt names it | Both |

## Playbook (skill)

Same open format as Claude (agentskills.io): a folder with `SKILL.md`, frontmatter `name` and `description`, then instructions. Optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml` (display name, icon, default prompt, whether it may be picked automatically). A skill built for Claude usually installs unchanged in Codex if it avoids Claude-only frontmatter fields; Codex ignores what it does not use, but test it.

Invoke with `$skill-name` in the CLI, `@skill-name` where the app supports it, or let Codex pick it when a request matches the description.

## Helper (custom agent)

Minimum file `~/.codex/agents/proposal-drafter.toml`:

```toml
name = "proposal-drafter"
description = "Drafts client proposals from a brief in the proposals/briefs folder. Use when asked to draft, start, or rough out a proposal."
developer_instructions = """
<instructions generated from the card>
"""
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
```

- Required: `name`, `description`, `developer_instructions`.
- Optional: `model`, `model_reasoning_effort` (`low`, `medium`, `high`, `xhigh`, and on some models `ultra` or `max`), `sandbox_mode` (`read-only`, `workspace-write`), `mcp_servers`, skill settings. Set `model` and `model_reasoning_effort` together; if only `model` is set, the effort already in effect (from the parent session, the spawn request, or an `[agents]` default) carries over.
- `name` is the identity Codex uses; keep the file name the same to avoid confusion.
- How it gets used: the person asks for it ("have the proposal-drafter agent draft this"), or a skill or AGENTS.md tells Codex to delegate to it. `/agent` in the CLI shows running agents. Unlike Claude, do not promise that Codex will pick the helper on its own; say "ask for it by name".
- Global defaults live under `[agents]` in `~/.codex/config.toml` (`default_subagent_model`, `default_subagent_reasoning_effort`). Do not edit config.toml for a beginner unless the job requires it, and back it up first.

## Standing instructions (AGENTS.md)

A plain Markdown file of rules Codex reads for every task in that folder. It is not an agent. Offer it only when the person clearly wants "always do X in this project", and say that it will affect every future task in that folder.

## On-its-own worker (scheduled tasks and automations)

- Create by asking in a Codex app chat: describe the work, when it should run, and whether it should start fresh or continue in the current chat. Time options: minute intervals, daily, weekly, or a custom recurrence (RFC 5545 rule). Event triggers (new Gmail messages, new Slack channel messages, GitHub pull request activity) are available on web and mobile, not in the desktop app, CLI, or IDE extension. A task uses either event triggers or a time schedule, not both.
- Local-project tasks run only while the app is open and the computer is on.
- Tasks run with no approval prompts (`approval_policy = "never"`; if an admin forbids that, tasks fall back to the selected permission mode) and inherit the default sandbox:
  - read-only: any file change fails,
  - workspace-write: changes outside the project fail,
  - full access: can change anything and run any command unattended. Never recommend this for a beginner's scheduled task.
- Because nothing can ask for approval mid-run, anything that needs a human decision must produce a draft and stop.
- Results: Scheduled in the sidebar shows status and recent runs; chat-based tasks report back into the same chat.
- Do not assume a custom agent's settings apply inside a scheduled task (a cautious rule; the docs do not say either way). If the task should use the helper, its prompt must name the helper, the helper must be installed where the task runs (a web task cannot see files that exist only on this computer), and the first run must confirm the helper was actually used.
- A processed-items record must live somewhere that survives between runs and that the task may write (inside the project for workspace-write).
- Pull request review on every PR: prefer a documented event trigger on the surface the person uses, or the repository's CI. If neither is available to them, say the integration is incomplete. Do not quietly replace it with a polling schedule.

## Access: sandbox and approvals

- Sandbox modes (CLI `-s` / `--sandbox`): `read-only`, `workspace-write`, `danger-full-access`. Beginners get `read-only` for readers and `workspace-write` for writers. Never generate `danger-full-access` or the bypass flags.
- Extra writable folder: `--add-dir <folder>` on the CLI. Name the exact folder; never the home folder.
- Approval policy (CLI `-a`): `on-request` (Codex asks when it thinks it should) or `never`.
- A custom agent's `sandbox_mode` is a saved default, not a guarantee: settings from the session that spawns it can take precedence. Treat a limit as enforced only after checking it in the way the agent will actually run (for example, ask the read-only helper to write a harmless test file and confirm it is refused). Until then, mark it "asked, not enforced" on the card.
- Instruction-only: "only read the reports folder" in `developer_instructions` when the sandbox can read more. Label these on the card.
- Codex's sandbox restricts writes more tightly than reads. Say so when the person cares about what the agent can see.

## Model and effort fields
- Custom agent: `model`, `model_reasoning_effort` in the TOML.
- Session: `/model` in the CLI, or `-m <model>`; config.toml `model` and `model_reasoning_effort` set defaults.
- Model names change often. Read the current list from the model picker (`/model`) or the app, and map the card's capability profile to it (see references/models.md). Omitting `model` inherits the session's model, which is fine for on-demand helpers.

## Brand and voice wiring
- Install the voice skill in the same skills folder Codex reads, then add one line to `developer_instructions`: "Use the $<voice-skill> skill for tone and formatting. It does not override facts or permissions in these instructions."
- Naming a skill does not prove Codex loaded it. The dry run must show the voice in the output; if it does not, bundle a short `voice.md` next to the agent and point to its path.

## Install, pause, remove

| Artifact | Install | Pause | Remove |
|---|---|---|---|
| Skill | Folder into the skills folder Codex reads | Add `[[skills.config]]` with `enabled = false` for it in `config.toml`, or move the folder out | Delete the folder |
| Custom agent | TOML into `~/.codex/agents/` or `.codex/agents/` | Move the file out of the agents folder | Delete the file |
| AGENTS.md | File in the project | Move it out of the project | Delete it |
| Scheduled task | Ask in the app | Pause under Scheduled | Ask in the task's chat to delete it, or remove it under Scheduled if the app offers that |

Codex picks up skill changes automatically; if a new skill or agent does not appear, restart Codex.

## Sources

Checked on 2026-09-24 against these pages and `codex --help` for codex-cli 0.153.3. Where a rule above is a caution rather than a documented fact, it says so.

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/automations?surface=app
- https://learn.chatgpt.com/docs/sandboxing
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/docs/cli/reference
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/models
