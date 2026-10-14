#!/usr/bin/env python3
"""Local dev server for the RTM dashboard.

Shared across all features — lives at the project root, not inside any
one feature folder. Serves a feature folder (RTMdashboard.html,
requirement.md) like a normal static server, plus write endpoints that
edit that folder's requirement.md in place:

  POST /save-ticket     {"id": "TC-001", "ticket": "PROJ-123"}
  POST /save-oq-status  {"id": "OQ-001", "status": "Answered"}
  POST /save-scope      {"type": "req"|"tc"|"oq", "id": "REQ-001", "outOfScope": true}
  POST /save-comment    {"type": "req"|"tc"|"oq", "id": "REQ-001", "comment": "..."}
  POST /add-oq          {"text": "...", "related": ["REQ-001"]}
  POST /add-requirement {"title": "...", "priority": "High", "status": "...", "description": "..."}
  POST /add-testcase    {"reqId": "REQ-001", "title": "...", "ticket": "...", "description": "..."}
  POST /edit-requirement {"id": "REQ-001", "title": "...", "priority": "High", "status": "...", "description": "..."}
  POST /edit-testcase    {"id": "TC-001", "title": "...", "description": "..."}

Usage:
  python3 serve.py [feature-folder] [port]

  feature-folder  Path to a features/<name> folder (contains RTMdashboard.html
                   and requirement.md). Defaults to the current directory —
                   so running this from inside a feature folder also works.
  port            Defaults to 8000.
  Order doesn't matter between the two; a plain number is always read as
  the port.

Examples:
  python3 serve.py features/multi-currency-checkout 8000
  cd features/multi-currency-checkout && python3 ../../serve.py 8000
"""
import http.server
import json
import os
import re
import sys

_args = sys.argv[1:]
PORT = 8000
FEATURE_DIR = None
for _a in _args:
    if _a.isdigit():
        PORT = int(_a)
    else:
        FEATURE_DIR = os.path.abspath(_a)
if FEATURE_DIR is None:
    FEATURE_DIR = os.getcwd()

ROOT = FEATURE_DIR
MD_PATH = os.path.join(ROOT, 'requirement.md')

TC_ID_RE = re.compile(r'^TC-[\w.-]+$')
OQ_ID_RE = re.compile(r'^OQ-[\w.-]+$')
REQ_ID_RE = re.compile(r'^REQ-[\w.-]+$')
TC_LINE_START_RE = re.compile(r'^-\s+(TC-[\w.-]+)\b', re.IGNORECASE)
OQ_LINE_START_RE = re.compile(r'^-\s+(OQ-[\w.-]+)\b', re.IGNORECASE)
REQ_HEADER_RE = re.compile(r'^###\s+(REQ-[\w.-]+)\s*:', re.IGNORECASE)
TC_MARKER_RE = re.compile(r'^####\s+Test Cases\s*$', re.IGNORECASE)
SECTION_HEADER_RE = re.compile(r'^#{1,3}\s+\S')
OQ_SECTION_RE = re.compile(r'^##\s+Open Questions\s*$', re.IGNORECASE)
INDENTED_RE = re.compile(r'^\s{2,}\S')
COMMENT_LINE_RE = re.compile(r'^Comment:\s*(.*)$', re.IGNORECASE)
PRIORITIES = ('High', 'Medium', 'Low')


class RTMHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        if self.path == '/save-ticket':
            self._handle_save_ticket(raw)
        elif self.path == '/save-oq-status':
            self._handle_save_oq_status(raw)
        elif self.path == '/save-scope':
            self._handle_save_scope(raw)
        elif self.path == '/save-comment':
            self._handle_save_comment(raw)
        elif self.path == '/add-oq':
            self._handle_add_oq(raw)
        elif self.path == '/add-requirement':
            self._handle_add_requirement(raw)
        elif self.path == '/add-testcase':
            self._handle_add_testcase(raw)
        elif self.path == '/edit-requirement':
            self._handle_edit_requirement(raw)
        elif self.path == '/edit-testcase':
            self._handle_edit_testcase(raw)
        else:
            self._respond(404, {'ok': False, 'error': 'not found'})

    # ---------------- test case tickets ----------------

    def _handle_save_ticket(self, raw):
        try:
            payload = json.loads(raw)
            tc_id = str(payload['id']).strip().upper()
            ticket = str(payload.get('ticket', '')).strip()
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not TC_ID_RE.match(tc_id):
            self._respond(400, {'ok': False, 'error': 'invalid test case id'})
            return

        lines = self._read_md()
        if lines is None:
            return

        line_re = re.compile(
            r'^(-\s+' + re.escape(tc_id) + r'\s*:\s*.*?\s*[-–—]\s*Ticket:)\s*.*?\s*((?:[-–—]\s*Scope:\s*.*)?)\s*$',
            re.IGNORECASE
        )
        for i, line in enumerate(lines):
            m = line_re.match(line.rstrip('\n'))
            if m:
                scope_suffix = m.group(2)
                lines[i] = (
                    m.group(1) + (' ' + ticket if ticket else '')
                    + (' ' + scope_suffix if scope_suffix else '') + '\n'
                )
                self._write_md(lines)
                self._respond(200, {'ok': True, 'id': tc_id, 'ticket': ticket})
                return

        self._respond(404, {'ok': False, 'error': f'{tc_id} not found in requirement.md'})

    # ---------------- open question status ----------------

    def _handle_save_oq_status(self, raw):
        try:
            payload = json.loads(raw)
            oq_id = str(payload['id']).strip().upper()
            status = str(payload.get('status', '')).strip()
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not OQ_ID_RE.match(oq_id):
            self._respond(400, {'ok': False, 'error': 'invalid open question id'})
            return
        if status.lower() not in ('open', 'answered'):
            self._respond(400, {'ok': False, 'error': 'status must be Open or Answered'})
            return

        lines = self._read_md()
        if lines is None:
            return

        line_re = re.compile(
            r'^(-\s+' + re.escape(oq_id) + r'\b.*?[-–—]\s*Status:)\s*.*?\s*((?:[-–—]\s*Scope:\s*.*)?)\s*$',
            re.IGNORECASE
        )
        for i, line in enumerate(lines):
            m = line_re.match(line.rstrip('\n'))
            if m:
                scope_suffix = m.group(2)
                lines[i] = (
                    m.group(1) + ' ' + status
                    + (' ' + scope_suffix if scope_suffix else '') + '\n'
                )
                self._write_md(lines)
                self._respond(200, {'ok': True, 'id': oq_id, 'status': status})
                return

        self._respond(404, {'ok': False, 'error': f'{oq_id} not found in requirement.md'})

    # ---------------- out-of-scope marking ----------------

    def _handle_save_scope(self, raw):
        try:
            payload = json.loads(raw)
            item_type = str(payload.get('type', '')).strip().lower()
            item_id = str(payload['id']).strip().upper()
            out_of_scope = bool(payload.get('outOfScope', False))
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if item_type not in ('req', 'tc', 'oq'):
            self._respond(400, {'ok': False, 'error': 'type must be req, tc, or oq'})
            return

        id_re = {'req': REQ_ID_RE, 'tc': TC_ID_RE, 'oq': OQ_ID_RE}[item_type]
        if not id_re.match(item_id):
            self._respond(400, {'ok': False, 'error': f'invalid {item_type} id'})
            return

        lines = self._read_md()
        if lines is None:
            return

        setter = {'req': self._set_req_scope, 'tc': self._set_tc_scope, 'oq': self._set_oq_scope}[item_type]
        if not setter(lines, item_id, out_of_scope):
            self._respond(404, {'ok': False, 'error': f'{item_id} not found in requirement.md'})
            return

        self._write_md(lines)
        self._respond(200, {'ok': True, 'type': item_type, 'id': item_id, 'outOfScope': out_of_scope})

    def _set_tc_scope(self, lines, tc_id, out_of_scope):
        line_re = re.compile(
            r'^(-\s+' + re.escape(tc_id) + r'\s*:\s*.*?\s*[-–—]\s*Ticket:)\s*(.*?)\s*(?:[-–—]\s*Scope:\s*.*)?\s*$',
            re.IGNORECASE
        )
        for i, line in enumerate(lines):
            m = line_re.match(line.rstrip('\n'))
            if m:
                ticket = m.group(2)
                lines[i] = (
                    m.group(1) + (' ' + ticket if ticket else '')
                    + (' — Scope: Out of Scope' if out_of_scope else '') + '\n'
                )
                return True
        return False

    def _set_oq_scope(self, lines, oq_id, out_of_scope):
        line_re = re.compile(
            r'^(-\s+' + re.escape(oq_id) + r'\b.*?[-–—]\s*Status:)\s*([A-Za-z][A-Za-z ]*?)\s*(?:[-–—]\s*Scope:\s*.*)?\s*$',
            re.IGNORECASE
        )
        for i, line in enumerate(lines):
            m = line_re.match(line.rstrip('\n'))
            if m:
                status = m.group(2)
                lines[i] = (
                    m.group(1) + ' ' + status
                    + (' — Scope: Out of Scope' if out_of_scope else '') + '\n'
                )
                return True
        return False

    def _set_req_scope(self, lines, req_id, out_of_scope):
        header_idx = self._find_item_line(lines, REQ_HEADER_RE, req_id)
        if header_idx is None:
            return False

        meta_idx, comment_idx, _ = self._scan_req_meta(lines, header_idx)
        if meta_idx is not None:
            raw_line = lines[meta_idx].rstrip('\n')
            body = raw_line.split('>', 1)[1].strip()
            parts = [p.strip() for p in body.split('|') if p.strip()]
            parts = [p for p in parts if not re.match(r'^Scope\s*:', p, re.IGNORECASE)]
            if out_of_scope:
                parts.append('Scope: Out of Scope')
            if parts:
                lines[meta_idx] = '> ' + ' | '.join(parts) + '\n'
            else:
                del lines[meta_idx]
        elif out_of_scope:
            # No Priority/Status line exists yet — a Priority/Status/Scope
            # line always sits BEFORE any comment line, so insert before it.
            insert_at = comment_idx if comment_idx is not None else header_idx + 1
            lines.insert(insert_at, '> Scope: Out of Scope\n')
        return True

    # ---------------- comments ----------------

    def _find_item_line(self, lines, line_start_re, item_id):
        for i, line in enumerate(lines):
            m = line_start_re.match(line.rstrip('\n'))
            if m and m.group(1).upper() == item_id:
                return i
        return None

    def _scan_req_meta(self, lines, header_idx):
        """Scan the '>' lines directly after a REQ header.

        Returns (meta_idx, comment_idx, next_idx): meta_idx is the
        Priority/Status/Scope line if present, comment_idx is the Comment
        line if present, next_idx is the first line after this block
        (where the description, if any, begins).
        """
        meta_idx = None
        comment_idx = None
        j = header_idx + 1
        while j < len(lines) and lines[j].lstrip().startswith('>'):
            body = lines[j].rstrip('\n').split('>', 1)[1].strip()
            if COMMENT_LINE_RE.match(body):
                comment_idx = j
            else:
                meta_idx = j
            j += 1
        return meta_idx, comment_idx, j

    def _continuation_block(self, lines, start_idx):
        j = start_idx + 1
        while (
            j < len(lines)
            and lines[j].strip() != ''
            and INDENTED_RE.match(lines[j])
            and not lines[j].lstrip().startswith('- ')
        ):
            j += 1
        return start_idx + 1, j

    def _clean_comment(self, comment):
        comment = re.sub(r'^\s*Comment:\s*', '', comment, flags=re.IGNORECASE)
        return comment.replace('\n', ' ').replace('\r', ' ').strip()

    def _set_comment_in_block(self, lines, item_line_idx, comment):
        block_start, block_end = self._continuation_block(lines, item_line_idx)
        comment_idx = None
        last_idx = item_line_idx
        for i in range(block_start, block_end):
            if COMMENT_LINE_RE.match(lines[i].strip()):
                comment_idx = i
            last_idx = i

        comment = self._clean_comment(comment)
        if comment:
            new_line = '  Comment: ' + comment + '\n'
            if comment_idx is not None:
                lines[comment_idx] = new_line
            else:
                lines.insert(last_idx + 1, new_line)
        elif comment_idx is not None:
            del lines[comment_idx]
        return comment

    def _set_tc_comment(self, lines, tc_id, comment):
        idx = self._find_item_line(lines, TC_LINE_START_RE, tc_id)
        if idx is None:
            return None
        return self._set_comment_in_block(lines, idx, comment)

    def _set_oq_comment(self, lines, oq_id, comment):
        idx = self._find_item_line(lines, OQ_LINE_START_RE, oq_id)
        if idx is None:
            return None
        return self._set_comment_in_block(lines, idx, comment)

    def _set_req_comment(self, lines, req_id, comment):
        header_idx = self._find_item_line(lines, REQ_HEADER_RE, req_id)
        if header_idx is None:
            return None

        comment = self._clean_comment(comment)
        meta_idx, comment_idx, _ = self._scan_req_meta(lines, header_idx)

        if comment:
            new_line = '> Comment: ' + comment + '\n'
            if comment_idx is not None:
                lines[comment_idx] = new_line
            elif meta_idx is not None:
                lines.insert(meta_idx + 1, new_line)
            else:
                lines.insert(header_idx + 1, new_line)
        elif comment_idx is not None:
            del lines[comment_idx]
        return comment

    def _handle_save_comment(self, raw):
        try:
            payload = json.loads(raw)
            item_type = str(payload.get('type', '')).strip().lower()
            item_id = str(payload['id']).strip().upper()
            comment = str(payload.get('comment', ''))
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if item_type not in ('req', 'tc', 'oq'):
            self._respond(400, {'ok': False, 'error': 'type must be req, tc, or oq'})
            return

        id_re = {'req': REQ_ID_RE, 'tc': TC_ID_RE, 'oq': OQ_ID_RE}[item_type]
        if not id_re.match(item_id):
            self._respond(400, {'ok': False, 'error': f'invalid {item_type} id'})
            return

        lines = self._read_md()
        if lines is None:
            return

        setter = {'req': self._set_req_comment, 'tc': self._set_tc_comment, 'oq': self._set_oq_comment}[item_type]
        result = setter(lines, item_id, comment)
        if result is None:
            self._respond(404, {'ok': False, 'error': f'{item_id} not found in requirement.md'})
            return

        self._write_md(lines)
        self._respond(200, {'ok': True, 'type': item_type, 'id': item_id, 'comment': result})

    # ---------------- add open question ----------------

    def _handle_add_oq(self, raw):
        try:
            payload = json.loads(raw)
            text = str(payload.get('text', '')).strip().replace('\n', ' ').replace('\r', ' ')
            related_raw = payload.get('related', [])
            related = [str(r).strip().upper() for r in related_raw if str(r).strip()] if isinstance(related_raw, list) else []
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not text:
            self._respond(400, {'ok': False, 'error': 'question text is required'})
            return
        for r in related:
            if not REQ_ID_RE.match(r):
                self._respond(400, {'ok': False, 'error': f'invalid related id: {r}'})
                return

        lines = self._read_md()
        if lines is None:
            return

        header_idx = None
        last_oq_idx = None
        for i, line in enumerate(lines):
            if OQ_SECTION_RE.match(line.rstrip('\n')):
                header_idx = i
            if header_idx is not None and OQ_LINE_START_RE.match(line):
                last_oq_idx = i

        if header_idx is None:
            self._respond(500, {'ok': False, 'error': '"## Open Questions" section not found in requirement.md'})
            return

        oq_id = self._next_id(lines, 'OQ', OQ_LINE_START_RE)
        related_part = f' (Related: {", ".join(related)})' if related else ''
        new_line = f'- {oq_id}{related_part}: {text} — Status: Open\n'

        if last_oq_idx is not None:
            insert_at = last_oq_idx + 1
        else:
            insert_at = header_idx + 1
            if insert_at < len(lines) and lines[insert_at].strip() == '':
                insert_at += 1

        lines.insert(insert_at, new_line)
        self._write_md(lines)
        self._respond(200, {'ok': True, 'id': oq_id, 'text': text, 'related': related, 'status': 'Open'})

    # ---------------- add requirement ----------------

    def _handle_add_requirement(self, raw):
        try:
            payload = json.loads(raw)
            title = str(payload.get('title', '')).strip().replace('\n', ' ').replace('\r', ' ')
            priority = str(payload.get('priority', '')).strip()
            status = str(payload.get('status', '')).strip()
            description = str(payload.get('description', '')).strip()
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not title:
            self._respond(400, {'ok': False, 'error': 'requirement title is required'})
            return
        if priority and priority not in PRIORITIES:
            self._respond(400, {'ok': False, 'error': 'priority must be High, Medium, or Low'})
            return

        lines = self._read_md()
        if lines is None:
            return

        req_id = self._next_id(lines, 'REQ', REQ_HEADER_RE)

        oq_header_idx = None
        for i, line in enumerate(lines):
            if OQ_SECTION_RE.match(line.rstrip('\n')):
                oq_header_idx = i
                break

        block = [f'### {req_id}: {title}\n']
        meta_parts = []
        if priority:
            meta_parts.append(f'Priority: {priority}')
        if status:
            meta_parts.append(f'Status: {status}')
        if meta_parts:
            block.append('> ' + ' | '.join(meta_parts) + '\n')
        block.append('\n')
        if description:
            block.append(description + '\n')
            block.append('\n')
        block.append('#### Test Cases\n')
        block.append('\n')

        if oq_header_idx is not None:
            lines[oq_header_idx:oq_header_idx] = block
        else:
            if lines and lines[-1].strip() != '':
                lines.append('\n')
            lines.extend(block)

        self._write_md(lines)
        self._respond(200, {
            'ok': True, 'id': req_id, 'title': title, 'priority': priority,
            'status': status, 'description': description
        })

    # ---------------- edit requirement ----------------

    def _req_description_range(self, lines, header_idx):
        """Non-blank description lines for a requirement: between its
        meta/comment block and its Test Cases marker (or next section)."""
        _, _, after_meta = self._scan_req_meta(lines, header_idx)
        start = after_meta
        while start < len(lines) and lines[start].strip() == '':
            start += 1
        end = start
        while end < len(lines):
            line = lines[end].rstrip('\n')
            if TC_MARKER_RE.match(line) or REQ_HEADER_RE.match(line) or OQ_SECTION_RE.match(line):
                break
            if SECTION_HEADER_RE.match(line) and not TC_MARKER_RE.match(line):
                break
            end += 1
        while end > start and lines[end - 1].strip() == '':
            end -= 1
        return start, end

    def _handle_edit_requirement(self, raw):
        try:
            payload = json.loads(raw)
            req_id = str(payload['id']).strip().upper()
            title = str(payload.get('title', '')).strip().replace('\n', ' ').replace('\r', ' ')
            priority = str(payload.get('priority', '')).strip()
            status = str(payload.get('status', '')).strip()
            description = str(payload.get('description', '')).strip()
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not REQ_ID_RE.match(req_id):
            self._respond(400, {'ok': False, 'error': 'invalid requirement id'})
            return
        if not title:
            self._respond(400, {'ok': False, 'error': 'requirement title is required'})
            return
        if priority and priority not in PRIORITIES:
            self._respond(400, {'ok': False, 'error': 'priority must be High, Medium, or Low'})
            return

        lines = self._read_md()
        if lines is None:
            return

        header_idx = self._find_item_line(lines, REQ_HEADER_RE, req_id)
        if header_idx is None:
            self._respond(404, {'ok': False, 'error': f'{req_id} not found in requirement.md'})
            return

        # Replace the description first — this only shifts indices AFTER
        # desc_start, which is always past the header/meta lines below.
        desc_start, desc_end = self._req_description_range(lines, header_idx)
        new_desc_lines = [description + '\n'] if description else []
        lines[desc_start:desc_end] = new_desc_lines

        meta_idx, _, _ = self._scan_req_meta(lines, header_idx)
        existing_scope = None
        if meta_idx is not None:
            body = lines[meta_idx].rstrip('\n').split('>', 1)[1].strip()
            for part in body.split('|'):
                part = part.strip()
                if re.match(r'^Scope\s*:', part, re.IGNORECASE):
                    existing_scope = part
        meta_parts = []
        if priority:
            meta_parts.append(f'Priority: {priority}')
        if status:
            meta_parts.append(f'Status: {status}')
        if existing_scope:
            meta_parts.append(existing_scope)

        if meta_idx is not None:
            if meta_parts:
                lines[meta_idx] = '> ' + ' | '.join(meta_parts) + '\n'
            else:
                del lines[meta_idx]
        elif meta_parts:
            lines.insert(header_idx + 1, '> ' + ' | '.join(meta_parts) + '\n')

        lines[header_idx] = f'### {req_id}: {title}\n'

        self._write_md(lines)
        self._respond(200, {
            'ok': True, 'id': req_id, 'title': title, 'priority': priority,
            'status': status, 'description': description
        })

    # ---------------- add test case ----------------

    def _handle_add_testcase(self, raw):
        try:
            payload = json.loads(raw)
            req_id = str(payload.get('reqId', '')).strip().upper()
            title = str(payload.get('title', '')).strip().replace('\n', ' ').replace('\r', ' ')
            ticket = str(payload.get('ticket', '')).strip()
            description = str(payload.get('description', '')).strip().replace('\n', ' ').replace('\r', ' ')
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not REQ_ID_RE.match(req_id):
            self._respond(400, {'ok': False, 'error': 'invalid requirement id'})
            return
        if not title:
            self._respond(400, {'ok': False, 'error': 'test case title is required'})
            return

        lines = self._read_md()
        if lines is None:
            return

        bounds = self._find_req_bounds(lines, req_id)
        if bounds is None:
            self._respond(404, {'ok': False, 'error': f'{req_id} not found in requirement.md'})
            return
        header_idx, end_idx = bounds

        tc_id = self._next_id(lines, 'TC', TC_LINE_START_RE)
        new_lines = [f'- {tc_id}: {title} — Ticket:' + (f' {ticket}' if ticket else '') + '\n']
        if description:
            new_lines.append(f'  {description}\n')

        marker_idx = None
        last_nonblank = header_idx
        for i in range(header_idx, end_idx):
            if TC_MARKER_RE.match(lines[i].rstrip('\n')):
                marker_idx = i
            if lines[i].strip() != '':
                last_nonblank = i

        if marker_idx is not None:
            insert_at = last_nonblank + 1
            lines[insert_at:insert_at] = new_lines
        else:
            insert_at = last_nonblank + 1
            block = ['\n', '#### Test Cases\n'] + new_lines
            lines[insert_at:insert_at] = block

        self._write_md(lines)
        self._respond(200, {'ok': True, 'id': tc_id, 'reqId': req_id, 'title': title, 'ticket': ticket, 'description': description})

    # ---------------- edit test case ----------------

    def _handle_edit_testcase(self, raw):
        try:
            payload = json.loads(raw)
            tc_id = str(payload['id']).strip().upper()
            title = str(payload.get('title', '')).strip().replace('\n', ' ').replace('\r', ' ')
            description = str(payload.get('description', '')).strip().replace('\n', ' ').replace('\r', ' ')
        except Exception:
            self._respond(400, {'ok': False, 'error': 'bad request body'})
            return

        if not TC_ID_RE.match(tc_id):
            self._respond(400, {'ok': False, 'error': 'invalid test case id'})
            return
        if not title:
            self._respond(400, {'ok': False, 'error': 'test case title is required'})
            return

        lines = self._read_md()
        if lines is None:
            return

        idx = self._find_item_line(lines, TC_LINE_START_RE, tc_id)
        if idx is None:
            self._respond(404, {'ok': False, 'error': f'{tc_id} not found in requirement.md'})
            return

        line_re = re.compile(
            r'^-\s+' + re.escape(tc_id) + r'\s*:\s*.*?\s*([-–—]\s*Ticket:.*)$',
            re.IGNORECASE
        )
        m = line_re.match(lines[idx].rstrip('\n'))
        if not m:
            self._respond(500, {'ok': False, 'error': f'could not parse {tc_id} line'})
            return
        lines[idx] = f'- {tc_id}: {title} ' + m.group(1) + '\n'

        block_start, block_end = self._continuation_block(lines, idx)
        comment_idx = None
        desc_idx = None
        for i in range(block_start, block_end):
            if COMMENT_LINE_RE.match(lines[i].strip()):
                comment_idx = i
            else:
                desc_idx = i

        if description:
            new_line = '  ' + description + '\n'
            if desc_idx is not None:
                lines[desc_idx] = new_line
            else:
                insert_at = comment_idx if comment_idx is not None else idx + 1
                lines.insert(insert_at, new_line)
        elif desc_idx is not None:
            del lines[desc_idx]

        self._write_md(lines)
        self._respond(200, {'ok': True, 'id': tc_id, 'title': title, 'description': description})

    # ---------------- helpers ----------------

    def _next_id(self, lines, prefix, line_start_re):
        max_num = 0
        for line in lines:
            m = line_start_re.match(line)
            if m:
                num_m = re.search(r'(\d+)$', m.group(1))
                if num_m:
                    max_num = max(max_num, int(num_m.group(1)))
        return f'{prefix}-{max_num + 1:03d}'

    def _find_req_bounds(self, lines, req_id):
        header_idx = None
        for i, line in enumerate(lines):
            m = REQ_HEADER_RE.match(line.rstrip('\n'))
            if m and m.group(1).upper() == req_id:
                header_idx = i
                break
        if header_idx is None:
            return None

        end_idx = len(lines)
        for j in range(header_idx + 1, len(lines)):
            line = lines[j].rstrip('\n')
            if SECTION_HEADER_RE.match(line) and not TC_MARKER_RE.match(line):
                end_idx = j
                break
        return header_idx, end_idx

    def _read_md(self):
        try:
            with open(MD_PATH, 'r', encoding='utf-8') as f:
                return f.readlines()
        except FileNotFoundError:
            self._respond(500, {'ok': False, 'error': f'requirement.md not found in {ROOT}'})
            return None

    def _write_md(self, lines):
        with open(MD_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _respond(self, code, body):
        data = json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))


if __name__ == '__main__':
    with http.server.ThreadingHTTPServer(('', PORT), RTMHandler) as httpd:
        print(f'RTM dashboard: http://localhost:{PORT}/RTMdashboard.html  (serving {ROOT})')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
