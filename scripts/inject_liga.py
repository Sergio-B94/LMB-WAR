# -*- coding: utf-8 -*-
import json

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\6b28ae4f-0eed-4aa2-9355-9c43acfd998c\scratchpad"
HTML_PATH = f"{SCRATCH}\\piratas_war.html"

with open(f"{SCRATCH}\\war_liga_output.json", encoding="utf-8") as f:
    data = json.load(f)

bat = data["batting"]
pit = data["pitching"]
val = data["validation"]
ctx = data["league_context"]

# Compact fields only (drop what the UI doesn't need, keep it light)
bat_slim = [{
    "rank": r["rank"], "name": r["name"], "team": r["team"], "isPiratas": r["isPiratas"],
    "position": r["position"], "PA": r["PA"], "AVG": r["AVG"], "OBP": r["OBP"], "SLG": r["SLG"],
    "OPS": r["OPS"], "HR": r["HR"], "wOBA": r["wOBA"], "OPSplus": r["OPSplus"],
    "battingRuns": r["battingRuns"], "WAR": r["WAR"], "WARplus": r["WARplus"],
} for r in bat]

pit_slim = [{
    "rank": r["rank"], "name": r["name"], "team": r["team"],
    "IP": r["IP"], "ERA": r["ERA"], "WHIP": r["WHIP"], "K": r["K"], "BB": r["BB"],
    "W": r["W"], "L": r["L"], "FIP": r["FIP"], "ERAplus": r["ERAplus"],
    "WAR": r["WAR"], "WARplus": r["WARplus"],
} for r in pit]

bat_json = json.dumps(bat_slim, ensure_ascii=False, separators=(',', ':'))
pit_json = json.dumps(pit_slim, ensure_ascii=False, separators=(',', ':'))

n_piratas_bat = sum(1 for r in bat if r["isPiratas"])

# ---------------- HTML section to insert after the pitching </section> (line ~259) ----------------
html_section = f'''
  <section class="panel">
    <div class="panel-head">
      <h2>Clasificaci\u00f3n completa \u2014 LMB 2026</h2>
      <span class="count">{{len(bat_slim)}} bateadores calificados de las 20 novenas \u00b7 {{len(pit_slim)}} lanzadores calificados</span>
    </div>
    <p class="league-note">Los mismos 130 bateadores y 49 lanzadores <em>calificados</em> que se usaron para derivar el contexto de liga
      (wOBA, ERA, runs por victoria, etc.) de este panel, ahora calculados individualmente y clasificados de mejor a peor WAR.
      Las filas de <b>Piratas de Campeche</b> est\u00e1n resaltadas. Ning\u00fan lanzador de Piratas alcanz\u00f3 el umbral oficial de
      entradas para calificar esta temporada \u2014 por eso no aparecen en la tabla de pitcheo.</p>
    <div class="card">
      <div class="table-scroll">
        <table id="ligaBatTable">
          <thead>
            <tr>
              <th data-key="rank" data-type="num" class="sorted">#</th>
              <th data-key="name" data-type="str">Jugador</th>
              <th data-key="team" data-type="str">Equipo</th>
              <th data-key="position" data-type="str">Pos</th>
              <th data-key="PA" data-type="num">PA</th>
              <th data-key="AVG" data-type="num">AVG</th>
              <th data-key="OPS" data-type="num">OPS</th>
              <th data-key="OPSplus" data-type="num">OPS+</th>
              <th data-key="WAR" data-type="num">WAR</th>
              <th data-key="WARplus" data-type="num">WAR+</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    <div class="card" style="margin-top:14px;">
      <div class="table-scroll">
        <table id="ligaPitTable">
          <thead>
            <tr>
              <th data-key="rank" data-type="num" class="sorted">#</th>
              <th data-key="name" data-type="str">Lanzador</th>
              <th data-key="team" data-type="str">Equipo</th>
              <th data-key="IP" data-type="num">IP</th>
              <th data-key="ERA" data-type="num">EFE</th>
              <th data-key="W" data-type="num">G</th>
              <th data-key="L" data-type="num">P</th>
              <th data-key="FIP" data-type="num">FIP</th>
              <th data-key="ERAplus" data-type="num">ERA+</th>
              <th data-key="WAR" data-type="num">WAR</th>
              <th data-key="WARplus" data-type="num">WAR+</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </section>
'''

# fix the {{...}} placeholders above (avoid f-string brace headaches) -> do plain replace
html_section = html_section.replace("{{len(bat_slim)}}", str(len(bat_slim))).replace("{{len(pit_slim)}}", str(len(pit_slim)))

# ---------------- CSS additions ----------------
css_add = '''
  .league-note{font-size:13px; color:var(--ink-muted); margin:0 0 12px;}
  tr.piratas-row{background:color-mix(in oklab, var(--maroon) 10%, var(--surface));}
  tr.piratas-row td:first-child{box-shadow: inset 3px 0 0 var(--maroon);}
  .rank-cell{color:var(--ink-muted); font-variant-numeric:tabular-nums;}
  .piratas-star{color:var(--maroon); font-size:11px;}
'''

# ---------------- JS additions ----------------
js_add = f'''
const LIGA_BATTING = {bat_json};
const LIGA_PITCHING = {pit_json};
const VALIDATION = {json.dumps(val, ensure_ascii=False)};
const LGCTX = {json.dumps(ctx, ensure_ascii=False)};

function renderLigaBatTable(data){{
  const tb = document.querySelector('#ligaBatTable tbody');
  tb.innerHTML = data.map(d => `<tr class="${{d.isPiratas ? 'piratas-row' : ''}}">
    <td class="rank-cell">${{d.rank}}</td>
    <td class="name-cell">${{d.isPiratas ? '<span class="piratas-star" title="Piratas de Campeche">★</span> ' : ''}}${{esc(d.name)}}</td>
    <td>${{esc(d.team)}}</td>
    <td><span class="pos-chip-cell">${{esc(d.position||'')}}</span></td>
    <td>${{d.PA}}</td>
    <td>${{d.AVG}}</td>
    <td>${{d.OPS}}</td>
    <td class="${{d.OPSplus>=100?'pos':'neg'}}">${{d.OPSplus}}</td>
    <td class="war ${{d.WAR>=0?'pos':'neg'}}">${{d.WAR>=0?'+':''}}${{d.WAR.toFixed(2)}}</td>
    <td class="${{d.WARplus>=100?'pos':'neg'}}">${{d.WARplus}}</td>
  </tr>`).join('');
}}

function renderLigaPitTable(data){{
  const tb = document.querySelector('#ligaPitTable tbody');
  tb.innerHTML = data.map(d => `<tr>
    <td class="rank-cell">${{d.rank}}</td>
    <td class="name-cell">${{esc(d.name)}}</td>
    <td>${{esc(d.team)}}</td>
    <td>${{d.IP.toFixed(1)}}</td>
    <td>${{d.ERA}}</td>
    <td>${{d.W}}</td>
    <td>${{d.L}}</td>
    <td>${{d.FIP.toFixed(2)}}</td>
    <td class="${{d.ERAplus>=100?'pos':'neg'}}">${{d.ERAplus}}</td>
    <td class="war ${{d.WAR>=0?'pos':'neg'}}">${{d.WAR>=0?'+':''}}${{d.WAR.toFixed(2)}}</td>
    <td class="${{d.WARplus>=100?'pos':'neg'}}">${{d.WARplus}}</td>
  </tr>`).join('');
}}

renderLigaBatTable(LIGA_BATTING);
renderLigaPitTable(LIGA_PITCHING);
setupSort('ligaBatTable', LIGA_BATTING, renderLigaBatTable, 'rank', 1);
setupSort('ligaPitTable', LIGA_PITCHING, renderLigaPitTable, 'rank', 1);
'''

with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

# 1) Insert new section after the second `</section>` (end of pitching panel)
marker = '</section>\n\n  <details class="method">'
assert marker in html, "pitching-section marker not found"
html = html.replace(marker, '</section>\n' + html_section + '\n  <details class="method">', 1)

# 2) Insert CSS just before the closing </style>
assert '</style>' in html
html = html.replace('</style>', css_add + '</style>', 1)

# 3) Insert JS right before the final </script>
assert html.rstrip().endswith('</script>')
idx = html.rstrip().rfind('</script>')
html = html[:idx] + js_add + '\n' + html[idx:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Injected. New file size:", len(html), "chars")
print("Piratas batters in league table:", n_piratas_bat)
print("Validation:", val)
