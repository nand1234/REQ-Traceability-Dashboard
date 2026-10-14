---
name: rtm-import-skill-location
description: The rtm-import skill may exist in two locations that must be kept in sync by hand
metadata:
  type: reference
---

The `rtm-import` skill (converts arbitrary requirement docs into
`requirement.md` for the RTM dashboard, and syncs the result to the shared
Claude Artifact — see [[reference-rtm-artifact]]) lives in this project's
`.claude/skills/rtm-import/`, so it triggers automatically while working here.
The user may keep a second copy elsewhere, for example in a shared skills repo.

There is no symlink or build step keeping the copies identical — when editing
the skill, edit one and `cp -r` the whole folder over the other (whichever
direction), and verify with `diff -r` before moving on.
