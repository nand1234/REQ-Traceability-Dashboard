---
name: reference-rtm-artifact
description: Where to find the shared/editable Claude Artifact version of the RTM dashboard and its source-of-truth link file
metadata: 
  node_type: memory
  type: reference
  modified: 2026-08-28T09:56:07.059Z
---

The project is organized as one folder per feature/CP under `features/`,
each with its own `requirement.md`, `RTMdashboard.html`,
`RTMdashboard-artifact.html`, and `ARTIFACT.md`. `serve.py` and
`format.md` are shared and live at the project root (not per-feature).

Each feature has its own shared, multi-editor Claude Artifact, titled
after that specific feature (not a generic name) — the live link is
recorded in `features/<feature-name>/ARTIFACT.md`. Read that file for the
current URL rather than trusting any URL remembered here, since the
`/rtm-import` skill ([[rtm-import-skill-location]]) may republish it under
a new link if the old one becomes unreadable.

The first feature, "multi-currency-checkout"
(`features/multi-currency-checkout/`), is titled "Multi-Currency
Checkout" on its Artifact — live link in its `ARTIFACT.md`.

`RTMdashboard-artifact.html` inside each feature folder is the
template/snapshot used to create or rebuild that feature's Artifact — it
is NOT auto-synced with that feature's `requirement.md`; syncing between
them only happens when `/rtm-import` runs its Artifact-sync step.
