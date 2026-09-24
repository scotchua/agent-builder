# Example: a filled card (illustrative)

This shows the target density for a simple helper. The person supplied three sentences and one sample; the builder filled everything else.

~~~
# Agent card: proposal-drafter

Status: tested on sample
Built for: Claude desktop, Code tab
Last updated: 2026-09-24

## The short version
- Job: Turn a one-page client brief into a first-draft proposal in my voice.
- Example: brief for a two-month website refresh -> 2-page proposal with scope, timeline, and [NEEDS: fee].
- Result goes to: Proposals/drafts/<client>-draft.md
- It can use: reads Proposals/briefs; writes Proposals/drafts; voice skill "my-voice"
- How it starts: the assistant picks it when I ask to draft a proposal, or I type @agent-proposal-drafter
- Model: uses your current model (fine for on-demand drafting you review)

## Tests
| Case | Input | Expected | Result |
|---|---|---|---|
| Normal | sample-brief.md | 2 pages, my voice, fee marked NEEDS | pass |
| Boundary | brief with no dates | timeline marked NEEDS, nothing invented | pass |

## Files
- ~/.claude/agents/proposal-drafter.md: the helper

## First use
Say: "Draft a proposal from Proposals/briefs/sample-brief.md."
You should get: a draft in Proposals/drafts with the fee marked [NEEDS: fee].
To change its tone: edit the my-voice skill, not this helper.

## How to pause, change, remove
- Pause: move the file out of ~/.claude/agents
- Change: edit the file, then start a new session
- Remove: delete the file

## Level 2
- A price list file it can read, so fees fill in instead of NEEDS. Boundary: it will quote whatever the file says.
~~~
