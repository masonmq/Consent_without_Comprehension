import pandas as pd
import numpy as np

path = ""
df = pd.read_csv(path)

# -----------------------------
# Columns
# -----------------------------
q_cols = ["Q2","Q13","Q3","Q4","Q5","Q10","Q6","Q7","Q8"]

likert_order = [
    "Strongly agree",
    "Agree",
    "Neither agree nor disagree",
    "Disagree",
    "Strongly disagree",
]
likert_set = set(likert_order)


for c in q_cols:
    df[c] = df[c].astype(str).str.strip()
    # Drop unexpected values
    df.loc[~df[c].isin(likert_set), c] = np.nan

# Map numeric group -> "G0"..."G5"
df["G"] = df["group"].apply(lambda x: f"G{int(x)}" if pd.notna(x) else np.nan)

# -----------------------------
# Check which groups saw which questions
# -----------------------------
availability = {
    c: sorted(df.loc[df[c].notna(), "G"].unique().tolist())
    for c in q_cols
}
availability_df = pd.DataFrame(
    {"question": list(availability.keys()),
     "groups_with_answers": [", ".join(v) for v in availability.values()]}
).sort_values("question")


long = df.melt(id_vars=["G"], value_vars=q_cols, var_name="question", value_name="response")
long = long.dropna(subset=["G", "response"])

# -----------------------------
# Overall pooled distribution across all responses (all questions combined)
# -----------------------------
overall_dist = (
    long["response"]
    .value_counts()
    .reindex(likert_order)
    .fillna(0)
    .astype(int)
    .to_frame("count")
)
overall_dist["percent"] = (overall_dist["count"] / overall_dist["count"].sum() * 100).round(1)

# -----------------------------
# Per-question pooled distribution (pooled across groups that saw the question)
# -----------------------------
per_q_counts = (
    long.groupby(["question", "response"]).size()
    .unstack(fill_value=0)
    .reindex(columns=likert_order)
)
per_q_pct = (per_q_counts.div(per_q_counts.sum(axis=1), axis=0) * 100).round(1)

# -----------------------------
# Tail rates: Disagree + Strongly disagree by (question × group)
# -----------------------------
tail_set = {"Disagree", "Strongly disagree"}

tail = (
    long.assign(is_tail=long["response"].isin(tail_set))
    .groupby(["question", "G"])
    .agg(n=("response", "size"), tail_n=("is_tail", "sum"))
    .reset_index()
)
tail["tail_pct"] = (tail["tail_n"] / tail["n"] * 100).round(1)

tail_pct_wide = tail.pivot(index="question", columns="G", values="tail_pct").round(1)
tail_n_wide   = tail.pivot(index="question", columns="G", values="n").astype("Int64")

# -----------------------------
# Satisficing check: straightlining
# -----------------------------
resp_mat = df[q_cols].copy()
answered_n = resp_mat.notna().sum(axis=1)

def n_unique_nonnull(row):
    vals = [v for v in row.tolist() if pd.notna(v)]
    return len(set(vals))

unique_n = resp_mat.apply(n_unique_nonnull, axis=1)
straightline = (unique_n == 1) & (answered_n >= 2)

straightline_summary = (
    pd.DataFrame({"G": df["G"], "straightline": straightline})
    .dropna(subset=["G"])
    .groupby("G")["straightline"]
    .mean()
    .mul(100)
    .round(1)
    .to_frame("straightline_%")
)

overall_straightline = float(
    pd.DataFrame({"G": df["G"], "straightline": straightline})
    .dropna(subset=["G"])["straightline"]
    .mean() * 100
)

print("Availability (which groups have answers per question):")
print(availability_df.to_string(index=False))

print("\nOverall pooled distribution (all responses):")
print(overall_dist)

print("\nPer-question distribution (%):")
print(per_q_pct)

print("\nTail disagreement rate (% Disagree+Strongly disagree) by question × group:")
print(tail_pct_wide)

print("\nStraightlining rate (%) by group:")
print(straightline_summary)
print(f"\nOverall straightlining rate: {overall_straightline:.1f}%")
