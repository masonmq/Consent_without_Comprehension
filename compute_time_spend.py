import pandas as pd
import numpy as np
from scipy.stats import kruskal

# -----------------------------
# Load
# -----------------------------
df = pd.read_csv("")

group_col   = "group"
policy1_col = "initial_read_time"
quiz1_col   = "initial_quiz_time"
policy2_col = "retry_read_time"
quiz2_col   = "retry_quiz_time"
retake_acc_col = "2Q_acc"  

time_cols = [policy1_col, quiz1_col, policy2_col, quiz2_col]


for c in time_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

def normalize_group(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s.upper().startswith("G"):
        return s.upper()
    try:
        i = int(float(s))  # handles "0", 0, "0.0"
        return f"G{i}"
    except Exception:
        return s

df[group_col] = df[group_col].apply(normalize_group)


for c in [policy2_col, quiz2_col]:
    if c in df.columns:
        df.loc[df[c] == 0, c] = np.nan


for c in time_cols:
    if c in df.columns:
        df.loc[df[c] >= 1200, c] = np.nan

if retake_acc_col in df.columns:
    retaker = df[retake_acc_col].notna()
else:
    retaker = (df[policy2_col].notna() | df[quiz2_col].notna())

# -----------------------------
# Summaries
# -----------------------------
def summarize_by_group(col):
    g = df.groupby(group_col)[col]
    out = g.agg(
        n="count",
        median="median",
        q1=lambda x: x.quantile(0.25),
        q3=lambda x: x.quantile(0.75),
        mean="mean",
        std="std",
    ).reset_index()
    out["iqr"] = out["q3"] - out["q1"]

    order = ["G0", "G1", "G2", "G3", "G4", "G5"]
    out[group_col] = pd.Categorical(out[group_col], categories=order, ordered=True)
    return out.sort_values(group_col)

print("\nFirst-attempt POLICY (initial_read_time):")
print(summarize_by_group(policy1_col).to_string(index=False))

print("\nFirst-attempt QUIZ (initial_quiz_time):")
print(summarize_by_group(quiz1_col).to_string(index=False))

print("\nSecond-attempt POLICY (retry_read_time):")
print(summarize_by_group(policy2_col).to_string(index=False))

print("\nSecond-attempt QUIZ (retry_quiz_time):")
print(summarize_by_group(quiz2_col).to_string(index=False))


def kruskal_test(col):
    order = ["G0", "G1", "G2", "G3", "G4", "G5"]
    present_groups = [g for g in order if g in set(df[group_col].dropna())]

    samples = []
    used = []
    for g in present_groups:
        s = df.loc[df[group_col] == g, col].dropna().values
        if len(s) > 0:
            samples.append(s)
            used.append(g)

    if len(samples) < 2:
        print(f"\nKruskal–Wallis on {col}: not enough non-missing groups. groups_used={used}")
        return

    H, p = kruskal(*samples)
    n = sum(len(s) for s in samples)
    k = len(samples)
    eps2 = (H - k + 1) / (n - k) if (n - k) > 0 else float("nan")

    print(f"\nKruskal–Wallis on {col}:")
    print("  groups_used =", used)
    print("  H =", float(H), " p =", float(p), " epsilon^2 =", float(eps2))

kruskal_test(policy1_col)
kruskal_test(quiz1_col)


df["total_time_1"] = df[[policy1_col, quiz1_col]].sum(axis=1, min_count=2)


df["total_time_2"] = np.nan
df.loc[retaker, "total_time_2"] = df.loc[retaker, [policy2_col, quiz2_col]].sum(axis=1, min_count=2)

def median_iqr(s):
    s = s.dropna()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    return pd.Series({"n": len(s), "median": s.median(), "q1": q1, "q3": q3, "iqr": q3 - q1})

print("\nFirst-attempt TOTAL time (review + quiz): median/IQR by group")
print(df.groupby(group_col)["total_time_1"].apply(median_iqr).reset_index().to_string(index=False))

print("\nSecond-attempt TOTAL time (review + quiz): median/IQR by group")
print(df.groupby(group_col)["total_time_2"].apply(median_iqr).reset_index().to_string(index=False))


print("\nSanity check: retaker counts by group (based on retaker flag)")
print(
    retaker.groupby(df[group_col])
           .sum()
           .rename("retakers_n")
           .reset_index()
           .to_string(index=False)
)