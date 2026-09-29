import json, math

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\c0469d6e-2a04-4c8f-8fd5-56fa18603191\scratchpad"

with open(f"{SCRATCH}\\liga_hit.json", encoding="utf-8") as f:
    hitters = json.load(f)
with open(f"{SCRATCH}\\liga_pit.json", encoding="utf-8") as f:
    pitchers = json.load(f)
with open(f"{SCRATCH}\\league_agg.json", encoding="utf-8") as f:
    lg = json.load(f)
with open(f"{SCRATCH}\\league_standings.json", encoding="utf-8") as f:
    standings = json.load(f)["teams"]

def num(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("-.--", ".---", "", "---"):
        return 0.0
    if s.startswith("."):
        s = "0" + s
    try:
        return float(s)
    except ValueError:
        return 0.0

def ip_to_innings(ip_str):
    s = str(ip_str)
    if "." in s:
        whole, frac = s.split(".")
    else:
        whole, frac = s, "0"
    whole = int(whole or 0)
    frac = int(frac or 0)
    outs = whole * 3 + frac
    return outs / 3.0

# ---------- League context (identical derivation to the Piratas-only script -- same 130/49 sample) ----------
h = lg["h"]
p = lg["p"]

lg_1B = h["H"] - h["D"] - h["T"] - h["HR"]
wBB, wHBP, w1B, w2B, w3B, wHR = 0.69, 0.72, 0.89, 1.27, 1.62, 2.10
lg_num = (wBB*h["BB"] + wHBP*h["HBP"] + w1B*lg_1B + w2B*h["D"] + w3B*h["T"] + wHR*h["HR"])
lg_den = (h["AB"] + h["BB"] - h["IBB"] + h["SF"] + h["HBP"])
LG_WOBA = lg_num / lg_den
WOBA_SCALE = 1.20

lg_team_games = sum(t["G"] + t["P"] for t in standings)
lg_team_runs = sum(t["CA"] for t in standings)
LG_RUNS_PER_TEAM_GAME = lg_team_runs / lg_team_games
RUNS_PER_WIN = 10.0 * math.sqrt((2 * LG_RUNS_PER_TEAM_GAME) / 9.0)

# Se probo recalibrar esto a 1.644 (20-ago-2026) y se revirtio -- ver nota completa en
# compute_war.py y seccion 8.2/8.3 del README. No mejoraba el modelo (mismo R^2), y el "punto
# fijo" no converge con solo 20 equipos de datos.
REPL_WINS_REFERENCE = 2.0
REPL_RUNS_PER_600PA = REPL_WINS_REFERENCE * RUNS_PER_WIN

POS_ADJ_PER_600 = {
    "C": 12.5, "SS": 7.5, "2B": 2.5, "3B": 2.5, "CF": 2.5,
    "LF": -7.5, "RF": -7.5, "1B": -12.5, "DH": -17.5, "X": 0.0, "OF": -2.5,
}

lg_ip = p["outs"] / 3.0
LG_ERA = p["ER"] * 9 / lg_ip
lg_fip_raw = (13*p["HR"] + 3*(p["BB"] + p["HBP"] - p["IBB"]) - 2*p["K"]) / lg_ip
FIP_CONSTANT = LG_ERA - lg_fip_raw
LG_FIP = lg_fip_raw + FIP_CONSTANT
REPL_FIP_GAP = (REPL_WINS_REFERENCE * RUNS_PER_WIN * 9) / 200.0

LG_TB = h["H"] + h["D"] + 2*h["T"] + 3*h["HR"]
LG_OBP = (h["H"] + h["BB"] + h["HBP"]) / (h["AB"] + h["BB"] + h["HBP"] + h["SF"])
LG_SLG = LG_TB / h["AB"]

PA_FULL = 420
IP_FULL = 100
WAR_PLUS_ANCHOR_BAT = REPL_WINS_REFERENCE * (PA_FULL / 600.0)
WAR_PLUS_ANCHOR_PIT = REPL_WINS_REFERENCE * (IP_FULL / 200.0)

PIRATAS_HIT_TEAM = "Piratas"

# ---------- Batting WAR, whole league ----------
bat_results = []
for pl in hitters:
    PA = num(pl.get("VB"))
    AB = num(pl.get("TB"))
    BB = num(pl.get("BB"))
    HBP = num(pl.get("HBP"))
    H_ = num(pl.get("H"))
    D = num(pl.get("2B"))
    T = num(pl.get("3B"))
    HR = num(pl.get("HR"))
    SF = num(pl.get("ES"))
    IBB = num(pl.get("IBB"))
    SB = num(pl.get("BR"))
    CS = num(pl.get("AR"))
    singles = H_ - D - T - HR
    if PA <= 0:
        continue

    num_ = wBB*BB + wHBP*HBP + w1B*singles + w2B*D + w3B*T + wHR*HR
    den_ = AB + BB - IBB + SF + HBP
    woba = (num_ / den_) if den_ > 0 else 0.0

    wraa = ((woba - LG_WOBA) / WOBA_SCALE) * PA
    wsb = SB*0.2 - CS*0.4
    pos = pl.get("position", "X")
    pos_adj = POS_ADJ_PER_600.get(pos, 0.0) * (PA/600.0)
    repl = REPL_RUNS_PER_600PA * (PA/600.0)

    batting_runs = wraa + wsb + pos_adj + repl
    war = batting_runs / RUNS_PER_WIN

    obp_p = (H_ + BB + HBP) / (AB + BB + HBP + SF) if (AB + BB + HBP + SF) > 0 else 0.0
    tb_p = H_ + D + 2*T + 3*HR
    slg_p = tb_p / AB if AB > 0 else 0.0
    ops_plus = 100 * (obp_p/LG_OBP + slg_p/LG_SLG - 1)
    war_plus = 100 * (war/PA*PA_FULL) / WAR_PLUS_ANCHOR_BAT

    bat_results.append({
        "name": pl["name"], "position": pos, "team": pl.get("team", "").strip(),
        "isPiratas": pl.get("team", "").strip() == PIRATAS_HIT_TEAM,
        "PA": int(PA), "AVG": pl.get("PRO"), "OBP": pl.get("OBP"), "SLG": pl.get("SLG"), "OPS": pl.get("OPS"),
        "HR": int(HR), "wOBA": round(woba, 3), "battingRuns": round(batting_runs, 1), "WAR": round(war, 2),
        "OPSplus": round(ops_plus), "WARplus": round(war_plus),
    })

bat_results.sort(key=lambda x: -x["WAR"])
for i, r in enumerate(bat_results, 1):
    r["rank"] = i

# ---------- Pitching WAR, whole league ----------
pit_results = []
for pl in pitchers:
    IP = ip_to_innings(pl.get("IL", "0.0"))
    if IP <= 0:
        continue
    HR = num(pl.get("HR"))
    BB = num(pl.get("BB"))
    HBP = num(pl.get("GP"))
    IBB = num(pl.get("IBB"))
    K = num(pl.get("P"))
    ER = num(pl.get("CL"))

    fip = (13*HR + 3*(BB + HBP - IBB) - 2*K) / IP + FIP_CONSTANT
    era = ER * 9 / IP
    repl_fip = LG_FIP + REPL_FIP_GAP
    raa = (repl_fip - fip) * (IP/9.0)
    war = raa / RUNS_PER_WIN

    era_plus = min(100 * LG_ERA / max(era, 0.10), 999)
    war_plus = 100 * (war/IP*IP_FULL) / WAR_PLUS_ANCHOR_PIT

    pit_results.append({
        "name": pl["name"], "team": pl.get("team", "").strip(), "isPiratas": False,
        "IP": round(IP, 1), "ERA": pl.get("EFE"), "WHIP": pl.get("WHIP"),
        "K": int(K), "BB": int(BB), "W": int(num(pl.get("JG"))), "L": int(num(pl.get("JP"))),
        "FIP": round(fip, 2), "WAR": round(war, 2), "ERAplus": round(era_plus), "WARplus": round(war_plus),
    })

pit_results.sort(key=lambda x: -x["WAR"])
for i, r in enumerate(pit_results, 1):
    r["rank"] = i

# ---------- Validate the "2.0 wins = average full-time regular" assumption ----------
# Empirically: for players with PA >= 300 (genuine regulars, not part-timers), what is the
# real average WAR/600PA in this league's own qualified sample?
regulars = [r for r in bat_results if r["PA"] >= 300]
avg_rate_600 = sum((r["WAR"]/r["PA"])*600 for r in regulars) / len(regulars) if regulars else 0
# Also a PA-weighted version (compilers count more)
tot_war = sum(r["WAR"] for r in regulars)
tot_pa = sum(r["PA"] for r in regulars)
pa_weighted_rate_600 = (tot_war/tot_pa)*600 if tot_pa else 0

pit_regulars = [r for r in pit_results if r["IP"] >= 60]
avg_pit_rate_200 = sum((r["WAR"]/r["IP"])*200 for r in pit_regulars) / len(pit_regulars) if pit_regulars else 0
tot_pwar = sum(r["WAR"] for r in pit_regulars)
tot_pip = sum(r["IP"] for r in pit_regulars)
pa_weighted_pit_rate_200 = (tot_pwar/tot_pip)*200 if tot_pip else 0

out = {
    "league_context": {
        "lgWOBA": round(LG_WOBA, 4), "runsPerWin": round(RUNS_PER_WIN, 3),
        "replRunsPer600PA": round(REPL_RUNS_PER_600PA, 2), "lgOBP": round(LG_OBP, 4), "lgSLG": round(LG_SLG, 4),
        "lgERA": round(LG_ERA, 3), "lgFIP": round(LG_FIP, 3), "fipConstant": round(FIP_CONSTANT, 3),
        "replFipGap": round(REPL_FIP_GAP, 3), "paFull": PA_FULL, "ipFull": IP_FULL,
    },
    "validation": {
        "n_regulars_bat_ge300PA": len(regulars),
        "avg_war_per_600pa_simple": round(avg_rate_600, 3),
        "avg_war_per_600pa_pa_weighted": round(pa_weighted_rate_600, 3),
        "n_regulars_pit_ge60IP": len(pit_regulars),
        "avg_war_per_200ip_simple": round(avg_pit_rate_200, 3),
        "avg_war_per_200ip_ip_weighted": round(pa_weighted_pit_rate_200, 3),
        "assumed_repl_wins_reference": REPL_WINS_REFERENCE,
    },
    "batting": bat_results,
    "pitching": pit_results,
}

with open(f"{SCRATCH}\\war_liga_output.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("=== VALIDATION: is '2.0 WAR/600PA = average regular' right for the LMB? ===")
print(f"Batters with PA>=300 (n={len(regulars)}): simple avg WAR/600PA = {avg_rate_600:.3f}, PA-weighted = {pa_weighted_rate_600:.3f}")
print(f"(we assumed {REPL_WINS_REFERENCE} as the anchor)")
print(f"Pitchers with IP>=60 (n={len(pit_regulars)}): simple avg WAR/200IP = {avg_pit_rate_200:.3f}, IP-weighted = {pa_weighted_pit_rate_200:.3f}")
print()
print("=== TOP 10 BATTING WAR, WHOLE LEAGUE ===")
for r in bat_results[:10]:
    tag = " <== PIRATAS" if r["isPiratas"] else ""
    print(f"  {r['rank']:3} {r['name']:25} {r['team']:15} {r['position']:3} WAR={r['WAR']:+.2f}{tag}")
print()
print("=== PIRATAS BATTERS IN LEAGUE-WIDE RANKING ===")
for r in bat_results:
    if r["isPiratas"]:
        print(f"  #{r['rank']:3}/{len(bat_results)}  {r['name']:25} WAR={r['WAR']:+.2f}  OPS+={r['OPSplus']}  WAR+={r['WARplus']}")
print()
print("=== TOP 10 PITCHING WAR, WHOLE LEAGUE (qualified only -- no Piratas pitcher qualifies) ===")
for r in pit_results[:10]:
    print(f"  {r['rank']:3} {r['name']:25} {r['team']:25} WAR={r['WAR']:+.2f}")
print()
print("Total batters:", len(bat_results), "Total pitchers:", len(pit_results))
