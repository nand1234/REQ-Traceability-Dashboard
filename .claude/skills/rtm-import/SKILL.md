---
name: rtm-import
description: "Converts arbitrary requirement content — a PRD, spec doc, meeting notes, ticket export, or an existing/malformed requirement.md — into a requirement.md inside features/<name>/, formatted for the RTM dashboard (RTMdashboard.html + the shared serve.py), and syncs the result to that feature's shared Claude Artifact (updating it if features/<name>/ARTIFACT.md points to one, creating a fresh one titled after the feature otherwise). Use when the user wants to import, convert, generate, regenerate, or bootstrap a requirement.md, or set up requirement traceability for a new or existing feature/CP from source material."
---

# /rtm-import

## Usage

```
/rtm-import <feature-name> <path(s) to source doc(s)>
/rtm-import <path(s) to source doc(s)>          # ask which feature if it's ambiguous
/rtm-import                                     # ask what the source and feature are
```

## What this does

Takes whatever requirement-ish content the user points at and produces or
updates `features/<feature-name>/requirement.md`, in the exact convention
`RTMdashboard.html`'s parser expects, then syncs that feature's shared
Claude Artifact. This is a **format conversion**, not a content-generation
pass — stay faithful to the source; don't embellish or invent.

## Project layout this skill assumes

```
<project-root>/
├── serve.py            # shared local write-back server (takes a feature folder as an argument)
├── format.md           # shared format guide + blank skeleton — the format spec and the template for a new feature
└── features/
    └── <feature-name>/
        ├── requirement.md              # that feature's data
        ├── RTMdashboard.html            # local dashboard
        ├── RTMdashboard-artifact.html   # source for that feature's shared Artifact
        └── ARTIFACT.md                  # that feature's live Artifact link + summary
```

If the project root doesn't look like this yet (no `features/` directory),
ask before restructuring — don't assume every project using this skill has
already adopted the layout.

## Steps

1. **Identify the target feature folder.**
   - If the user named a feature (or one is obvious from the source, e.g.
     an existing CP title), use `features/<slugified-name>/`.
   - If `features/` has exactly one folder and nothing else suggests a
     different target, use it.
   - If ambiguous (multiple feature folders, or none and no clear name),
     ask.
   - **New feature** (the folder doesn't exist yet): create
     `features/<name>/`, copy `format.md` → `features/<name>/requirement.md`
     as the starting point, and copy `templates/RTMdashboard.html` (next to
     this SKILL.md — see "Dashboard templates" below) into the new one
     unchanged. Don't copy it from another feature: those keep whatever
     version they were created with.

2. **Find the authoritative format spec.** Read `format.md` at the project
   root — that's the live, current spec (it may have evolved since this
   skill was written).

3. **Identify the source.**
   - A file path (or several) the user gave — read them.
   - Pasted text in the request — use that.
   - Neither — ask what to read (a file path, a doc, or "paste it").

4. **Update `features/<name>/requirement.md`.**
   - If it already has real content (not just the `format.md` skeleton):
     **merge, don't blow away.** Read it fully first. Preserve every
     existing `Ticket:` value, every Open Question `Status: Answered`,
     every `Scope: Out of Scope` marker, and every `Comment:` note — these
     represent real work (linked tickets, resolved questions, scope
     decisions, review notes) that the source doc won't know about. Only add new
     requirements/test cases/questions, or update descriptions for things
     that clearly changed in the source. If the user explicitly asks for a
     from-scratch regenerate, confirm before discarding existing
     ticket/status data.
   - Continue ID numbering after whatever's already in the file — never
     reuse or renumber existing `REQ-`/`TC-`/`OQ-` IDs.

5. **Extract structure from the source.**
   - **Requirements** — distinct capabilities/behaviors the feature must
     deliver. One `### REQ-<id>: <Title>` each.
   - **Priority / Status** — infer only if the source actually signals it
     (e.g. "must have" → High, "nice to have" → Low, "P1" → High). Leave
     blank rather than guess.
   - **Description** — the requirement's own prose, tightened. Don't pad
     it with boilerplate.
   - **Test cases** — pull from explicit acceptance criteria / test plans
     in the source. If the source has none, derive a small number of
     high-level, black-box test cases per requirement that would plausibly
     verify it — behavioral, not implementation detail. Always leave
     `Ticket:` blank; never invent a ticket number.
   - **Open Questions** — things the source raises but doesn't resolve:
     ambiguity, explicit TODO/TBD markers, contradictions, missing
     acceptance criteria, "to be decided" notes. Ground every open question
     in an actual gap you can point to in the source — don't manufacture
     questions to pad the section.

6. **Write `features/<name>/requirement.md`** following the format spec
   exactly (`format.md`). Its own header comment should just point back to
   `../../format.md` (see any existing feature's file for the wording) —
   don't duplicate the whole guide into every feature's file.

7. **Sync to that feature's shared Artifact** (see "Syncing to the shared
   Artifact" below) — do this after `requirement.md` is finalized, using
   its now-current content as the basis.

8. **Report a short summary**: which feature folder, counts of
   requirements/test cases/open questions written or updated, plus
   anything from the source you weren't confident enough to place — call
   those out explicitly instead of silently dropping them. Include
   whether the Artifact was updated or newly created, its title, and its
   link.

## Syncing to the shared Artifact

`features/<name>/requirement.md` and that feature's shared Claude Artifact
are two independent snapshots of the same data — the Artifact isn't
auto-synced, so bring it up to date explicitly after updating
`requirement.md`.

1. **Find the existing Artifact, if any.** Look for
   `features/<name>/ARTIFACT.md` and read the "Live link" URL from it.

2. **If a link exists:**
   - `Artifact` tool, `action: "read"`, that `url` — this returns the
     Artifact's raw HTML (you own it). If the read fails (deleted,
     inaccessible), treat this the same as "no link exists" (step 3).
   - Extract the JSON from its `<script id="rtm-state" type="application/json">`
     tag — this is the Artifact's current state (requirements, test cases,
     open questions), independent of whatever's in `requirement.md`.
   - Parse the now-current `requirement.md` into the same shape (title,
     meta, requirements with test cases, open questions) — same fields as
     the Artifact's state.
   - **Merge the two, in both directions — never destroy either side's
     data:**
     - Anything in `requirement.md` but not yet in the Artifact's state
       (new/updated requirements, test cases, open questions from this
       import) → add/update in the merged state.
     - Anything in the Artifact's state but not in `requirement.md` (items
       added or edited directly on the live page since they last
       diverged — tickets, Answered statuses, whole items) → keep them,
       AND fold them back into `requirement.md` too, so the two files stop
       drifting apart. Mention this in your summary.
     - If the same ID (`REQ-`/`TC-`/`OQ-`) refers to clearly different
       content on each side, don't silently pick one — renumber the newer
       one to a fresh ID, or ask the user if you can't tell which is
       authoritative.
     - Carry each item's `outOfScope` flag (the `Scope: Out of Scope`
       marker — see `format.md`) through the merge exactly like `Ticket:`
       and `Status:` — it's real state set from the dashboard UI, not
       something the source doc will know about. Never let it default
       back to `false` for an item that already exists on either side.
     - Carry each item's `comment` field the same way — it's a note added
       from the dashboard UI (or hand-written as a `Comment:` line), not
       content the source doc will ever supply. Never let a re-import
       clear an existing comment, and never fabricate one from source
       wording.
   - Take the Artifact's current raw HTML, replace only the contents of
     its `<script id="rtm-state" type="application/json">` tag with the
     merged state (JSON-stringified, every `<` escaped as `<` so a
     `</script>` can never appear inside the payload) — leave everything
     else (styles, the `<script id="app-script">` tag, the `<title>` tag,
     structure) byte-for-byte unchanged. Write this to a local file and
     publish it with the `Artifact` tool passing this same `url` (updates
     the existing Artifact in place — same link, new version). Before
     publishing, do a fresh `action: "read"` of that same `url` in this
     turn if you haven't already — a publish built on a stale read is
     rejected.

3. **If no link exists (missing `ARTIFACT.md`, no link in it, or the read
   in step 2 failed):**
   - Take `RTMdashboard-artifact.html` from `features/<name>/` if it
     exists there already; otherwise copy `templates/RTMdashboard-artifact.html`
     (next to this SKILL.md — see "Dashboard templates" below) to
     `features/<name>/RTMdashboard-artifact.html`. Everything except the
     embedded state and the two `<title>` tags is feature-agnostic.
   - In that file, set BOTH `<title>` occurrences (the one at the top of
     the file, and the one inside the `buildDocument()` function's
     returned string) to the feature's own name — e.g. "Multi-Currency
     Checkout", not a generic "Traceability Matrix". This is what keeps
     multiple features' Artifacts distinguishable in a gallery; do this
     even when the file came from the template.
   - Replace the `<script id="rtm-state" type="application/json">`
     payload with the state parsed from the now-current `requirement.md`
     (same JSON shape, `<` escaped as above).
   - Publish it fresh with the `Artifact` tool (no `url` — this creates a
     new Artifact): `title` = the feature's name (not "Traceability
     Matrix"), a one-sentence `description` naming the feature, `favicon`
     🧭 (keep this emoji consistent across every feature's Artifact — it's
     the family marker; the title is what distinguishes them), 
     `capabilities: {"artifact": {}}`.
   - Write (or create) `features/<name>/ARTIFACT.md` with the resulting
     link and the feature's Artifact title — see any existing feature's
     `ARTIFACT.md` for the shape (a "Live link" line, the Artifact title,
     a feature summary, and a note that `/rtm-import` uses this file to
     find the Artifact next time).

## Dashboard templates

`templates/` (next to this SKILL.md) holds the two dashboard files every
**new** feature starts from:

- `templates/RTMdashboard.html` — the local dashboard.
- `templates/RTMdashboard-artifact.html` — the source of the shared Artifact,
  with an empty `rtm-state` (`{"title":"Traceability Matrix","meta":{},"requirements":[],"openQuestions":[]}`)
  and the generic title "Traceability Matrix" in both `<title>` places.

They carry the current dashboard behaviour: the **Read-only | Edit** switch
(Read-only by default; Edit opens every form and comment box at once) and
test case scenarios shown with **GIVEN**, **WHEN** and **THEN** each on
their own line. A new feature gets both because it starts from these files,
not from whichever feature happens to exist.

An import never rewrites an existing feature's dashboard files (see the
non-negotiables), so existing features keep the version they were created
with. To bring one up to date, replace its dashboard files from the
templates on request, merge its live Artifact's state into the new
Artifact file, and publish that over the same `url`.

**Changing the dashboard:** edit and test it in a feature's files, then
copy it over the templates (for the Artifact one: set both `<title>`s to
"Traceability Matrix" and the `rtm-state` payload to the empty state above).
If you keep a second copy of this skill elsewhere (for example in a shared
skills repo), keep the two in step by hand: after editing either copy,
`cp -r` the whole folder over the other and check with `diff -r`.

## Non-negotiables

- Never fabricate ticket numbers, priorities, or statuses not present in
  the source.
- Never delete or overwrite an existing `Ticket:` value, `Status:
  Answered` open question, `Scope: Out of Scope` marker, or `Comment:`
  note during a merge. Never fabricate a `Scope: Out of Scope` marker or a
  `Comment:` note either — only carry one forward from an existing side,
  never infer either from source wording (e.g. "deferred", "out of
  scope") without the user having actually set it.
- Stay faithful to source wording in descriptions — conversion, not rewrite.
- If the source is too thin to produce a requirement with any confidence,
  leave it out and mention it in the summary rather than inventing content.
- Never overwrite the Artifact's state wholesale from `requirement.md` (or
  vice versa) — always merge; edits made directly on the live page are as
  real as edits made to the file.
- Never touch the Artifact's `<style>`/`<script id="app-script">` content
  when updating it — only the embedded state (and, when creating fresh,
  the `<title>` tag) changes.
- Never give two different features' Artifacts the same title — each
  Artifact's `<title>` must name the specific feature it tracks.
