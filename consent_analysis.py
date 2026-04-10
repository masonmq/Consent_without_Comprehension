import pandas as pd
import numpy as np
import json, ast

CSV_PATH = ""
GROUP_COL = "group"
CONSENT_COL = "consent"
INIT_ANS_COL = "initial_answers"
RETRY_ANS_COL = "retry_answers"

RETAKE_GROUPS = {2, 3, 5}
NONRETAKE_GROUPS = {0, 1, 4}
N_Q = 6
THRESH = 0.80

def normalize_group(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if s.upper().startswith("G"):
        s = s[1:]
    return int(float(s))

def parse_consent(x):
    if pd.isna(x): return np.nan
    if isinstance(x, bool): return x
    s = str(x).strip().lower()
    if s in {"true","t","1","yes","y"}: return True
    if s in {"false","f","0","no","n"}: return False
    try:
        v = ast.literal_eval(str(x))
        return v if isinstance(v, bool) else np.nan
    except Exception:
        return np.nan

def parse_bool_list(s):
    if pd.isna(s): return None
    s = str(s).strip()
    if s == "" or s.lower() in {"nan","none"}: return None
    try:
        out = json.loads(s)
        if isinstance(out, list):
            return [bool(x) for x in out]
    except Exception:
        pass
    try:
        s2 = s.replace("true","True").replace("false","False")
        out = ast.literal_eval(s2)
        if isinstance(out, list):
            return [bool(x) for x in out]
    except Exception:
        pass
    return None

def first6(lst):
    if lst is None or len(lst) < N_Q: return None
    return lst[:N_Q]

def acc(lst6):
    if lst6 is None: return np.nan
    return float(np.mean(np.array(lst6, dtype=bool)))

df = pd.read_csv(CSV_PATH)
df["group_int"] = df[GROUP_COL].apply(normalize_group)
df["group"] = df["group_int"].apply(lambda g: f"G{g}")
df["consent_bool"] = df[CONSENT_COL].apply(parse_consent)

df["init_list"] = df[INIT_ANS_COL].apply(parse_bool_list).apply(first6)
df["acc1"] = df["init_list"].apply(acc)
df["pass1"] = df["acc1"] >= THRESH

if RETRY_ANS_COL in df.columns:
    df["retry_list"] = df[RETRY_ANS_COL].apply(parse_bool_list).apply(first6)
    df["acc2"] = df["retry_list"].apply(acc)
    df["pass2"] = df["acc2"] >= THRESH
else:
    df["acc2"] = np.nan
    df["pass2"] = False

df["eligible"] = df.apply(
    lambda r: (r["pass1"] if r["group_int"] in NONRETAKE_GROUPS else (r["pass1"] or r["pass2"])),
    axis=1
)

# --------- (1) Consent among eligible ----------
eligible = df[df["eligible"] & df["consent_bool"].isin([True, False])].copy()

rows = []
for g in ["G0","G1","G2","G3","G4","G5"]:
    sub = eligible[eligible["group"] == g]
    yes = int((sub["consent_bool"] == True).sum())
    no  = int((sub["consent_bool"] == False).sum())
    denom = yes + no
    rate = (100.0 * yes / denom) if denom > 0 else np.nan
    rows.append([g, denom, yes, no, f"{rate:.1f}%" if denom > 0 else "--"])

eligible_yes = int((eligible["consent_bool"] == True).sum())
eligible_no  = int((eligible["consent_bool"] == False).sum())
eligible_den = eligible_yes + eligible_no
eligible_rate = 100.0 * eligible_yes / eligible_den

print("\nConsent among eligible (universal definition):")
print("group  eligible_n  consent_yes  consent_no  consent_yes_rate")
for r in rows:
    print(f"{r[0]:>3} {r[1]:>11} {r[2]:>12} {r[3]:>10} {r[4]:>16}")
print(f"Pooled eligible: n={eligible_den}, yes={eligible_yes}, no={eligible_no}, rate={eligible_rate:.1f}%")

# --------- (2) Non-gated groups: fail-but-consent ---------
nongated_fail = df[
    df["group_int"].isin(NONRETAKE_GROUPS) &
    (~df["pass1"]) &
    df["consent_bool"].isin([True, False])
].copy()

rows2 = []
for g in ["G0","G1","G4"]:
    sub = nongated_fail[nongated_fail["group"] == g]
    yes = int((sub["consent_bool"] == True).sum())
    no  = int((sub["consent_bool"] == False).sum())
    denom = yes + no
    rate = (100.0 * yes / denom) if denom > 0 else np.nan
    rows2.append([g, denom, yes, no, f"{rate:.1f}%" if denom > 0 else "--"])

fail_yes = int((nongated_fail["consent_bool"] == True).sum())
fail_no  = int((nongated_fail["consent_bool"] == False).sum())
fail_den = fail_yes + fail_no
fail_rate = 100.0 * fail_yes / fail_den

print("\nNon-gated groups (G0,G1,G4): consent despite failing (<80% on first quiz):")
print("group  fail_n  consent_yes  consent_no  consent_yes_rate")
for r in rows2:
    print(f"{r[0]:>3} {r[1]:>7} {r[2]:>12} {r[3]:>10} {r[4]:>16}")
print(f"Pooled non-gated fail: n={fail_den}, yes={fail_yes}, no={fail_no}, rate={fail_rate:.1f}%")

print("\nQuick comparison (different denominators, interpret carefully):")
print(f"  Pooled eligible consent rate (all groups): {eligible_rate:.1f}% ({eligible_yes}/{eligible_den})")
print(f"  Pooled fail-but-consent (non-gated only):  {fail_rate:.1f}% ({fail_yes}/{fail_den})")