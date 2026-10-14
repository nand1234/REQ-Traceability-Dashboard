#!/usr/bin/env python3
"""Build the Jira 'AC-n + Required Tests' markdown block for one Jira ticket from the RTM
state (output of parse_rtm.js) and a hand-written grouping file.

  gen_jira_ac.py list  --state s.json --ticket PROJ-123
      Lists the test cases that name this ticket: id, co-owners, title, planned layer, and
      whether the description is Given/When/Then (copyable) or needs an override.

  gen_jira_ac.py build --state s.json --groups g.json --out block.md [--ticket PROJ-123]
      Writes the markdown block. With --ticket, the groups must cover exactly the cases
      that name that ticket (nothing missing, nothing twice). Without it (a new ticket
      such as the E2E one) any case ids may be used.

groups.json (a list; order = AC numbering, restarts at 1 per ticket):
  [{"title": "Theme title",
    "tcs": ["TC-047", "TC-048"],
    "ticks": ["Unit", "Integration"],          # any of Unit, Integration, Visual, E2E
    "why": "one short clause: why these layers",
    "required_tests": false,                   # optional: omit the Required Tests block (CI / ops checks)
    "overrides": {"TC-068": {"given": "...", "when": "...", "then": "..."}}   # optional, per case
  }]

Each assertion becomes three lines (GIVEN / WHEN / THEN, bold caps, two trailing spaces for
the line break), with a blank line between assertions.
"""
import argparse, json, re, sys

BOXES = ['Unit', 'Integration', 'Visual', 'E2E']

# dashboard-only references that mean nothing in Jira; anything left over is reported
SUBS = [
    (r'\(POC bug \d+; bounds in OQ-\d+\)', '(the bounds are still to agree with product)'),
    (r' \(POC bug \d+\)', ''),
    (r'\(OQ-\d+; ', '('),
    (r'; OQ-\d+\)', ')'),
    (r' \(OQ-\d+\)', ''),
]
GWT = re.compile(r'^Given (.*?)\. When (.*?)\. Then (.*?)\.(?: Planned layer: .*)?$')


def load_cases(state_path):
    state = json.load(open(state_path, encoding='utf-8'))
    return {t['id']: t for r in state['requirements'] for t in r['testCases']}


def clean(s):
    for a, b in SUBS:
        s = re.sub(a, b, s)
    return s


def names_ticket(case, ticket):
    return re.search(r'(?<![A-Z0-9-])%s(?![0-9])' % re.escape(ticket), case['ticket']) is not None


def planned_layer(desc):
    m = re.search(r'Planned layer: (.*?)\.(?: |$)', desc)
    return m.group(1) if m else '(none recorded)'


def cmd_list(a):
    cases = load_cases(a.state)
    rows = [t for t in cases.values() if names_ticket(t, a.ticket)]
    if not rows:
        sys.exit('no test case names %s' % a.ticket)
    print('%d case(s) name %s' % (len(rows), a.ticket))
    for t in rows:
        others = sorted(set(re.findall(r'[A-Z]+-\d+', t['ticket'])) - {a.ticket})
        flag = 'copyable' if GWT.match(t['description']) else 'NEEDS OVERRIDE (not Given/When/Then)'
        oos = ' [out of scope]' if t.get('outOfScope') else ''
        print('%s%s | co-owned with: %s | %s | layer: %s | %s' % (
            t['id'], oos, ', '.join(others) or '-', t['title'], planned_layer(t['description']), flag))
        if 'partial' in t['ticket']:
            print('   ^ ticket says "partial": write only the half this ticket owns (use an override)')


def block_for(case, override):
    if override:
        g, w, th = override['given'], override['when'], override['then']
    else:
        m = GWT.match(case['description'])
        if not m:
            sys.exit('%s: description is not Given/When/Then, add an override for it' % case['id'])
        g, w, th = (clean(x) for x in m.groups())
    th = th.rstrip('.') + '.'
    return '**GIVEN** %s  \n**WHEN** %s  \n**THEN** %s' % (g.rstrip('.'), w.rstrip('.'), th)


def cmd_build(a):
    cases = load_cases(a.state)
    groups = json.load(open(a.groups, encoding='utf-8'))
    used = [i for g in groups for i in g['tcs']]
    unknown = [i for i in used if i not in cases]
    if unknown:
        sys.exit('unknown case ids: %s' % unknown)
    if len(used) != len(set(used)):
        sys.exit('a case is in two groups')
    if a.ticket:
        owned = sorted(i for i, t in cases.items() if names_ticket(t, a.ticket))
        if owned != sorted(used):
            sys.exit('groups out of sync with the RTM for %s: %s' % (a.ticket, sorted(set(owned) ^ set(used))))
    out = []
    for n, g in enumerate(groups, 1):
        assertions = [block_for(cases[i], g.get('overrides', {}).get(i)) for i in g['tcs']]
        text = '**AC-%d %s**\n\n%s\n' % (n, g['title'], '\n\n'.join(assertions))
        if g.get('required_tests') is not False:
            bad = set(g['ticks']) - set(BOXES)
            if bad:
                sys.exit('unknown boxes %s (use %s)' % (sorted(bad), BOXES))
            line = ' | '.join(('☑ ' if b in g['ticks'] else '☐ ') + b for b in BOXES)
            text = text.rstrip('\n') + '\n\n###### Required Tests\n%s  \n_Why: %s_\n' % (line, g['why'].strip())
        out.append(text)
    result = '\n'.join(out)
    left = sorted(set(re.findall(r'OQ-\d+|POC bug \d+|TC-\d+', result)))
    if left:
        print('WARNING: dashboard-only references left in the text: %s (fix with an override)' % left, file=sys.stderr)
    open(a.out, 'w', encoding='utf-8').write(result)
    print('wrote %d AC(s), %d assertion(s) -> %s' % (len(groups), len(used), a.out))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list'); l.add_argument('--state', required=True); l.add_argument('--ticket', required=True)
    b = sub.add_parser('build'); b.add_argument('--state', required=True); b.add_argument('--groups', required=True)
    b.add_argument('--out', required=True); b.add_argument('--ticket')
    a = p.parse_args()
    {'list': cmd_list, 'build': cmd_build}[a.cmd](a)
