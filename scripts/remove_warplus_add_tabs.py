# -*- coding: utf-8 -*-
import json, re

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\6b28ae4f-0eed-4aa2-9355-9c43acfd998c\scratchpad"
HTML_PATH = f"{SCRATCH}\\piratas_war.html"

with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

orig_len = len(html)

# ---------- 1) Strip WARplus (and now-unused WAR+ anchor fields) from the 4 data arrays ----------
def strip_keys_from_array(html, var_name, keys):
    marker = f"const {var_name} = ["
    start = html.index(marker)
    arr_start = start + len(marker) - 1
    depth = 0
    i = arr_start
    while True:
        c = html[i]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    arr_end = i + 1
    data = json.loads(html[arr_start:arr_end])
    for entry in data:
        for k in keys:
            entry.pop(k, None)
    new_text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return html[:arr_start] + new_text + html[arr_end:]

for var_name in ["BATTING", "PITCHING", "LIGA_BATTING", "LIGA_PITCHING"]:
    html = strip_keys_from_array(html, var_name, ["WARplus"])

# Strip now-unused fields from LEAGUE object
league_marker = "const LEAGUE = "
lstart = html.index(league_marker) + len(league_marker)
lend = html.index(";", lstart) + 1
league_obj = json.loads(html[lstart:lend-1])
for k in ["paFull", "ipFull", "warPlusAnchorBat", "warPlusAnchorPit"]:
    league_obj.pop(k, None)
html = html[:lstart] + json.dumps(league_obj, ensure_ascii=False) + ";" + html[lend:]

print("Step 1 done (data arrays + LEAGUE cleaned)")

# ---------- 2) Remove the 4 "WAR+" <th> header cells ----------
th_pattern = '\n              <th data-key="WARplus" data-type="num">WAR+</th>'
n_th = html.count(th_pattern)
html = html.replace(th_pattern, '')
print(f"Step 2: removed {n_th} <th> WAR+ headers")

# ---------- 3) Remove the 4 WAR+ <td> render cells ----------
td_pattern = '\n    <td class="${d.WARplus>=100?\'pos\':\'neg\'}">${d.WARplus}</td>'
n_td = html.count(td_pattern)
html = html.replace(td_pattern, '')
print(f"Step 3: removed {n_td} WAR+ <td> render cells")

# ---------- 4) Remove the WAR+ methodology block (h4 + p + ul), but keep the validation <li> ----------
h4_marker = '<h4>WAR+'
h4_idx = html.index(h4_marker)
h4_start = html.rindex('<h4>', 0, h4_idx + 4)
ul_close = html.index('</ul>', h4_start) + len('</ul>')
block = html[h4_start:ul_close]

# Pull out the validation sentence to preserve it in a new, WAR+-independent section.
val_match = re.search(r'<li><b>\u2705 Ya validamos.*?</li>', block, re.S)
validation_li = val_match.group(0) if val_match else ''
# Drop the WAR+-only framing from that sentence (it references "arriba" i.e. the WAR+ anchor
# derivation above, which no longer exists) and stand it on its own.
validation_li_clean = validation_li.replace(
    '(m\u00e1s abajo, en la secci\u00f3n de clasificaci\u00f3n completa de la liga): ', ''
)

replacement = (
    '<h4>Nivel de reemplazo \u2014 validado con datos reales de la LMB, no solo asumido</h4>\n'
    '      <ul>\n        ' + validation_li_clean + '\n      </ul>'
)
html = html[:h4_start] + replacement + html[ul_close:]
print("Step 4: WAR+ methodology block replaced with validation-only section")

# ---------- 5) Clean the caveat box: drop WAR+-specific sentences ----------
html = html.replace(
    ' y los anclas\n        de "temporada completa" de WAR+ (420 PA / 100 IP) usan los l\u00edderes reales de la liga en 2026,\n        no los 600 PA / 200 IP de una temporada de 162 juegos de MLB.',
    '.'
)
html = html.replace(
    ' WAR+ es,\n        insistimos, un \u00edndice de elaboraci\u00f3n propia \u2014 no lo cites como si fuera una m\u00e9trica publicada.',
    ''
)
print("Step 5: caveat box cleaned")

# ---------- 6) Remove the const-grid "temporada completa" row (PA_FULL/IP_FULL, WAR+-only) ----------
grid_row = '\n  <div><b>${LEAGUE.paFull} PA / ${LEAGUE.ipFull} IP</b>"Temporada completa" en LMB (l\u00edderes reales 2026, no MLB)</div>'
n_grid = html.count(grid_row)
html = html.replace(grid_row, '')
print(f"Step 6: removed {n_grid} const-grid row(s)")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Saved. Length before:", orig_len, "after:", len(html))
