<!--
  REQUIREMENT TRACEABILITY MATRIX — FORMAT GUIDE
  ================================================
  This is the shared template for starting a new CP/feature. Copy this
  file to features/<feature-name>/requirement.md and replace the
  placeholder content below — keep the markers exactly as shown (the
  headings, the "#### Test Cases" marker, the "## Open Questions"
  heading); free text (titles, descriptions, questions) can be anything.

  RTMdashboard.html parses this file live in the browser — save it and
  refresh the page. No build step.

  # <CP Title>                                    -> H1, becomes the dashboard title (once, first line of content)
  > Field: value | Field: value                   -> optional metadata line right after the H1

  ## Requirements                                 -> section divider (cosmetic, optional)

  ### REQ-<id>: <Title>                           -> one collapsible section per requirement
  > Priority: High|Medium|Low | Status: <text>    -> optional metadata line right after the REQ header
  <description paragraph(s)>                      -> plain text, shown as the requirement body

  #### Test Cases                                 -> starts this requirement's test case list
  - TC-<id>: <Title> — Ticket: <ticket-no, or leave blank if not yet covered>
    <optional indented line>                      -> test case description (indent by 2+ spaces)

  ## Open Questions                               -> starts the open-questions section (once)
  - OQ-<id> (Related: REQ-<id>, REQ-<id>): <question text> — Status: Open|Answered

  IDs are global and sequential within their own prefix (TC-001, TC-002,
  ... across the whole file, not reset per requirement). Status values are
  case-insensitive. The dash before "Status:"/"Ticket:" can be a hyphen
  (-), en dash (–), or em dash (—).

  OUT OF SCOPE MARKING
  ---------------------
  Any REQ, TC, or OQ can be flagged "out of scope" — deferred/descoped but
  kept in the file (not deleted) so it can be pulled back in later. It's
  an orthogonal field, not a Priority/Status value: an item keeps its own
  Status (Draft/Approved, Open/Answered) independent of its Scope, and the
  dashboard hides out-of-scope items from the coverage stats while still
  listing them (dimmed, with a "Out of scope" badge) so nothing silently
  disappears. Omit the field entirely for in-scope items — that's the
  default; only write it when marking something out of scope.

  REQ: append to the same metadata line as Priority/Status —
    > Priority: High | Status: Draft | Scope: Out of Scope

  TC: append after Ticket, using the same dash convention —
    - TC-<id>: <Title> — Ticket: <ticket-no> — Scope: Out of Scope

  OQ: append after Status —
    - OQ-<id> (Related: REQ-<id>): <question text> — Status: Open — Scope: Out of Scope

  The dashboard's "Mark out of scope" / "Restore" controls write this
  field back in place — hand-editing works too, using the same syntax.

  COMMENTS
  ---------
  Any REQ, TC, or OQ can carry one free-text comment — a note, not a
  second description. It's a SEPARATE LINE, never appended to the
  Priority/Ticket/Status line — comments are open-ended text and are
  likely to contain "|" or "—" themselves, which would break those
  pipe/dash-delimited lines. Single line only (no blank-line paragraphs);
  the dashboard flattens newlines on save. Omit entirely when there's no
  comment — that's the default.

  REQ: its own blockquote line, directly after the Priority/Status line —
    > Priority: High | Status: Draft
    > Comment: <free text>

  TC: an indented line under the entry, alongside (before or after) the
  description line —
    - TC-<id>: <Title> — Ticket: <ticket-no>
      <description>
      Comment: <free text>

  OQ: an indented line under the entry (OQ lines don't otherwise have
  continuation lines) —
    - OQ-<id>: <question text> — Status: Open
      Comment: <free text>

  The dashboard's "Add comment" / "Edit" controls write this back in
  place — hand-editing works too, using the same syntax.
-->

# CP-<id>: <Feature title>

> Owner: <name> | Date: <YYYY-MM-DD> | Status: Draft

## Requirements

### REQ-001: <First requirement title>
> Priority: <High|Medium|Low> | Status: <Draft|Approved>

<What this requirement covers, in a sentence or two.>

#### Test Cases
- TC-001: <Test case title> — Ticket:
  <What this test verifies.>

## Open Questions

- OQ-001: <A question this feature raises but doesn't yet answer.> — Status: Open
