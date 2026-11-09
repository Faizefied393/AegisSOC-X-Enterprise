import argparse
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from aegissoc.data import load_flows


def train(csv_path: str | None = None, output_dir: str = "artifacts") -> dict:
    x, y, source = load_flows(csv_path)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "classifier",
                RandomForestClassifier(n_estimators=100, max_depth=14, n_jobs=-1, random_state=42),
            ),
        ]
    )
    model.fit(x_train, y_train)
    prob = model.predict_proba(x_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, pred, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    result = {
        "dataset": source,
        "samples": len(x),
        "features": list(x.columns),
        "threshold": 0.5,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "pr_auc": float(average_precision_score(y_test, prob)),
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0,
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "warning": "Synthetic data is not a security benchmark"
        if not csv_path
        else "Random row split may leak session-specific patterns; do not claim deployment validity",
    }
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "rf_model.joblib")
    (out / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "features"}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()
    train(args.csv)
