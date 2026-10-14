# Shared Artifact — Multi-Currency Checkout

**Live link:** https://claude.ai/code/artifact/f50c0f01-fd0f-4da1-b8f5-a2cd1661e11f
**Artifact title:** Multi-Currency Checkout

This is the shareable, multi-editor version of the Multi-Currency Checkout
feature's RTM dashboard, published as a Claude Artifact. It's a separate
deliverable from the local `RTMdashboard.html` + `serve.py` (shared, at the
project root) + `requirement.md` setup in this folder — same feature set,
but no local server and no markdown file. All state lives inside the
published page itself; editing it publishes a new version of the whole
page, which live-reloads for everyone with the link.

Titled after this feature specifically (not a generic name) so it stays
distinguishable once other features have their own Artifacts too.

`RTMdashboard-artifact.html` in this folder is the source for what's
currently published — it's a snapshot, not auto-synced with
`requirement.md`. To push local changes to the live artifact, republish
that file (via the Artifact tool) using the link above as `url`.

## Features

- Same dashboard as the local tool: collapsible requirements, test cases
  tracked by **ticket number** (not pass/fail), open questions with
  Open/Answered toggling, two-column layout (requirements | open
  questions).
- **Add from the UI**: new requirements, new test cases (per requirement),
  new open questions (optionally linked to requirements) — no separate
  server needed, unlike the local version.
- **Shared editing**: any viewer with write access can edit; every edit
  publishes a new version that live-reloads for everyone else viewing it.
- **Read-only viewers** are detected automatically (on their first edit
  attempt, or immediately if the page can't write at all) and get a
  "View only" badge with edit controls disabled, instead of a confusing
  failure.
- **Conflict handling**: if two people edit at nearly the same time, the
  later publish wins and every view (including the one that lost) reloads
  to it — no error shown, since the reload delivers the correct state a
  moment later.
- **Read-only | Edit switch**: the page opens read-only; Edit opens every
  form and comment box at once. Test case scenarios show **GIVEN**, **WHEN**
  and **THEN** each on their own line. Requirements, test cases and open
  questions can be marked out of scope and can carry a comment.
- Light/dark theme (per-viewer preference, stored in that browser only —
  not part of the shared document).

## How `/rtm-import` uses this file

The `rtm-import` skill checks this file for the live link above before
deciding whether to update the existing artifact or publish a new one. If
you ever publish a new artifact for this project (rather than updating this
one), update the link above so the skill — and anyone else opening this
file — finds the current one.

_Published 2026-08-28. Retitled and moved into features/multi-currency-checkout/ 2026-08-28. Upgraded to the current dashboard templates 2026-10-14._
