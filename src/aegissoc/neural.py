import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from aegissoc.data import load_flows


def train_neural(csv_path: str | None = None):
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise SystemExit("Install with: uv sync --group dev --extra deep-learning") from exc

    torch.manual_seed(42)
    x, y, source = load_flows(csv_path)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_array = scaler.fit_transform(imputer.fit_transform(x_train))
    val_array = scaler.transform(imputer.transform(x_val))
    test_array = scaler.transform(imputer.transform(x_test))
    train_array = np.clip(train_array, -20, 20)
    val_array = np.clip(val_array, -20, 20)
    test_array = np.clip(test_array, -20, 20)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    def tensors(a, b):
        return (
            torch.tensor(a, dtype=torch.float32, device=device),
            torch.tensor(b.to_numpy(), dtype=torch.float32, device=device).reshape(-1, 1),
        )

    xt, yt = tensors(train_array, y_train)
    xv, yv = tensors(val_array, y_val)
    xe, _ = tensors(test_array, y_test)
    net = nn.Sequential(
        nn.Linear(xt.shape[1], 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 1)
    ).to(device)
    optimizer = torch.optim.AdamW(net.parameters(), lr=0.001)
    pos_weight = torch.tensor(
        [float((y_train == 0).sum() / max(1, (y_train == 1).sum()))], device=device
    )
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    best_loss = float("inf")
    best_state = None
    patience = 0
    for epoch in range(40):
        net.train()
        for start in range(0, len(xt), 256):
            logits = net(xt[start : start + 256])
            loss = criterion(logits, yt[start : start + 256])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        net.eval()
        with torch.no_grad():
            val_loss = criterion(net(xv), yv).item()
        print(f"epoch={epoch + 1} val_loss={val_loss:.4f}")
        if val_loss < best_loss - 0.0001:
            best_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= 5:
                break
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(net(xe)).cpu().numpy().ravel()
    pred = (probabilities >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, pred, average="binary", zero_division=0
    )
    metrics = {
        "dataset": source,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "pr_auc": float(average_precision_score(y_test, probabilities)),
        "note": "Compare only with models evaluated on an identical test split",
    }
    Path("artifacts").mkdir(exist_ok=True)
    torch.save(
        {"state_dict": net.cpu().state_dict(), "input_dim": xt.shape[1]}, "artifacts/mlp_model.pt"
    )
    (Path("artifacts") / "mlp_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv")
    train_neural(parser.parse_args().csv)
