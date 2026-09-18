---
name: requirements-clarification-and-decision-capture
description: "Use when gathering user decisions in chat or a TUI."
version: 0.1.0
author: Hermes Curator
license: Proprietary
metadata:
  hermes:
    tags: [requirements, clarification, decisions, tui, collaboration]
---

# Requirements Clarification and Decision Capture

## When to use

Use when a task needs several business, architecture, workflow, policy or implementation decisions before action. Especially use this skill in terminal/TUI surfaces or whenever the user says interactive forms, buttons or question widgets are not visible.

## Primary rule

Prefer numbered plain-text questions in the normal assistant response for this user. The user explicitly reported that clarification forms were not visible and requested questions as response text. Do not rely on the `clarify` form as the only presentation of required questions in this workflow.

## Workflow

1. First give a short assessment and recommended approach so the questions have context.
2. Separate confirmed decisions from open decisions.
3. Ask all independent questions together as a numbered plain-text list.
4. Put the recommended answer first under each question and explain the trade-off in one or two sentences.
5. Give a compact reply template, for example: `1 yes; 2 option B; 3 ...`.
6. Do not ask the user to repeat stable policy already present in the profile.
7. When the user answers, restate the decisions in a compact decision table before planning or implementation.
8. If the user says “do not make changes yet,” limit work to read-only inspection and a design/plan artifact. Do not patch runtime contracts, skills or integrations as part of the design response.
9. Label assumptions and unresolved activation gates separately from business decisions.
10. When a later request authorises implementation, use the captured decisions rather than reopening settled questions.

## Form-tool boundary

The `clarify` tool may be used only when the active interface is known to render it for the user. If a form returns empty responses or the user says it is invisible:

- switch immediately to plain-text questions;
- do not interpret empty form responses as business decisions;
- do not report merely “operation interrupted” without reproducing the questions in text;
- keep using text for subsequent clarification in that workflow unless the user asks to try forms again.

## Question quality

Good questions change implementation or governance. Ask about:

- source order and fallback triggers;
- field ownership, merge precedence and conflict handling;
- scope limits and stop conditions;
- identity/selection criteria;
- external provider permissions and spend boundaries;
- write targets, approvals and read-back;
- acceptance evidence and rollout gates.

Avoid questions whose answer can be resolved from active contracts, live metadata or source documentation. Inspect those sources first.

## Decision recording

For a multi-decision design task, preserve:

- the exact user answer;
- the recommended interpretation;
- any implementation assumption needed to remove ambiguity;
- unresolved dependencies that block activation;
- an explicit statement of whether changes were or were not made.

Use a versioned plan or decision artifact for durable project decisions. Do not use memory for temporary task progress.

## Pitfalls

- Hiding required choices inside an invisible form.
- Asking one question per turn when questions are independent.
- Treating a recommendation as user approval.
- Converting “no count limit” into “no financial or safety boundary” without saying so.
- Applying implementation changes when the user requested planning only.
- Reasking questions already answered in the same conversation.

## Verification

Before finishing a clarification turn, check that:

- every required choice is visible as text;
- selectable alternatives are understandable without UI controls;
- the recommendation is clear but not presented as approved;
- no external action or profile mutation occurred unless authorised;
- the next user message can answer all questions concisely.

## Supporting material

See `references/plain-text-decision-pattern.md` for a reusable requirements-question template.
