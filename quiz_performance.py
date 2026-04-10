import pandas as pd
import ast
import numpy as np

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------
df = pd.read_csv("")

# Ensure group is numeric
df["group"] = df["group"].astype(int)

# --------------------------------------------------------------
# parse "[true, false, ...]" into Python list
# --------------------------------------------------------------
def parse_bool_list(s):
    if pd.isna(s):
        return None
    s = s.strip()
    # Convert "true"/"false" to Python True/False
    s = s.replace("true", "True").replace("false", "False")
    try:
        return ast.literal_eval(s)
    except:
        return None

# --------------------------------------------------------------
# Extract initial_answers → 1Q1–1Q7
# --------------------------------------------------------------
df["initial_list"] = df["initial_answers"].apply(parse_bool_list)

for i in range(7):  # 1Q1 to 1Q7
    col = f"1Q{i+1}"
    def extract_initial(row):
        lst = row["initial_list"]
        if lst is None:
            return np.nan
        if i < len(lst):
            return 1 if lst[i] else 0
        return np.nan   # not group 2 (no 7th question)
    df[col] = df.apply(extract_initial, axis=1)

# --------------------------------------------------------------
#Extract retry_answers → 2Q1–2Q7
# --------------------------------------------------------------
df["retry_list"] = df["retry_answers"].apply(parse_bool_list)

for i in range(7):  # 2Q1 to 2Q7
    col = f"2Q{i+1}"
    def extract_retry(row):
        lst = row["retry_list"]
        if lst is None:
            return np.nan
        if i < len(lst):
            return 1 if lst[i] else 0
        return np.nan
    df[col] = df.apply(extract_retry, axis=1)

# --------------------------------------------------------------
# Compute accuracy (1Q_acc and 2Q_acc)
# --------------------------------------------------------------
def compute_acc(row, prefix):
    # Determine number of questions
    if row["group"] == 2:
        end = 7
    else:
        end = 6
    cols = [f"{prefix}{i}" for i in range(1, end+1)]
    values = row[cols]
    values_clean = values.dropna()
    if len(values_clean) == 0:
        return np.nan
    return values_clean.sum() / end

df["1Q_acc"] = df.apply(lambda r: compute_acc(r, "1Q"), axis=1)
df["2Q_acc"] = df.apply(lambda r: compute_acc(r, "2Q"), axis=1)

