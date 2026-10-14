---
name: rtm-jira-ac
description: "Writes a feature's RTM test cases (features/<name>/requirement.md) into the descriptions of the Jira tickets that own them, as a few themed acceptance criteria — each assertion with GIVEN / WHEN / THEN on separate lines — plus a Required Tests block (Unit | Integration | Visual | E2E checkboxes and a one-clause Why). Reads each ticket first, drafts and shows the block for approval, checks the ticket is unchanged, writes only the new block, and re-reads to verify. Can also draft a new ticket (for example a go-live E2E ticket) under the same epic. Use when the user wants to add test cases, acceptance criteria or Required Tests to a Jira ticket, push RTM data to Jira, or create a test ticket from RTM cases."
---

# /rtm-jira-ac

## Usage

```
/rtm-jira-ac <feature-name>                    # every ticket named in that feature's RTM
/rtm-jira-ac <feature-name> PROJ-1234 PROJ-5678  # only these tickets
/rtm-jira-ac <feature-name> new <case ids>     # draft a NEW ticket from cases (e.g. the E2E ones)
```

## What this does

Takes the test cases already in `features/<name>/requirement.md` and writes them into the Jira
tickets that own them (the `Ticket:` field). It is a **format conversion**: the Given/When/Then
text comes from the RTM, it is not invented. The only judgement calls are the grouping, the
Required Tests ticks and the Why lines, and the user approves those before anything is written.

Jira is shared with colleagues, so this skill follows a strict **read, draft, approve, write,
verify** loop on every ticket.

## Files

```
scripts/parse_rtm.js     parses requirement.md with the dashboard's own parser -> JSON
scripts/gen_jira_ac.py   `list` (cases of a ticket) and `build` (markdown block from a groups file)
examples/groups-example.json   a model of the groups file (10 cases -> 4 ACs, one override); the
                               schema, not data that builds against a real RTM
```

Work in a scratch directory for the state/groups/block files, never inside `features/`.

## Steps

1. **Parse the RTM.** `node .claude/skills/rtm-jira-ac/scripts/parse_rtm.js features/<name> <scratch>/state.json`.
   Pick the tickets: the distinct Jira keys in the cases' `Ticket:` values (a value can hold
   several keys, and `(partial)` marks half-covered cases). Report cases with **no ticket**: they
   cannot go into any ticket, say so and stop there for those.

2. **Per ticket, one at a time** (unless the user asks for a batch):
   1. `python3 .claude/skills/rtm-jira-ac/scripts/gen_jira_ac.py list --state <state> --ticket PROJ-x`
      lists the cases, their co-owners, planned layers, and which are not Given/When/Then.
   2. Load the Atlassian tools with ToolSearch if they are deferred, get the cloud id with
      `getAccessibleAtlassianResources`, then `getJiraIssue` (fields summary, description,
      updated; `responseContentFormat: markdown`). **Note `updated`.** Read the whole
      description: its sections decide where the block goes (see Placement).
   3. **Propose the grouping** (see Grouping) and write a groups file (schema in the header of
      `gen_jira_ac.py`; `examples/groups-example.json` is a model).
   4. `gen_jira_ac.py build --state <state> --ticket PROJ-x --groups <groups> --out <block.md>`
      (it refuses if the groups do not cover exactly the ticket's cases). Fix any WARNING it
      prints about leftover dashboard-only references with an `overrides` entry.
   5. **Show the draft and wait for a go-ahead.** `AskUserQuestion` with the block in the
      option `preview` works well. Mention anything unusual (a shared case, a partial case, a
      reworded bullet, an inferred tick). If the user says "change it first", ask what to change
      if they did not say, and show the new draft.
   6. **Write.** Re-fetch `updated`; if it moved, someone edited the ticket: re-read and merge,
      do not overwrite. Then `editJiraIssue` with `contentFormat: markdown` and the **full
      description**, identical to what you read except for the new block. Copy nested lists and
      their whitespace-only lines exactly.
   7. **Verify.** The edit response returns the stored description: confirm the block is there
      and the rest is unchanged (compare section by section). Report the ticket link.

3. **Final report:** a table of tickets (ACs written, assertions), anything skipped, and
   anything the user still has to decide.

## The format

```
**AC-1 Theme title**

**GIVEN** a customer whose browser locale is de-DE  
**WHEN** the checkout page loads  
**THEN** all prices show in EUR at the current daily rate.

**GIVEN** ...  
**WHEN** ...  
**THEN** ...

###### Required Tests
☑ Unit | ☑ Integration | ☐ Visual | ☐ E2E  
_Why: Unit covers the rate conversion; integration shows the rendered prices on first load._
```

- GIVEN, WHEN and THEN each on **their own line** (bold caps; two trailing spaces make the
  line break; THEN ends with a full stop). One three-line block per assertion, blank line
  between assertions.
- ACs are numbered **AC-1, AC-2... per ticket**, not with the RTM's TC ids.
- No heading or intro paragraph around the ACs.
- Jira stores a blank line after `###### Required Tests`; that is fine.

## Grouping

- Group the ticket's cases into **a few themed ACs** (about 2 to 5; the 10 cases in
  `examples/groups-example.json` became 4), not one AC per case. Group by what the ticket's own Scope and "Done when" describe.
- Each assertion stays one case's Given/When/Then, wording kept. Strip dashboard-only
  references (open-question ids, "POC bug n"); the script does the common ones.
- Include **co-owned** cases in every ticket that owns them.
- **Partial** cases: write only the half this ticket owns (an `overrides` entry) and note the
  uncovered half in the bullet, so the ticket does not claim what it does not own.
- Never add assertions the RTM does not have. If the RTM has no cases for a ticket, ask the
  user before drafting anything from the ticket text alone.
- A ticket that already has its own Acceptance Criteria: keep its wording. Number and format them in place, never replace them with RTM cases that are
  outside that ticket's scope. If it is already in this format, leave it alone.

## Required Tests

Ticks are the **union of the group's planned layers** in the RTM:

| RTM layer | Box |
| --- | --- |
| unit | Unit |
| SSR integration, integration | Integration |
| visual, axe | Visual |
| E2E | E2E |
| manual, scripted check, build check, CI self-test | none: say it in the Why line |

- Why is **one short clause** saying why those layers fit, grounded in the ticket's own
  "By level" table. Mark any tick you inferred rather than read, so the user can confirm.
- **CI-check and ops-only tickets** (CI gates, scheduled jobs, scripted post-deploy checks):
  the user's rule is **no Required Tests block**, only the ACs (`"required_tests": false`).
- E2E is ticked only when the RTM plans E2E (or the ticket is an E2E ticket).

## Placement

Insert the block **just before the `## Done when` section**. If there is none, put it before
the final notes / blocked-by sections. If the ticket has a test-checks table, it goes after
it. Everything else in the description stays byte for byte.

## Non-negotiables

- **Draft first, write after an explicit go-ahead.** One ticket at a time unless told otherwise.
  Re-check `updated` immediately before every write.
- Never touch anything outside the AC block. Never reword the ticket's own text.
- Never invent test cases, ticket keys, or links. Adding a "Blocks" link changes the *other*
  ticket too and these tools cannot remove it: ask first.
- The Atlassian tools return and accept **markdown only** (ADF requests come back as markdown).
- Do not mark anything out of scope or add comments in the RTM as part of this.

## Creating a new ticket (for example the go-live E2E ticket)

1. Pick the cases (`new <case ids>`); `build` without `--ticket`. Typical: ACs with E2E ticked.
2. Draft the whole description in the house layout (Objective, Scope, the ACs, Done when,
   Blocked by, Notes) and show it. Copy the structure of a sibling ticket.
3. On approval, look at a sibling first (`getJiraIssue` with parent, components, labels,
   issuelinks) so the new one matches: same parent epic (the epic key goes in `parent`),
   component, and any label your team puts on AI-drafted tickets.
4. `createJiraIssue`, then re-read it to confirm parent, component and label applied.
5. Offer (do not assume) the "is blocked by" links and recording the new key on those cases in
   the RTM (`requirement.md` and, via `/rtm-import`'s sync rules, the shared Artifact, folding
   back any edits made on the live page).

## After writing

The RTM keeps its own TC/OQ ids; the Jira ACs use AC-1... per ticket, so the mapping lives
only in this conversation. If the user wants it kept, add the Jira numbers to the case
descriptions in `requirement.md`.

## Where this skill lives

The project-local copy in `.claude/skills/rtm-jira-ac/` is the one that triggers while working
here. If you keep a second copy elsewhere (for example in a shared skills repo), keep the two in
step by hand: after editing one, `cp -r` it over the other and verify with `diff -r`.
