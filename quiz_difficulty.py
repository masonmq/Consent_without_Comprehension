import pandas as pd
import numpy as np
import ast
import json

CSV_PATH = ""

GROUP_COL = "group"
INIT_LIST_COL = "initial_answers"
RETRY_LIST_COL = "retry_answers"

N_Q_ALL = 6        
RETAKE_GROUPS = {2, 3, 5}


def normalize_group(x):
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


def extract_item_cols(df, prefix, n_max=7):
    cols = []
    for i in range(1, n_max + 1):
        c = f"{prefix}{i}"
        if c in df.columns:
            cols.append(c)
    return cols


def ensure_item_columns(df):

    init_cols = extract_item_cols(df, "1Q")
    retry_cols = extract_item_cols(df, "2Q")

    if len(init_cols) >= 6 and len(retry_cols) >= 6:
        return df

    if INIT_LIST_COL not in df.columns:
        raise KeyError(
            "Could not find 1Q* columns or initial_answers column."
        )

    df = df.copy()
    df["_init_list"] = df[INIT_LIST_COL].apply(parse_bool_list)

    if RETRY_LIST_COL in df.columns:
        df["_retry_list"] = df[RETRY_LIST_COL].apply(parse_bool_list)
    else:
        df["_retry_list"] = None

    for i in range(7):
        c1 = f"1Q{i+1}"
        if c1 not in df.columns:
            def get_init(row, idx=i):
                lst = row["_init_list"]
                if lst is None or idx >= len(lst):
                    return np.nan
                return 1 if bool(lst[idx]) else 0
            df[c1] = df.apply(get_init, axis=1)

        c2 = f"2Q{i+1}"
        if c2 not in df.columns:
            def get_retry(row, idx=i):
                lst = row["_retry_list"]
                if lst is None or idx >= len(lst):
                    return np.nan
                return 1 if bool(lst[idx]) else 0
            df[c2] = df.apply(get_retry, axis=1)

    return df


def pct(x):
    return round(100 * x, 1) if pd.notna(x) else np.nan


def first_attempt_overall(df):
    rows = []
    for q in range(1, N_Q_ALL + 1):
        col = f"1Q{q}"
        valid = df[col].dropna()
        n = len(valid)
        correct = int(valid.sum())
        incorrect = int(n - correct)
        acc = correct / n if n > 0 else np.nan
        rows.append({
            "question": f"Q{q}",
            "n": n,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": acc,
            "incorrect_rate": 1 - acc if pd.notna(acc) else np.nan,
        })
    out = pd.DataFrame(rows)
    out = out.sort_values(["accuracy", "question"], ascending=[True, True]).reset_index(drop=True)
    return out


def first_attempt_by_group(df):
    rows = []
    for g, sub in df.groupby("group_int"):
        for q in range(1, N_Q_ALL + 1):
            col = f"1Q{q}"
            valid = sub[col].dropna()
            n = len(valid)
            correct = int(valid.sum())
            acc = correct / n if n > 0 else np.nan
            rows.append({
                "group": f"G{g}",
                "question": f"Q{q}",
                "n": n,
                "accuracy": acc,
                "incorrect_rate": 1 - acc if pd.notna(acc) else np.nan,
            })
    out = pd.DataFrame(rows)
    out = out.sort_values(["group", "accuracy", "question"], ascending=[True, True, True]).reset_index(drop=True)
    return out


def get_retakers(df):
    retry_cols = [f"2Q{i}" for i in range(1, N_Q_ALL + 1)]
    mask_group = df["group_int"].isin(RETAKE_GROUPS)
    mask_retry = df[retry_cols].notna().any(axis=1)
    return df[mask_group & mask_retry].copy()


def second_attempt_overall(ret):
    rows = []
    for q in range(1, N_Q_ALL + 1):
        col = f"2Q{q}"
        valid = ret[col].dropna()
        n = len(valid)
        correct = int(valid.sum())
        incorrect = int(n - correct)
        acc = correct / n if n > 0 else np.nan
        rows.append({
            "question": f"Q{q}",
            "n": n,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": acc,
            "incorrect_rate": 1 - acc if pd.notna(acc) else np.nan,
        })
    out = pd.DataFrame(rows)
    out = out.sort_values(["accuracy", "question"], ascending=[True, True]).reset_index(drop=True)
    return out


def second_attempt_by_group(ret):
    rows = []
    for g, sub in ret.groupby("group_int"):
        for q in range(1, N_Q_ALL + 1):
            col = f"2Q{q}"
            valid = sub[col].dropna()
            n = len(valid)
            correct = int(valid.sum())
            acc = correct / n if n > 0 else np.nan
            rows.append({
                "group": f"G{g}",
                "question": f"Q{q}",
                "n": n,
                "accuracy": acc,
                "incorrect_rate": 1 - acc if pd.notna(acc) else np.nan,
            })
    out = pd.DataFrame(rows)
    out = out.sort_values(["group", "accuracy", "question"], ascending=[True, True, True]).reset_index(drop=True)
    return out


def item_transition_summary(ret):
    rows = []
    for q in range(1, N_Q_ALL + 1):
        c1 = f"1Q{q}"
        c2 = f"2Q{q}"
        sub = ret[[c1, c2]].dropna()
        n = len(sub)

        init = sub[c1].astype(int).to_numpy()
        retry = sub[c2].astype(int).to_numpy()

        wc = int(((init == 0) & (retry == 1)).sum())  # wrong -> correct
        cw = int(((init == 1) & (retry == 0)).sum())  # correct -> wrong
        ww = int(((init == 0) & (retry == 0)).sum())  # wrong -> wrong
        cc = int(((init == 1) & (retry == 1)).sum())  # correct -> correct

        init_wrong = int((init == 0).sum())
        init_correct = int((init == 1).sum())

        correction_rate = wc / init_wrong if init_wrong > 0 else np.nan
        persistent_wrong_rate = ww / init_wrong if init_wrong > 0 else np.nan
        backslide_rate = cw / init_correct if init_correct > 0 else np.nan

        rows.append({
            "question": f"Q{q}",
            "n_retakers": n,
            "initial_wrong": init_wrong,
            "initial_correct": init_correct,
            "W_to_C": wc,
            "W_to_W": ww,
            "C_to_W": cw,
            "C_to_C": cc,
            "correction_rate_among_initial_wrong": correction_rate,
            "persistent_wrong_rate_among_initial_wrong": persistent_wrong_rate,
            "backslide_rate_among_initial_correct": backslide_rate,
        })

    out = pd.DataFrame(rows)
    return out


def print_pretty(df, title, pct_cols=None):
    pct_cols = pct_cols or []
    show = df.copy()
    for c in pct_cols:
        if c in show.columns:
            show[c] = show[c].map(lambda x: f"{pct(x):.1f}%" if pd.notna(x) else "")
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    print(show.to_string(index=False))


def main():
    df = pd.read_csv(CSV_PATH)
    df["group_int"] = df[GROUP_COL].apply(normalize_group)
    df = ensure_item_columns(df)

    # Keep only rows with valid group
    df = df[df["group_int"].notna()].copy()
    df["group_int"] = df["group_int"].astype(int)

    # 1) First attempt overall
    first_all = first_attempt_overall(df)
    print_pretty(
        first_all,
        "1) FIRST-ATTEMPT ITEM DIFFICULTY (ALL GROUPS, FIRST 6 QUESTIONS)",
        pct_cols=["accuracy", "incorrect_rate"]
    )

    # 2) First attempt by group
    first_group = first_attempt_by_group(df)
    print_pretty(
        first_group,
        "2) FIRST-ATTEMPT ITEM DIFFICULTY BY GROUP (FIRST 6 QUESTIONS)",
        pct_cols=["accuracy", "incorrect_rate"]
    )

    # Retakers only
    ret = get_retakers(df)

    # sanity
    ret_counts = ret.groupby("group_int").size().reset_index(name="retakers_n")
    ret_counts["group"] = ret_counts["group_int"].map(lambda x: f"G{x}")
    print_pretty(
        ret_counts[["group", "retakers_n"]],
        "SANITY CHECK: RETAKERS INCLUDED IN RETRY ANALYSIS"
    )

    # 3) Second attempt overall
    second_all = second_attempt_overall(ret)
    print_pretty(
        second_all,
        "3) SECOND-ATTEMPT ITEM DIFFICULTY (RETAKERS ONLY, FIRST 6 QUESTIONS)",
        pct_cols=["accuracy", "incorrect_rate"]
    )

    # 4) Second attempt by group
    second_group = second_attempt_by_group(ret)
    print_pretty(
        second_group,
        "4) SECOND-ATTEMPT ITEM DIFFICULTY BY GROUP (RETAKERS ONLY, FIRST 6 QUESTIONS)",
        pct_cols=["accuracy", "incorrect_rate"]
    )

    # 5) Transition summary
    trans = item_transition_summary(ret)
    print_pretty(
        trans.sort_values("persistent_wrong_rate_among_initial_wrong", ascending=False),
        "5) ITEM-LEVEL RETAKE TRANSITIONS (SORTED BY PERSISTENT WRONG RATE)",
        pct_cols=[
            "correction_rate_among_initial_wrong",
            "persistent_wrong_rate_among_initial_wrong",
            "backslide_rate_among_initial_correct",
        ]
    )

    # top-2 summaries
    print("\n" + "=" * 90)
    print("TOP 2 HARDEST ITEMS ON FIRST ATTEMPT (ALL GROUPS)")
    print("=" * 90)
    print(first_all[["question", "accuracy", "incorrect_rate"]].head(2).assign(
        accuracy=lambda d: d["accuracy"].map(lambda x: f"{pct(x):.1f}%"),
        incorrect_rate=lambda d: d["incorrect_rate"].map(lambda x: f"{pct(x):.1f}%")
    ).to_string(index=False))

    print("\n" + "=" * 90)
    print("TOP 2 HARDEST ITEMS ON SECOND ATTEMPT (RETAKERS)")
    print("=" * 90)
    print(second_all[["question", "accuracy", "incorrect_rate"]].head(2).assign(
        accuracy=lambda d: d["accuracy"].map(lambda x: f"{pct(x):.1f}%"),
        incorrect_rate=lambda d: d["incorrect_rate"].map(lambda x: f"{pct(x):.1f}%")
    ).to_string(index=False))

    print("\n" + "=" * 90)
    print("TOP 2 ITEMS HARDEST TO FIX AFTER RETAKE")
    print("=" * 90)
    top_fix = trans.sort_values(
        "persistent_wrong_rate_among_initial_wrong", ascending=False
    )[["question", "persistent_wrong_rate_among_initial_wrong", "correction_rate_among_initial_wrong"]].head(2)
    top_fix["persistent_wrong_rate_among_initial_wrong"] = top_fix["persistent_wrong_rate_among_initial_wrong"].map(lambda x: f"{pct(x):.1f}%")
    top_fix["correction_rate_among_initial_wrong"] = top_fix["correction_rate_among_initial_wrong"].map(lambda x: f"{pct(x):.1f}%")
    print(top_fix.to_string(index=False))


if __name__ == "__main__":
    main()