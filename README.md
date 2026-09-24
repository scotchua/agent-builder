# agent-builder

A skill that walks a beginner through creating their own AI agent in Claude or Codex: picking the right kind of agent, writing its instructions, deciding what it can access, designing what starts it, choosing a model, and testing it before it runs on its own.

After installing, start with something like: "I want to build an agent that summarizes my inbox every Monday."

## Install

**Claude desktop app or claude.ai:** Customize > Skills > + > upload a zip of this folder (without this README), named `agent-builder.skill`. If the upload is refused or the skill cannot run, check that code execution and file creation are turned on in Settings (often under Capabilities).

**Claude Code:** copy this folder to `~/.claude/skills/agent-builder/`, then start a new session.

**Codex:** copy this folder to `~/.agents/skills/agent-builder/` (or `~/.codex/skills/agent-builder/` if that is where your other skills live), then start a new session. Invoke with `$agent-builder`.

## What is inside
- `SKILL.md`: the step-by-step flow.
- `references/`: runtime adapters for Claude and Codex, model and effort guidance, pushback rules, setup scan rules, instruction template, starter recipes, terminal rules, glossary, example card.
- `assets/agent-card.md`: the plan-and-save-file the skill fills in with you.
- `scripts/scan_setup.py`: optional read-only inventory of your existing skills, agents, schedules, and agent-related settings. It reports names, descriptions, headings, and a settings summary, never file bodies, keys, or environment values. `test_scan_setup.py` tests it.
- `scripts/validate_agent.py`: checks the skill, helper, or Codex agent files it creates (required fields, names, known settings, anything that looks like a password or key). The password and key check is best effort: it matches common patterns and will not catch every leak, for example a key in the middle of a JSON line with no `{` on that line. `test_validate_agent.py` tests it.
- `agents/openai.yaml`: the name and starter prompt Codex shows for this skill.
- `evals/evals.json`: test prompts for anyone evaluating the skill.

## Keeping it current
Product facts in the adapters were checked on the date at the bottom of each file. Claude and Codex change often; the skill tells the model to trust the live product over these files when they disagree.

## License
MIT. See `LICENSE`.
