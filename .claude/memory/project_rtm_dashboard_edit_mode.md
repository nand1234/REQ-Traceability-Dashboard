---
name: rtm-dashboard-edit-mode
description: "Read-only / Edit switch and GIVEN/WHEN/THEN line display on the RTM dashboard (2026-10-14), how new artifacts inherit them via rtm-import templates, what is not synced, quirks found while testing"
metadata:
  type: project
---

The dashboard files (`RTMdashboard.html` and `RTMdashboard-artifact.html`) have a toolbar **Read-only | Edit** switch. Read-only (default, remembered per viewer in localStorage `rtm-mode`) hides every write control; Edit opens every req/TC edit form and every comment box at once. The per-row Edit buttons and comment Edit/Delete buttons are gone (clear a comment and Save to delete). When a shared Artifact is updated, build the new page from the latest live page's state plus the new script, so other people's comments, statuses and edits are kept.

- **Scenario display:** a test case description "Given … When … Then … Planned layer: …" (also "Given A, when B, then C" on one line, or on separate lines) renders as GIVEN / WHEN / THEN each on its own line, with "Planned layer…" as a muted line. Anything else stays a plain paragraph. Display only; stored data unchanged. Same code in both files.
- **New artifacts inherit it:** `rtm-import` has `templates/RTMdashboard.html` and `templates/RTMdashboard-artifact.html` (empty state, generic title) in `.claude/skills/rtm-import/templates/`. A new feature copies from them, not from whichever feature exists. To change the dashboard: edit and test in a feature, then copy over the templates and sync any second copy of the skill.
- **Not synced:** a feature created before the templates keeps its old dashboard files and old live artifact (no switch, no GIVEN/WHEN/THEN lines); an import never rewrites an existing feature's dashboard. Upgrade one on request: replace its dashboard files from the templates, merge its live state in, publish over the same url.
- **Pre-existing bug fixed in both files:** forms with the `hidden` attribute were always visible because their CSS sets `display:flex`; added `[hidden]{display:none!important}`. Before that, the local dashboard showed every add/edit/comment form permanently.
- **Live comments live only on the live page:** comments added on a live Artifact are not in `requirement.md` or the local `RTMdashboard-artifact.html`. Re-importing from the local file would drop them unless they are folded back first (see [[reference-rtm-artifact]]).
- **Artifact behaviour:** every save publishes and the page reloads, so unsaved text in other open forms is stashed in sessionStorage (`rtm-drafts`, 15 s) and restored after the reload. A viewer without write access is forced to Read-only and the Edit button is disabled; they can still view comments.
- **Not done:** the OQ question text and Related links cannot be edited (no `serve.py` endpoint for it). Testing was headless Playwright against a scratch copy with a mocked `window.claude`.

**Why:** the user asked for a mode where everything is editable and one read-only mode. **How to apply:** when touching these dashboards, keep `applyMode()` at the end of every re-render path, and keep the artifact variant in step with the local one by hand.
