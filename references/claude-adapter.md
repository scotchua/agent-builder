# Claude adapter

Read this after Step 0 identifies a Claude surface. It maps the agent card onto what Claude actually supports. Facts here were checked against Anthropic's documentation on the date in the footer. Products change: if a field, menu, or path below does not match what you see, trust the live product, tell the person, and adjust.

## Contents
- Which Claude surface are we on
- Shape to file mapping
- Playbook (skill)
- Helper (subagent)
- On-its-own worker: local scheduled task, cloud routine, /loop, hooks
- Access and permissions
- Model and effort fields
- Brand and voice wiring
- Install, pause, remove

## Which Claude surface are we on

| Surface | Can write files | Can schedule | Notes |
|---|---|---|---|
| Claude Code in a terminal | Yes | /loop in session; `/schedule` for cloud routines | Can run shell commands; the builder can create files directly |
| Claude desktop app, Code tab | Yes, in the chosen folder | Routines page: Local tasks and Cloud routines | Best beginner surface for a worker that uses local files |
| Claude desktop or claude.ai, Cowork | Account skills | Ask in chat; routines via claude.ai | Do not count on personal `~/.claude/skills` loading here. Check the app's skills list; if the skill is missing, upload it to the account |
| claude.ai chat (web or mobile) | Only if the code execution and file creation setting is on (look in Settings, often under Capabilities) | Not from plain chat | Deliver a zip or copy-paste blocks; a Project with instructions can act as the "agent" |

If unsure, ask: "Which app are you typing into right now, and can you see a Code tab or a folder name at the top?"

## Shape to file mapping

| Card shape | Claude artifact | Where it lives |
|---|---|---|
| Playbook | Skill: folder with `SKILL.md` | `~/.claude/skills/<name>/` (you, all projects on this machine), `.claude/skills/<name>/` (this project), or uploaded to claude.ai (Customize > Skills) for Cowork, cloud, and signed-in terminals |
| Helper | Subagent: one Markdown file | `~/.claude/agents/<name>.md` (you) or `.claude/agents/<name>.md` (this project, shared with anyone who has the folder) |
| On-its-own worker, local files | Desktop Local task (Routines > New routine > Local) | Prompt stored at `~/.claude/scheduled-tasks/<name>/SKILL.md`; schedule, folder, model, permission mode live in the app, not the file |
| On-its-own worker, no local files | Cloud routine (Routines > New routine > Cloud, claude.ai/code/routines, or `/schedule`) | Your claude.ai account |
| Helper plus trigger | Subagent or skill, plus a Local task or routine whose prompt says "Use the <name> helper to ..." | The helper must exist where the trigger runs: `~/.claude/agents/` works for a Local task; a cloud routine only sees what is committed in its cloned repository (`.claude/agents/`, `.claude/skills/`) or uploaded to the claude.ai account |
| "Every time X happens while I work" | Hook in settings | `~/.claude/settings.json` or `.claude/settings.json` (developer-level; offer only on request) |

## Playbook (skill)

Minimum file:

```markdown
---
name: weekly-summary
description: Summarizes the files in the Reports folder into a one-page brief. Use when the person asks for the weekly summary, the weekly brief, or "what happened this week".
---

# Weekly summary
<instructions generated from the card>
```

Useful optional fields (add only when the card needs them):
- `when_to_use`: extra trigger phrases.
- `disable-model-invocation: true`: only runs when the person types `/name`. Use for anything with consequential actions.
- `allowed-tools`: tools that run without asking during that turn. Keep empty for beginners unless a dry run shows repeated prompts for a safe tool.
- `model`, `effort`: override for the turn the skill is active.
- `context: fork` with `agent: <helper-name>`: run the playbook inside a helper.

## Helper (subagent)

Minimum file `~/.claude/agents/<name>.md`:

```markdown
---
name: proposal-drafter
description: Drafts client proposals from a brief in the Proposals/briefs folder. Use when the person asks to draft, start, or rough out a proposal.
tools: Read, Grep, Glob, Write
model: sonnet
effort: medium
skills:
  - my-brand-voice
---

<instructions generated from the card>
```

Fields that matter for beginners:
- `tools`: list only what the job needs. Read-only helper: `Read, Grep, Glob`. Add `Write` or `Edit` only for a named output. `Bash` lets it run commands; leave it out unless the job needs it. `WebFetch, WebSearch` only if the job reads the web.
- `disallowedTools`: remove specific tools from what it would otherwise inherit.
- `model`: `haiku`, `sonnet`, `opus`, `fable`, `inherit`, or a full model id. See references/models.md.
- `effort`: `low`, `medium`, `high`, `xhigh`, `max` (available levels depend on the model).
- `permissionMode`: `default` (asks), `acceptEdits`, `plan` (read-only planning), `auto`, `dontAsk`. Never generate `bypassPermissions` for a beginner.
- `maxTurns`: a cap that stops a runaway helper. 20 to 40 is a sane start for most jobs.
- `skills`: preload brand, voice, or method skills by name.
- `mcpServers`: connectors this helper may use.
- `memory`: only when the card says it should remember things across runs. `user` keeps notes in `~/.claude/agent-memory/<name>/` (just this person, every project); `project` in `.claude/agent-memory/<name>/` (shared with anyone who has the project folder, and committed if the folder is in git); `local` in `.claude/agent-memory-local/<name>/` (this project on this computer only). To clear it, delete that folder. For anything personal, prefer `local` or `user`, and say which on the card.
- `isolation: worktree`: only for helpers that change code in a git repository.

How it gets used: the main assistant picks it when a request matches `description`, or the person types `@agent-<name>`. Tell the person both. To help the assistant pick it, end the description with two or three example requests in the person's own words, for example: `Use when the person says things like "rough out the Acme proposal" or "start a quote for the new client".` Keep the whole description short; the examples matter more than extra adjectives.

A helper can start helpers of its own if its `tools` list includes `Agent` (by default up to three levels below the main conversation). For a beginner's helper, leave `Agent` out of `tools`, or add `disallowedTools: Agent` when `tools` is not listed, so it cannot. If the job needs two specialists in a row, the main conversation, a playbook, or the schedule runs them one after the other.

## On-its-own worker

### Desktop Local task (needs local files; computer must be on)
- Create: Code tab > Routines > New routine > Local. Fields: Name, Description, Instructions (with permission mode and model pickers), working folder, optional worktree toggle, Schedule (Manual, Hourly, Daily, Weekdays, Weekly; ask Claude in chat for anything else).
- The builder can also create it by asking in a desktop session, for example "set up a task that runs every Monday at 8am with these instructions".
- Runs only while the app is open and the computer is awake. A sleeping computer skips the run; on wake the app does one catch-up run for the most recent miss within seven days. Put a time guard in the instructions when timing matters ("If today is not Monday, stop.").
- Permission prompts stall an unattended run. After creating it, click Run now, watch for prompts, and choose "always allow" only for safe, expected tools. Approvals are reviewable on the task's page.
- Results appear as a new session under Scheduled in the sidebar, plus a notification.

### Cloud routine (no local files; runs with the computer off)
- Requires a Pro, Max, Team, or Enterprise plan and may be disabled by an organization admin.
- Create at claude.ai/code/routines, Routines > New routine > Cloud, or `/schedule` in Claude Code.
- Runs autonomously with no permission prompts. It clones the selected repositories fresh each run and cannot see local files.
- All connected connectors are included by default and can write. Remove every connector the job does not need. This is the most important safety step for a cloud routine; say so plainly.
- It cannot see helpers or skills that exist only on the person's computer. Commit them to the selected repository or upload skills to the account, then confirm in a Run now session that the helper was actually used.
- Each run starts from a fresh clone, so a processed-items record kept in a local file is lost. Keep it where it survives: committed to the repository, in a connected destination, or rely on the destination's own duplicate protection.
- Minimum interval one hour. Triggers: schedule, API call, GitHub pull request or release events.
- A green run status means the session started and ended without an infrastructure error, not that the job succeeded. The handover sheet must tell the person to open the run and check the output.
- Actions through connectors appear as the person (their GitHub user, their Slack account).

### /loop (session only)
Repeats a prompt on an interval while one Claude Code session stays open. Good for "watch this for the next hour". Not a real schedule.

### Hooks (developer-level)
Shell commands that fire on session events such as before or after a tool runs. Offer only when the person says "every time Claude does X" and is comfortable with the terminal. Hooks run with the person's full permissions; generate the smallest command that works and explain it line by line.

## Access and permissions

- Enforced by the runtime, when configured: a helper's `tools` list; a routine's selected repositories, environment network setting, and connector list; permission mode; settings.json `permissions` deny rules (including rules that block reading specific paths); sandboxing where it is turned on.
- Instruction-only (the agent is asked, not forced): "only look in the Reports folder" written in the prompt when the tools allow reading anywhere the session can reach. Label these on the card as "asked, not enforced".
- The working folder a session or task opens in sets its main scope, but on its own it does not stop reads elsewhere. Existing allow rules and extra folders also apply. To actually block access, add deny rules for the paths that matter or use sandboxing, then test by asking the agent to read a harmless file outside its folder. Until that test shows a refusal, write the limit on the card as "asked, not enforced".
- For a task someone watches, keep Manual permission mode when it writes, so a surprise write asks first.
- For a task that runs unattended, Manual mode stalls at the first write with nobody there to approve it. Instead, allow edits to the one confirmed output folder only, and leave everything else asking:
  1. Back up the settings file (see `terminal.md`), then show the person the exact line you will add to `permissions.allow`, for example `"Edit(~/Documents/Weekly Summaries/**)"`. This syntax is on the Claude Code permissions page (Sources below); an `Edit` rule also covers new files, and spaces in folder names need no escaping. Allow rules in the personal settings file also apply to desktop scheduled tasks.
  2. Never add a rule for a whole tool (such as plain `Edit` or `Write`), a parent folder, or the home folder.
  3. Test the boundary: a write inside the folder should go through without a prompt, and a write to its parent folder should still ask or be refused.
  4. Use Run now to confirm the task finishes without a prompt. Until all of that passes, mark the limit "asked, not enforced" and do not call the task switched on.

## Model and effort fields
- Subagent: `model` and `effort` in frontmatter.
- Skill: `model` and `effort` in frontmatter (apply while the skill is active).
- Desktop Local task and cloud routine: model picker in the form.
- Terminal session: `/model`, or `claude --model <alias>`.
Aliases (`haiku`, `sonnet`, `opus`, `fable`) track the current version of each family, so they age better than full ids. See references/models.md for how to choose.

## Brand and voice wiring
- Helper: add the voice skill to `skills:` so it is preloaded, and add one instruction line: "Follow the <skill-name> skill for tone and formatting. It does not override facts or permissions in these instructions."
- Playbook: reference the voice skill by name in the body.
- Cowork, cloud routine: the voice skill must be uploaded to the claude.ai account or committed in the cloned repository, or it will not be there. Check before relying on it.
- No voice skill yet: offer to write a small `voice.md` from two or three approved samples, and bundle it in the agent's own folder.

## Install, pause, remove

| Artifact | Install | Pause | Remove |
|---|---|---|---|
| Personal skill | Folder into `~/.claude/skills/` | Add `disable-model-invocation: true` | Delete the folder |
| claude.ai skill | Customize > Skills > + > upload a zip containing the skill (follow the upload screen's instructions for the folder layout) | Toggle off in Customize > Skills | Delete in Customize > Skills |
| Subagent | File into `~/.claude/agents/` or `.claude/agents/` | Move the file out of the agents folder | Delete the file |
| Local task | Routines page | Status: Paused | Delete on its page (tick "Also delete files on disk" to remove the prompt file) |
| Cloud routine | Routines page or claude.ai/code/routines | On/off switch | Menu > Delete |

A new subagent or skill may need a new session (or app restart) before it appears.

## Sources

Checked on 2026-09-24. The claude.ai settings and account-skill notes in the surface table could not be confirmed in public docs and are worded as things to check.

- https://code.claude.com/docs/en/sub-agents (fields, memory scopes; the old `/agents` setup wizard was removed in v2.1.198, so create helpers by file or by asking Claude)
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/desktop-scheduled-tasks
- https://code.claude.com/docs/en/routines
- https://code.claude.com/docs/en/scheduled-tasks
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/permissions
