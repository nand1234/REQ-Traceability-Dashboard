#!/usr/bin/env node
// Parse a feature's requirement.md with the dashboard's OWN parser (extracted
// verbatim from that feature's RTMdashboard.html), so the data this skill reads
// is exactly what the dashboard shows. Prints the parsed state as JSON.
//
// usage: node parse_rtm.js features/<feature> [out.json]
const fs = require('fs');
const path = require('path');

const dir = process.argv[2];
const outPath = process.argv[3];
if (!dir) { console.error('usage: node parse_rtm.js features/<feature> [out.json]'); process.exit(2); }

const htmlPath = path.join(dir, 'RTMdashboard.html');
const mdPath = path.join(dir, 'requirement.md');
for (const p of [htmlPath, mdPath]) {
  if (!fs.existsSync(p)) { console.error('missing file: ' + p); process.exit(2); }
}

const html = fs.readFileSync(htmlPath, 'utf8');
function grab(startMarker, endMarker) {
  const a = html.indexOf(startMarker);
  const b = html.indexOf(endMarker, a);
  if (a < 0 || b < 0) { console.error('parser marker not found in ' + htmlPath + ': ' + startMarker); process.exit(2); }
  return html.slice(a, b);
}
const code =
  grab('function normStatus(s)', 'function statusRole(s)') +
  grab('function parseMetaLine(line)', '// ---------------- render ----------------') +
  '\nreturn parseRTM;';
const parseRTM = new Function(code)();
const state = parseRTM(fs.readFileSync(mdPath, 'utf8'));

const json = JSON.stringify(state);
if (outPath) {
  fs.writeFileSync(outPath, json);
  const tcs = state.requirements.flatMap(r => r.testCases);
  console.error(`parsed ${dir}: ${state.requirements.length} REQ, ${tcs.length} TC, ${state.openQuestions.length} OQ -> ${outPath}`);
} else {
  process.stdout.write(json);
}
