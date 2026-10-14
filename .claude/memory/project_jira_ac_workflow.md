---
name: jira-ac-workflow
description: "How RTM test cases go into Jira tickets as AC blocks: the draft-before-write rule, the AC format, and tool gotchas"
metadata:
  type: project
---

Writing a feature's RTM test cases into the Jira tickets that own them (the `rtm-jira-ac` skill):

- **Rule:** show the draft and get the user's OK before editing any ticket. Right before writing, re-read the ticket and check `updated`; send the full description with only the AC block added; re-read after to verify. **Why:** a ticket had to be redone several times because the format was only settled after writing.
- **Format:** a few themed ACs per ticket (the example groups file turns 10 cases into 4), numbered AC-1.. per ticket. Each assertion is **GIVEN / WHEN / THEN on three separate lines** (bold caps, two trailing spaces). Then `###### Required Tests`, a line like `☑ Unit | ☐ Integration | ☐ Visual | ☐ E2E`, and `_Why: <one clause>_`. Insert before "Done when". No Required Tests block on CI/ops-only tickets. Keep a ticket's own existing ACs.
- **Gotchas:** the Atlassian tools take and return markdown only. A "Blocks" link also appears on the other ticket and these tools cannot remove it, so ask before adding one.
- **Skill:** `rtm-jira-ac` is in `.claude/skills/rtm-jira-ac/` (SKILL.md plus two scripts). A second copy elsewhere, if kept, follows the same two-place convention as [[rtm-import-skill-location]].
