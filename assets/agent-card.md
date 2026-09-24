# Agent card: <name>

Status: <draft | prototype | configured | tested on sample | first scheduled run pending | verified>
Built for: <surface, for example "Claude desktop, Code tab" or "Codex CLI">
Last updated: <date>

## The short version
- **Job:** <one sentence, a result not an activity>
- **Example:** <one real or invented input, and what a good result looks like>
- **Done means:** <two to four checks a person could verify by looking>
- **Result goes to:** <chat, a named file or folder, a draft message>
- **It can use:** <folders it reads, folders it writes, connectors or tools>
- **Needs your approval before:** <sending, deleting, publishing, paying, overwriting; or "nothing, it only drafts">
- **Remembers between runs:** <nothing | what, where (just you / everyone with the project / this computer only), how to clear it>
- **Asked, not enforced:** <limits that are only in the instructions; or "none">
- **Brand or voice:** <skill or file used, or none>
- **How it starts:** <you ask for it by name | the assistant picks it when you ask for X | on a schedule | when an event happens>
- **Model:** <profile (setting), effort, one-line reason; or "uses your current model">
- **Rough cost (recurring or consequential agents):** <how often it runs, model profile and effort, where to watch usage; an estimate>
- **Assumed / switched off:** <reversible defaults the builder picked; any action left disabled and why>

## Running on its own (scheduled or event-driven agents only)
- **Schedule or event:** <when, time zone>
- **Runs where:** <this computer (must be on, app open) | cloud (sees only connected sources)>
- **If the computer is asleep or the app is closed:** <what happens>
- **Already-done check:** <stable identifier per item, and where the record is kept so it survives between runs>
- **Stop limits:** <most items per run, retries per item, longest run time; what it reports when a limit is hit>
- **If it fails:** <where the failure shows up so you will see it>
- **Readiness:** <each dependency, how it was confirmed in this runner, what happens if missing>
- **Owner:** <optional: who looks after it>

## Tests
| Case | Input | Expected | Result |
|---|---|---|---|
| Normal | | | |
| Boundary | | | |
| Planted instruction (if it reads outside content) | | Ignores it, mentions it | |
| Without instructions (recurring or consequential) | | Worse than with them | |

## Files
- <path>: <what it is>

## First use
- Say or click: <exact words or clicks>
- You should get: <what comes back>
- To adjust it: <one thing to edit>

## How to pause, change, remove
- Pause: <exact steps>
- Change: <edit which file or form; start a new session afterwards>
- Remove: <exact steps>

## Level 2 (optional next upgrades)
- <one or two upgrades that fit this agent, each with one benefit and one boundary>
