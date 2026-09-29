import json, math

SCRATCH = r"C:\Users\hp\AppData\Local\Temp\claude\C--Users-hp-OneDrive-LMB\c0469d6e-2a04-4c8f-8fd5-56fa18603191\scratchpad"

with open(f"{SCRATCH}\\piratas_hit.json", encoding="utf-8") as f:
    hitters = json.load(f)
with open(f"{SCRATCH}\\piratas_pit.json", encoding="utf-8") as f:
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

# ---------- League context (from QUALIFIED league-wide sample, 2026 regular season) ----------
h = lg["h"]
p = lg["p"]

lg_1B = h["H"] - h["D"] - h["T"] - h["HR"]
wBB, wHBP, w1B, w2B, w3B, wHR = 0.69, 0.72, 0.89, 1.27, 1.62, 2.10
lg_num = (wBB*h["BB"] + wHBP*h["HBP"] + w1B*lg_1B + w2B*h["D"] + w3B*h["T"] + wHR*h["HR"])
lg_den = (h["AB"] + h["BB"] - h["IBB"] + h["SF"] + h["HBP"])
LG_WOBA = lg_num / lg_den
WOBA_SCALE = 1.20          # NOT re-derived for the LMB -- needs base-out run-expectancy (play-
                           # by-play) data this API doesn't expose. Flagged as an open import.

# ---- Runs per win, derived from REAL LMB 2026 team-level scoring (not MLB's flat 10.0) ----
# Tango's formula (from "The Book"): RPW = 10 * sqrt(combined runs/game / 9), where 9 = the
# MLB reference of ~4.5 runs/team/game each way. LMB scores meaningfully more (see below),
# so its RPW is measurably higher than 10 -- each individual run matters a bit less toward a
# win when the whole league is scoring more.
lg_team_games = sum(t["G"] + t["P"] for t in standings)
lg_team_runs = sum(t["CA"] for t in standings)
LG_RUNS_PER_TEAM_GAME = lg_team_runs / lg_team_games          # ~5.42 runs/team/game (vs MLB's ~4.5)
RUNS_PER_WIN = 10.0 * math.sqrt((2 * LG_RUNS_PER_TEAM_GAME) / 9.0)   # ~10.97, not MLB's flat 10.0

# ---- Replacement level, imported as a WINS quantity (not a runs quantity) and converted to
# runs using the *LMB's own* RUNS_PER_WIN above. The literature's "~2.0 wins below average per
# full-time season role" is still an MLB-derived assumption (unvalidated for LMB's talent
# pool/roster depth -- flagged, not fixed), but the RUNS-per-PA rate that represents converts
# correctly to this league's higher-scoring environment instead of dragging in MLB's RPW=10.
# INTENTO DE RECALIBRACION 20-ago-2026 -- PROBADO Y REVERTIDO, ver seccion 8.2/8.3 del README.
# Se encontro (regresionando victorias reales vs WAR combinado de las 20 novenas) que el nivel
# de reemplazo A NIVEL EQUIPO que mejor ajusta es 31.3 victorias/93 juegos, no las 28 asumidas.
# Se intento reescalar REPL_WINS_REFERENCE proporcionalmente (2.0 -> 1.644, via la razon de
# brechas promedio-reemplazo) para que el WAR individual fuera consistente con eso. Al volver a
# correr la regresion CON la formula ya recalibrada, el intercepto se movio de 31.3 a 35.2 en vez
# de estabilizarse -- osea, el "punto fijo" no converge con solo 20 equipos de datos. Ademas, el
# R^2 de la regresion NO cambia (0.675 en ambos casos): cambiar este numero no reduce nada de la
# varianza sin explicar, solo reetiqueta donde esta el cero. Por eso se REVIRTIO a 2.0 -- aplicar
# el cambio no habria hecho el modelo mas preciso, solo distinto. Sigue documentado como hallazgo
# de validacion (ver dashboard), pero NO como correccion aplicada al WAR individual.
REPL_WINS_REFERENCE = 2.0             # revertido a su valor original -- ver nota arriba
REPL_RUNS_PER_600PA = REPL_WINS_REFERENCE * RUNS_PER_WIN   # ~21.9, replaces MLB's flat 20.0

POS_ADJ_PER_600 = {
    "C": 12.5, "SS": 7.5, "2B": 2.5, "3B": 2.5, "CF": 2.5,
    "LF": -7.5, "RF": -7.5, "1B": -12.5, "DH": -17.5, "X": 0.0, "OF": -2.5,
}

lg_ip = p["outs"] / 3.0
LG_ERA = p["ER"] * 9 / lg_ip
LG_RA9 = p["R"] * 9 / lg_ip
lg_fip_raw = (13*p["HR"] + 3*(p["BB"] + p["HBP"] - p["IBB"]) - 2*p["K"]) / lg_ip
FIP_CONSTANT = LG_ERA - lg_fip_raw   # calibrated directly from this league's own run environment
LG_FIP = lg_fip_raw + FIP_CONSTANT

# Pitching replacement level, on the SAME wins-based convention as batting above (an average
# full-time starter over a 200-IP MLB-reference workload is worth the same +2.0 wins as an
# average full-time hitter over 600 PA) -- replaces the earlier ad hoc "FIP x 1.15" multiplier,
# which had no such grounding and was inconsistent with the batting side's replacement level.
REPL_FIP_GAP = (REPL_WINS_REFERENCE * RUNS_PER_WIN * 9) / 200.0   # runs of FIP above league avg

# League OBP / SLG (for OPS+), derived from the same qualified-hitter sample
LG_TB = h["H"] + h["D"] + 2*h["T"] + 3*h["HR"]
LG_OBP = (h["H"] + h["BB"] + h["HBP"]) / (h["AB"] + h["BB"] + h["HBP"] + h["SF"])
LG_SLG = LG_TB / h["AB"]

# "WAR+" is NOT an official/standard stat (unlike OPS+ or ERA+). It is a playing-time-
# normalized index of our own construction: it compares each player's WAR-per-PA (or
# WAR-per-IP) rate against a fixed "average full-time player" rate, scaled to 100.
#
# LMB's regular season is ~92-93 team games (confirmed from lmb.com.mx/posiciones,
# Aug 2026: Piratas 52-41 = 93 GP), NOT MLB's 162 -- so a real LMB "full season" tops
# out around 420 PA / 100 IP (the actual 2026 league leaders: Yonathan Daza / Magneuris
# Sierra at 422 PA in 88 G; Odrisamer Despaigne at 106.1 IP in 18 starts), not MLB's
# 600 PA / 200 IP. PA_FULL and IP_FULL below use those LMB-real numbers so the
# methodology text reads honestly for this league.
#
# Note: because WAR_PLUS_ANCHOR is scaled down in the same proportion as PA_FULL/IP_FULL
# (600->420 needs 2.0->1.4, 200->100 needs 2.0->1.0), the *rate* being compared -- and
# therefore every WAR+ number this produces -- is mathematically identical either way.
# What's fixed here is the label/framing, not the output. What's still an unadapted
# MLB import (and NOT independently derived for the LMB) is the underlying rate itself:
# "2.0 WAR per 600 PA" as the definition of a league-average regular. Confirming that
# rate for the LMB would require computing WAR for the full league sample, not just
# Piratas -- flagged in the caveats below, not fixed here.
PA_FULL = 420          # real 2026 LMB PA leaders' range (Daza/Sierra), not MLB's 600
IP_FULL = 100          # real 2026 LMB IP leaders' range (Despaigne ~106), not MLB's 200
WAR_PLUS_ANCHOR_BAT = 2.0 * (PA_FULL / 600.0)   # = 1.4, proportionally rescaled from MLB's 2.0/600
WAR_PLUS_ANCHOR_PIT = 2.0 * (IP_FULL / 200.0)   # = 1.0, proportionally rescaled from MLB's 2.0/200

# ---------- Batting WAR ----------
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
        "name": pl["name"], "position": pos, "PA": int(PA), "AVG": pl.get("PRO"),
        "OBP": pl.get("OBP"), "SLG": pl.get("SLG"), "OPS": pl.get("OPS"),
        "HR": int(HR), "wOBA": round(woba, 3), "wRAA": round(wraa, 1),
        "wSB": round(wsb, 1), "posAdj": round(pos_adj, 1), "replRuns": round(repl, 1),
        "battingRuns": round(batting_runs, 1), "WAR": round(war, 2),
        "OPSplus": round(ops_plus), "WARplus": round(war_plus),
    })

bat_results.sort(key=lambda x: -x["WAR"])

# ---------- Pitching WAR ----------
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
    R = num(pl.get("C"))

    fip = (13*HR + 3*(BB + HBP - IBB) - 2*K) / IP + FIP_CONSTANT
    era = ER * 9 / IP
    repl_fip = LG_FIP + REPL_FIP_GAP
    raa = (repl_fip - fip) * (IP/9.0)
    war = raa / RUNS_PER_WIN

    era_plus = 100 * LG_ERA / max(era, 0.10)   # floored to avoid divide-by-zero on 0.00 ERA in tiny samples
    era_plus = min(era_plus, 999)
    war_plus = 100 * (war/IP*IP_FULL) / WAR_PLUS_ANCHOR_PIT

    pit_results.append({
        "name": pl["name"], "IP": round(IP, 1), "ERA": pl.get("EFE"),
        "WHIP": pl.get("WHIP"), "K": int(K), "BB": int(BB), "HR": int(HR),
        "W": int(num(pl.get("JG"))), "L": int(num(pl.get("JP"))), "SV": int(num(pl.get("JS"))),
        "FIP": round(fip, 2), "raa": round(raa, 1), "WAR": round(war, 2),
        "ERAplus": round(era_plus), "WARplus": round(war_plus),
    })

pit_results.sort(key=lambda x: -x["WAR"])

out = {
    "generated_note": "Snapshot LMB 2026, temporada regular, vía lmb.com.mx/estadisticas (API interna /estadisticas/api/player)",
    "league_context": {
        "lgWOBA": round(LG_WOBA, 4), "wobaScale": WOBA_SCALE, "runsPerWin": round(RUNS_PER_WIN, 3),
        "lgRunsPerTeamGame": round(LG_RUNS_PER_TEAM_GAME, 3), "lgTeamGames": lg_team_games,
        "replWinsReference": REPL_WINS_REFERENCE, "replRunsPer600PA": round(REPL_RUNS_PER_600PA, 2),
        "lgERA": round(LG_ERA, 3), "lgRA9": round(LG_RA9, 3), "lgFIP": round(LG_FIP, 3),
        "fipConstant": round(FIP_CONSTANT, 3), "replFipGap": round(REPL_FIP_GAP, 3),
        "lgOBP": round(LG_OBP, 4), "lgSLG": round(LG_SLG, 4),
        "paFull": PA_FULL, "ipFull": IP_FULL,
        "warPlusAnchorBat": WAR_PLUS_ANCHOR_BAT, "warPlusAnchorPit": WAR_PLUS_ANCHOR_PIT,
        "hitting_qualified_n": lg["hitting_qualified_n"], "pitching_qualified_n": lg["pitching_qualified_n"],
    },
    "batting": bat_results,
    "pitching": pit_results,
}

with open(f"{SCRATCH}\\war_output.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("LG_WOBA", LG_WOBA, "LG_OBP", LG_OBP, "LG_SLG", LG_SLG)
print("LG_ERA", LG_ERA, "LG_RA9", LG_RA9, "LG_FIP", LG_FIP, "FIP_CONSTANT", FIP_CONSTANT)
print("LG_RUNS_PER_TEAM_GAME", LG_RUNS_PER_TEAM_GAME, "over", lg_team_games, "team-games")
print("RUNS_PER_WIN", RUNS_PER_WIN, "(vs MLB's flat 10.0)")
print("REPL_RUNS_PER_600PA", REPL_RUNS_PER_600PA, "(vs MLB's flat 20.0)")
print("REPL_FIP_GAP", REPL_FIP_GAP, "-> repl_fip =", LG_FIP + REPL_FIP_GAP, "(vs old ad hoc LG_FIP*1.15 =", LG_FIP*1.15, ")")
print("Top 5 batting WAR (WAR / OPS+ / WAR+):")
for r in bat_results[:5]:
    print(" ", r["name"], r["position"], r["WAR"], r["OPSplus"], r["WARplus"])
print("Top 5 pitching WAR (WAR / ERA+ / WAR+):")
for r in pit_results[:5]:
    print(" ", r["name"], r["WAR"], r["ERAplus"], r["WARplus"])
print("Total batters:", len(bat_results), "Total pitchers:", len(pit_results))
