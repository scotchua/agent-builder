# Choosing a model and effort

Model names change every few months. This file recommends a capability profile and an effort level from what the job demands, then maps them to whatever the person's app offers today. Record all three on the card: the profile, the exact setting chosen, and a one-line reason. When names change, the profile and reason let anyone remap it.

## When to recommend at all

- On-demand helper or playbook: inherit the person's current model unless a trait below clearly calls for a change. Say "It will use whatever model you have selected. That is fine for this job because ..."
- Recurring, high-volume, or unattended agent: always give an explicit recommendation with a reason. An unattended job that silently inherits the strongest model at high effort multiplies cost every run; one that inherits a small model can fail a judgment call with nobody watching.

## Step 1: score the job

| Trait | Low | High |
|---|---|---|
| Judgment: does it weigh trade-offs or decide what matters? | Follows fixed rules | Weighs, prioritizes, or writes persuasively |
| Ambiguity of input | Clean, same shape every time | Messy, varied, incomplete |
| Steps and tools | One or two steps | Many steps, several tools, has to plan |
| Cost of a mistake | Easy to spot and fix | Reaches other people, money, or records |
| Volume and frequency | Occasional | Many items or many runs |

## Step 2: pick the profile

| Profile | Use when | Typical jobs |
|---|---|---|
| Fast | Low judgment, low ambiguity, high volume | Sorting, tagging, renaming, pulling fields out of tidy documents, formatting |
| Balanced (default) | Most jobs | Summaries, drafts from a clear brief, checklists, routine reviews |
| Strongest | High judgment or a costly mistake, and a test shows the balanced profile falls short | Nuanced writing in a voice, complex reviews, multi-step planning, anything a professional would sign |

Volume pulls toward Fast; cost of a mistake pulls toward Strongest. When they conflict, split the job: a fast helper does the bulk sorting, and only the flagged items go to a stronger one.

## Step 3: pick the effort

| Effort | Use when |
|---|---|
| Low | Mechanical work with an obvious right answer |
| Medium (default) | Normal work with a few decisions |
| High | Multi-step reasoning, ambiguous input, careful review |
| Extra-high or max | Only with a specific reason, such as a review that measurably misses problems at high. Say the reason on the card |

More effort means slower and costlier runs, and it does not fix missing information. If output is poor, first check the instructions and inputs, then raise effort one level, then try a stronger model.

## Step 4: map to what is available today

Read the model list from the person's app (model picker, `/model`, or the settings form) rather than from memory. Then map:

- Claude (as checked 2026-09-24): aliases `haiku` (fast), `sonnet` (balanced), `opus` (strongest). Other families may appear in the picker, such as `fable`; read the picker's own description before mapping one. Aliases follow the latest version of each family, so prefer them over full model ids unless the person needs a pinned version. Effort values: `low`, `medium`, `high`, `xhigh`, `max`, depending on the model.
- Codex: read the current list from `/model` or the app. Map the smallest listed general model to Fast, the default to Balanced, and the top model to Strongest. Effort values for `model_reasoning_effort`: `low`, `medium`, `high`, `xhigh`, with `ultra` or `max` on some models. Set model and effort together.
- Not every effort level exists on every model. If the app rejects a pairing, step down one level and note it.

## Step 5: check with the dry run

The recommendation is a starting point. If the dry run output is good, keep it. For a recurring job, try one profile lower on the same test cases; if it still passes all of them, use the cheaper one and say so. If it fails, stay or step up, and record which test decided it.

## Card entry format

```
Model: Balanced (sonnet), effort medium
Why: drafts from a clear brief; mistakes are caught when you review the draft.
Tested: passed 2 of 2 sample briefs on 2026-09-24.
```
