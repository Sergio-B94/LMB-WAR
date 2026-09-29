# -*- coding: utf-8 -*-
import json

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\6b28ae4f-0eed-4aa2-9355-9c43acfd998c\scratchpad"
HTML_PATH = f"{SCRATCH}\\piratas_war.html"

with open(f"{SCRATCH}\\name_to_code.json", encoding="utf-8") as f:
    name_to_code = json.load(f)

with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

def replace_flags_in_array(html, var_name):
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
    arr_text = html[arr_start:arr_end]
    data = json.loads(arr_text)
    n = 0
    for entry in data:
        code = name_to_code.get(entry["name"])
        if code:
            entry["flag"] = code
            n += 1
        elif "flag" in entry:
            del entry["flag"]
    new_arr_text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    new_html = html[:arr_start] + new_arr_text + html[arr_end:]
    return new_html, n, len(data)

for var_name in ["BATTING", "PITCHING", "LIGA_BATTING", "LIGA_PITCHING"]:
    html, matched, total = replace_flags_in_array(html, var_name)
    print(f"{var_name}: {matched}/{total} now have a country code")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print("Saved. New length:", len(html))
