# -*- coding: utf-8 -*-
SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\6b28ae4f-0eed-4aa2-9355-9c43acfd998c\scratchpad"
HTML_PATH = f"{SCRATCH}\\piratas_war.html"

with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

# ---------- Locate the 3 sections by their headings (robust to line-number drift) ----------
def section_bounds(html, heading_text):
    h_idx = html.index(heading_text)
    sec_start = html.rindex('<section class="panel">', 0, h_idx)
    sec_end = html.index('</section>', h_idx) + len('</section>')
    return sec_start, sec_end

bat_start, bat_end = section_bounds(html, "Bateo — WAR ofensivo")
pit_start, pit_end = section_bounds(html, "Pitcheo — WAR de lanzadores")
liga_start, liga_end = section_bounds(html, "Clasificación completa — LMB 2026")

assert pit_start > bat_end, "expected pitching section right after batting section"
assert liga_start > pit_end, "expected liga section right after pitching section"

piratas_block = html[bat_start:pit_end]           # both Piratas sections, contiguous
liga_block = html[liga_start:liga_end]

# Sanity: make sure nothing else sits between bat_end/pit_start and pit_end/liga_start except whitespace
assert html[bat_end:pit_start].strip() == ""
assert html[pit_end:liga_start].strip() == ""

wrapped_piratas = (
    '<div id="tab-piratas" class="tab-panel active">\n' + piratas_block + '\n  </div>'
)
wrapped_liga = (
    '<div id="tab-liga" class="tab-panel">\n' + liga_block + '\n  </div>'
)

tab_nav = '''  <div class="tabs" role="tablist">
    <button class="tab-btn active" data-tab="piratas" role="tab" aria-selected="true" type="button">Piratas de Campeche</button>
    <button class="tab-btn" data-tab="liga" role="tab" aria-selected="false" type="button">Toda la liga — LMB 2026</button>
  </div>

'''

# Replace the whole span from bat_start to liga_end with: tab nav + wrapped piratas + wrapped liga
new_middle = tab_nav + wrapped_piratas + '\n\n' + wrapped_liga
html = html[:bat_start] + new_middle + html[liga_end:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Tabs wrapped. New length:", len(html))
