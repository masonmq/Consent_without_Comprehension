import pandas as pd
import numpy as np
import json
import ast

CSV_PATH = ""

GROUP_COL = "group"           
INIT_COL  = "initial_answers"
RETRY_COL = "retry_answers"

KEEP_GROUPS = {2, 3, 5}
N_Q = 6  


def normalize_group(x):
    """Map group labels like 'G2', 2, '2', '2.0' -> int 2."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s.upper().startswith("G"):
        s = s[1:]
    try:
        return int(float(s))
    except Exception:
        return np.nan


def parse_bool_list(s):

    if pd.isna(s):
        return None
    s = str(s).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return None

    try:
        out = json.loads(s)
        if isinstance(out, list):
            return out
    except Exception:
        pass

    try:
        s2 = s.replace("true", "True").replace("false", "False")
        out = ast.literal_eval(s2)
        if isinstance(out, list):
            return out
    except Exception:
        pass

    return None


def first6(lst):

    if lst is None or not isinstance(lst, list):
        return None
    if len(lst) < N_Q:
        return None
    return lst[:N_Q]


def compute_row_metrics(init6, retry6):
    """
    Compute per-participant error dynamics:
      - corrected: wrong->correct
      - backslide: correct->wrong
      - persistent_wrong: wrong->wrong
      - stable_correct: correct->correct
      - correction_rate among initially-wrong items
      - backslide_rate among initially-correct items
      - persistent_wrong_rate among initially-wrong items
      - net_change = corrected - backslide
    """
    init6 = np.array(init6, dtype=bool)
    retry6 = np.array(retry6, dtype=bool)

    wrong1 = (~init6).sum()
    correct1 = init6.sum()

    corrected = ((~init6) & (retry6)).sum()
    backslide = ((init6) & (~retry6)).sum()
    persistent_wrong = ((~init6) & (~retry6)).sum()
    stable_correct = ((init6) & (retry6)).sum()

    correction_rate = corrected / wrong1 if wrong1 > 0 else np.nan
    backslide_rate = backslide / correct1 if correct1 > 0 else np.nan
    persistent_wrong_rate = persistent_wrong / wrong1 if wrong1 > 0 else np.nan

    acc1 = correct1 / N_Q
    acc2 = retry6.sum() / N_Q
    net_change = int(corrected) - int(backslide)

    return {
        "wrong1": int(wrong1),
        "correct1": int(correct1),
        "corrected": int(corrected),
        "backslide": int(backslide),
        "persistent_wrong": int(persistent_wrong),
        "stable_correct": int(stable_correct),
        "correction_rate": correction_rate,
        "backslide_rate": backslide_rate,
        "persistent_wrong_rate": persistent_wrong_rate,
        "net_change": net_change,
        "acc1": acc1,
        "acc2": acc2,
    }


def summarize_group(df_g):
    n = len(df_g)
    total_items = n * N_Q

    # Totals across all items
    tot_corrected = df_g["corrected"].sum()
    tot_backslide = df_g["backslide"].sum()
    tot_persistent_wrong = df_g["persistent_wrong"].sum()
    tot_stable_correct = df_g["stable_correct"].sum()

    tot_wrong1 = df_g["wrong1"].sum()
    tot_correct1 = df_g["correct1"].sum()

    # Aggregate rates (weighted by available denominators)
    corr_rate_weighted = (tot_corrected / tot_wrong1) if tot_wrong1 > 0 else np.nan
    back_rate_weighted = (tot_backslide / tot_correct1) if tot_correct1 > 0 else np.nan
    pers_wrong_rate_weighted = (tot_persistent_wrong / tot_wrong1) if tot_wrong1 > 0 else np.nan

    mean_corr_rate = df_g["correction_rate"].mean(skipna=True)
    mean_back_rate = df_g["backslide_rate"].mean(skipna=True)
    mean_pers_wrong_rate = df_g["persistent_wrong_rate"].mean(skipna=True)

    median_net = df_g["net_change"].median()
    mean_acc1 = df_g["acc1"].mean()
    mean_acc2 = df_g["acc2"].mean()

    return {
        "retakers_n": n,
        "items_total": total_items,
        "corrected_total": int(tot_corrected),
        "backslide_total": int(tot_backslide),
        "persistent_wrong_total": int(tot_persistent_wrong),
        "stable_correct_total": int(tot_stable_correct),
        "corr_rate_weighted": corr_rate_weighted,              # corrected / initially-wrong (pooled)
        "backslide_rate_weighted": back_rate_weighted,         # backslide / initially-correct (pooled)
        "persistent_wrong_rate_weighted": pers_wrong_rate_weighted,
        "corr_rate_mean": mean_corr_rate,                      # mean across participants
        "backslide_rate_mean": mean_back_rate,
        "persistent_wrong_rate_mean": mean_pers_wrong_rate,
        "net_change_median": median_net,
        "acc1_mean_retakers": mean_acc1,
        "acc2_mean_retakers": mean_acc2,
    }


def per_item_transitions(df_rows):
    """
    Optional: per-question transition counts by group (still only first 6).
    Returns a tidy DataFrame with columns:
      group, q_idx, WC, CW, WW, CC
    """
    records = []
    for g, sub in df_rows.groupby("group_int"):
        # initialize counts
        counts = np.zeros((N_Q, 4), dtype=int)  # WC, CW, WW, CC
        for init6, retry6 in zip(sub["init6"], sub["retry6"]):
            init6 = np.array(init6, dtype=bool)
            retry6 = np.array(retry6, dtype=bool)
            wc = ((~init6) & (retry6)).astype(int)
            cw = ((init6) & (~retry6)).astype(int)
            ww = ((~init6) & (~retry6)).astype(int)
            cc = ((init6) & (retry6)).astype(int)
            counts[:, 0] += wc
            counts[:, 1] += cw
            counts[:, 2] += ww
            counts[:, 3] += cc

        for i in range(N_Q):
            records.append({
                "group": f"G{g}",
                "q_idx": i + 1,
                "W->C": int(counts[i, 0]),
                "C->W": int(counts[i, 1]),
                "W->W": int(counts[i, 2]),
                "C->C": int(counts[i, 3]),
            })
    return pd.DataFrame.from_records(records)


df = pd.read_csv(CSV_PATH)

# Normalize group
if GROUP_COL not in df.columns:
    raise KeyError(f"Expected group column '{GROUP_COL}' not found. Columns: {list(df.columns)}")

df["group_int"] = df[GROUP_COL].apply(normalize_group)
df = df[df["group_int"].isin(KEEP_GROUPS)].copy()

# Parse answers
if INIT_COL not in df.columns or RETRY_COL not in df.columns:
    raise KeyError(f"Expected columns '{INIT_COL}' and '{RETRY_COL}' not found. Columns: {list(df.columns)}")

df["init_list"] = df[INIT_COL].apply(parse_bool_list).apply(first6)
df["retry_list"] = df[RETRY_COL].apply(parse_bool_list).apply(first6)

# Keep only actual retakers: need both attempts present
df_ret = df[df["init_list"].notna() & df["retry_list"].notna()].copy()

# retaker counts
retaker_counts = df_ret.groupby("group_int").size().rename("retakers_n").reset_index()
retaker_counts["group"] = retaker_counts["group_int"].apply(lambda x: f"G{int(x)}")
retaker_counts = retaker_counts[["group", "retakers_n"]].sort_values("group")

print("\nSanity check: retaker counts by group (rows with valid initial+retry answer lists)")
print(retaker_counts.to_string(index=False))

# Compute per-row metrics
metrics = []
for init6, retry6 in zip(df_ret["init_list"], df_ret["retry_list"]):
    metrics.append(compute_row_metrics(init6, retry6))
m_df = pd.DataFrame(metrics)
df_ret = pd.concat([df_ret.reset_index(drop=True), m_df.reset_index(drop=True)], axis=1)

# Group summaries
summaries = []
for g, sub in df_ret.groupby("group_int"):
    s = summarize_group(sub)
    s["group"] = f"G{int(g)}"
    summaries.append(s)

summary_df = pd.DataFrame(summaries).sort_values("group")

fmt_cols = [
    "corr_rate_weighted",
    "backslide_rate_weighted",
    "persistent_wrong_rate_weighted",
    "corr_rate_mean",
    "backslide_rate_mean",
    "persistent_wrong_rate_mean",
    "acc1_mean_retakers",
    "acc2_mean_retakers",
]
for c in fmt_cols:
    summary_df[c] = summary_df[c].map(lambda x: np.nan if pd.isna(x) else float(x))

print("\nRetake error-dynamics summary by group (first 6 questions only)")
print(summary_df.to_string(index=False))

df_ret["init6"] = df_ret["init_list"]
df_ret["retry6"] = df_ret["retry_list"]
per_item_df = per_item_transitions(df_ret).sort_values(["group", "q_idx"])

print("\nOptional: per-question transition counts by group (first 6 questions only)")
print(per_item_df.to_string(index=False))