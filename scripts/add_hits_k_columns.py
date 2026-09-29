# -*- coding: utf-8 -*-
import json, re, unicodedata, difflib
from collections import defaultdict

HTML_PATH = r"C:\Users\hp\OneDrive\Sergio Notaria Claude\CODE\LMB\dashboard\piratas_war.html"
CSV_PATH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-Sergio-Notaria-Claude-CODE-LMB\7e4bb95b-9c2d-45cc-b967-24c287ac7a75\scratchpad\hitting_all.csv"

def norm(s):
    s = (s or '').strip()
    s = s.replace('\ufffd', '')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-zA-Z0-9 ]', '', s)
    return re.sub(r'\s+', ' ', s).lower().strip()

csv_rows = []
with open(CSV_PATH, encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('|')
        name, team, h = parts[0], parts[1], parts[2]
        csv_rows.append((name, team, int(h) if h != '' else None))
assert len(csv_rows) == 464, len(csv_rows)

by_team = defaultdict(list)
for name, team, h in csv_rows:
    by_team[norm(team)].append((name, h))
team_keys = list(by_team.keys())

all_by_norm = defaultdict(list)
for name, team, h in csv_rows:
    all_by_norm[norm(name)].append((name, team, h))

def find_team_bucket(team_label):
    nt = norm(team_label)
    if nt in by_team:
        return by_team[nt]
    for k in team_keys:
        if nt in k or k in nt:
            return by_team[k]
    first_word = nt.split(' ')[0]
    for k in team_keys:
        if k.split(' ')[0] == first_word:
            return by_team[k]
    return None

def h_for(team_label, player_name):
    pname = norm(player_name)
    bucket = find_team_bucket(team_label)
    if bucket:
        for name, h in bucket:
            if norm(name) == pname:
                return h
        names = [n for n, h in bucket]
        close = difflib.get_close_matches(pname, [norm(n) for n in names], n=1, cutoff=0.82)
        if close:
            for name, h in bucket:
                if norm(name) == close[0]:
                    return h
    matches = all_by_norm.get(pname)
    if matches:
        teams = set(t for n, t, h in matches)
        if len(teams) == 1 or len(matches) == 1:
            return matches[0][2]
        return None  # ambiguous
    return None

with open(HTML_PATH, encoding='utf-8') as f:
    lines = f.readlines()

def line_idx_for(const_name):
    for i, line in enumerate(lines):
        if line.startswith('const ' + const_name + ' ='):
            return i
    raise AssertionError(const_name + ' not found')

def extract(const_name):
    i = line_idx_for(const_name)
    m = re.match(r'^const ' + const_name + r' = (.*);\s*$', lines[i])
    assert m, const_name
    return i, json.loads(m.group(1))

i_bat, BATTING = extract('BATTING')
i_other, OTHER_TEAMS = extract('OTHER_TEAMS')
i_zona, ZONA_NORTE_TEAMS = extract('ZONA_NORTE_TEAMS')
i_ligabat, LIGA_BATTING = extract('LIGA_BATTING')

misses = 0
for d in BATTING:
    d['H'] = h_for('Piratas', d['name'])
    if d['H'] is None: misses += 1
for d in LIGA_BATTING:
    d['H'] = h_for(d['team'], d['name'])
    if d['H'] is None: misses += 1
for group in (OTHER_TEAMS, ZONA_NORTE_TEAMS):
    for team_key, obj in group.items():
        for d in obj['BATTING']:
            d['H'] = h_for(team_key, d['name'])
            if d['H'] is None: misses += 1

assert misses == 0, f"{misses} unresolved H values -- aborting"

def dump_line(const_name, obj):
    return 'const %s = %s;\n' % (const_name, json.dumps(obj, ensure_ascii=False, separators=(',', ':')))

lines[i_bat] = dump_line('BATTING', BATTING)
lines[i_other] = dump_line('OTHER_TEAMS', OTHER_TEAMS)
lines[i_zona] = dump_line('ZONA_NORTE_TEAMS', ZONA_NORTE_TEAMS)
lines[i_ligabat] = dump_line('LIGA_BATTING', LIGA_BATTING)

html = ''.join(lines)

# --- thead edits ---
def must_replace(html, old, new, label):
    assert html.count(old) == 1, f"expected exactly 1 occurrence of {label}, found {html.count(old)}"
    return html.replace(old, new)

# 1) #batTable thead: insert H after PA (disambiguated from ligaBatTable by the OBP header that follows)
html = must_replace(html,
    '<th data-key="PA" data-type="num">PA</th>\n              <th data-key="AVG" data-type="num">AVG</th>\n              <th data-key="OBP" data-type="num">OBP</th>',
    '<th data-key="PA" data-type="num">PA</th>\n              <th data-key="H" data-type="num">H</th>\n              <th data-key="AVG" data-type="num">AVG</th>\n              <th data-key="OBP" data-type="num">OBP</th>',
    'batTable PA->AVG->OBP')

# 2) #ligaBatTable thead: insert H after PA, HR after OPS
html = must_replace(html,
    '<th data-key="PA" data-type="num">PA</th>\n              <th data-key="AVG" data-type="num">AVG</th>\n              <th data-key="OPS" data-type="num">OPS</th>\n              <th data-key="OPSplus" data-type="num">OPS+</th>',
    '<th data-key="PA" data-type="num">PA</th>\n              <th data-key="H" data-type="num">H</th>\n              <th data-key="AVG" data-type="num">AVG</th>\n              <th data-key="OPS" data-type="num">OPS</th>\n              <th data-key="HR" data-type="num">HR</th>\n              <th data-key="OPSplus" data-type="num">OPS+</th>',
    'ligaBatTable PA/OPS')

# 3) #ligaPitTable thead: insert K after EFE
html = must_replace(html,
    '<th data-key="ERA" data-type="num">EFE</th>\n              <th data-key="W" data-type="num">G</th>',
    '<th data-key="ERA" data-type="num">EFE</th>\n              <th data-key="K" data-type="num">K</th>\n              <th data-key="W" data-type="num">G</th>',
    'ligaPitTable EFE->G')

# --- render function edits ---
# renderBatTable: insert H td after PA td (disambiguated via the OBP td that follows)
html = must_replace(html,
    "<td>${d.PA}</td>\n    <td>${d.AVG}</td>\n    <td>${d.OBP}</td>",
    "<td>${d.PA}</td>\n    <td>${d.H}</td>\n    <td>${d.AVG}</td>\n    <td>${d.OBP}</td>",
    'renderBatTable PA->AVG->OBP')

# renderLigaBatTable: insert H td after PA td, HR td after OPS td
html = must_replace(html,
    "<td>${d.PA}</td>\n    <td>${d.AVG}</td>\n    <td>${d.OPS}</td>\n    <td class=\"${d.OPSplus>=100?'pos':'neg'}\">${d.OPSplus}</td>",
    "<td>${d.PA}</td>\n    <td>${d.H}</td>\n    <td>${d.AVG}</td>\n    <td>${d.OPS}</td>\n    <td>${d.HR}</td>\n    <td class=\"${d.OPSplus>=100?'pos':'neg'}\">${d.OPSplus}</td>",
    'renderLigaBatTable PA/OPS')

# renderLigaPitTable: insert K td after ERA td
html = must_replace(html,
    "<td>${d.ERA}</td>\n    <td>${d.W}</td>",
    "<td>${d.ERA}</td>\n    <td>${d.K}</td>\n    <td>${d.W}</td>",
    'renderLigaPitTable ERA->W')

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("Done. Misses:", misses)
print("Piratas sample:", BATTING[0]['name'], 'H=', BATTING[0]['H'])
print("Liga sample:", LIGA_BATTING[0]['name'], 'H=', LIGA_BATTING[0]['H'], 'HR=', LIGA_BATTING[0].get('HR'))
