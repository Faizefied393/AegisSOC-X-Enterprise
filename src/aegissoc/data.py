from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification


def load_flows(csv_path: str | None = None) -> tuple[pd.DataFrame, pd.Series, str]:
    if not csv_path:
        x, y = make_classification(
            n_samples=3000, n_features=20, n_informative=12, weights=[0.90, 0.10], random_state=42
        )
        return (
            pd.DataFrame(x, columns=[f"feature_{i}" for i in range(20)]),
            pd.Series(y, name="target"),
            "synthetic-smoke-test",
        )

    path = Path(csv_path)
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    if "Label" not in df.columns:
        raise ValueError("Expected CIC-IDS2017 CSV with a 'Label' column")
    target = df["Label"].astype(str).str.strip().str.upper().ne("BENIGN").astype(int)
    x = df.drop(columns=["Label"])
    x = x.select_dtypes(include="number")
    x = x.loc[:, ~x.columns.duplicated()]
    x = x.replace([np.inf, -np.inf], np.nan)
    x = x.dropna(axis=1, how="all")
    if x.empty or target.nunique() < 2:
        raise ValueError("Need numeric features and both benign and attack examples")
    return x, target, str(path)
