# -*- coding: utf-8 -*-
import json

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\6b28ae4f-0eed-4aa2-9355-9c43acfd998c\scratchpad"
HTML_PATH = f"{SCRATCH}\\piratas_war.html"

with open(f"{SCRATCH}\\league_agg.json", encoding="utf-8") as f:
    lg = json.load(f)
h = lg["h"]

wBB, wHBP, w1B, w2B, w3B, wHR = 0.69, 0.72, 0.89, 1.27, 1.62, 2.10
lg_1B = h["H"] - h["D"] - h["T"] - h["HR"]
num = wBB*h["BB"] + wHBP*h["HBP"] + w1B*lg_1B + w2B*h["D"] + w3B*h["T"] + wHR*h["HR"]
den = h["AB"] + h["BB"] - h["IBB"] + h["SF"] + h["HBP"]
LG_WOBA = num / den
WOBA_SCALE = 1.20
LG_R_PER_PA = h["R"] / h["PA"]

print("LG_WOBA:", LG_WOBA, "LG_R_PER_PA:", LG_R_PER_PA)

with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

def add_wrcplus_to_array(html, var_name):
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
        woba = entry["wOBA"]
        rate = (woba - LG_WOBA) / WOBA_SCALE + LG_R_PER_PA
        wrc_plus = 100 * rate / LG_R_PER_PA
        entry["wRCplus"] = round(wrc_plus)
    new_text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return html[:arr_start] + new_text + html[arr_end:], data

html, bat_data = add_wrcplus_to_array(html, "BATTING")
html, liga_bat_data = add_wrcplus_to_array(html, "LIGA_BATTING")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("\nTop 5 Piratas by wRC+:")
for r in sorted(bat_data, key=lambda x: -x["wRCplus"])[:5]:
    print(" ", r["name"], r["wRCplus"], "WAR=", r["WAR"])

print("\nTop 5 league by wRC+:")
for r in sorted(liga_bat_data, key=lambda x: -x["wRCplus"])[:5]:
    print(" ", r["name"], r["wRCplus"], "WAR=", r["WAR"])

# Sanity check: PA-weighted average wRC+ of the qualified league sample should land near 100
tot_pa = sum(r["PA"] for r in liga_bat_data)
weighted_avg = sum(r["wRCplus"]*r["PA"] for r in liga_bat_data) / tot_pa
print("\nPA-weighted average wRC+ (league qualified sample):", weighted_avg)
print("Saved. Constants used -> LG_WOBA:", round(LG_WOBA,4), "WOBA_SCALE:", WOBA_SCALE, "LG_R_PER_PA:", round(LG_R_PER_PA,4))
