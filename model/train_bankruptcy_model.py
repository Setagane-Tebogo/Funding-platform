"""Train a small, reproducible financial-distress model from the UCI ARFF file.

The resulting artifact is an auxiliary risk signal. It must not be presented as
a guarantee of profitability or as the sole basis for a funding decision.
"""
from __future__ import annotations

import json
import math
import pathlib
import random

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "polish_bankruptcy" / "5year.arff"
OUT = ROOT / "model" / "bankruptcy_model.json"


def load_arff(path: pathlib.Path):
    rows = []
    in_data = False
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower() == "@data":
            in_data = True
            continue
        if not in_data or line.startswith("@"):
            continue
        values = line.split(",")
        try:
            numeric = [float(value) if value not in {"?", ""} else math.nan for value in values[:-1]]
            label = int(float(values[-1]))
        except ValueError:
            continue
        rows.append((numeric, label))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    x = np.asarray([row[0] for row in rows], dtype=float)
    y = np.asarray([row[1] for row in rows], dtype=float)
    medians = np.nanmedian(x, axis=0)
    x = np.where(np.isnan(x), medians, x)
    return x, y


def train(x: np.ndarray, y: np.ndarray):
    rng = random.Random(42)
    indexes = list(range(len(y)))
    rng.shuffle(indexes)
    split = int(len(indexes) * 0.8)
    train_idx, test_idx = indexes[:split], indexes[split:]
    mean = x[train_idx].mean(axis=0)
    scale = x[train_idx].std(axis=0)
    scale[scale < 1e-8] = 1.0
    train_x = (x[train_idx] - mean) / scale
    test_x = (x[test_idx] - mean) / scale
    # Add an intercept and use a class-weighted logistic loss for imbalance.
    train_x = np.column_stack([np.ones(len(train_x)), train_x])
    test_x = np.column_stack([np.ones(len(test_x)), test_x])
    weights = np.zeros(train_x.shape[1])
    positive = max(float(y[train_idx].sum()), 1.0)
    negative = max(float(len(train_idx) - positive), 1.0)
    class_weight = np.where(y[train_idx] > 0, 0.5 / positive, 0.5 / negative)
    for _ in range(1800):
        logits = np.clip(train_x @ weights, -30, 30)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        gradient = (train_x.T @ ((probabilities - y[train_idx]) * class_weight)) + 0.001 * weights
        weights -= 0.08 * gradient
    probabilities = 1.0 / (1.0 + np.exp(-np.clip(test_x @ weights, -30, 30)))
    predictions = probabilities >= 0.5
    accuracy = float((predictions == y[test_idx]).mean())
    true_positive = float(((predictions == 1) & (y[test_idx] == 1)).sum())
    actual_positive = float((y[test_idx] == 1).sum())
    recall = true_positive / actual_positive if actual_positive else 0.0
    return {"weights": weights.tolist(), "mean": mean.tolist(), "scale": scale.tolist(), "features": int(x.shape[1]), "rows": int(len(y)), "positiveRate": float(y.mean()), "testAccuracy": accuracy, "testRecall": recall}


if __name__ == "__main__":
    features, labels = load_arff(DATA)
    artifact = train(features, labels)
    artifact.update({"dataset": "UCI Polish Companies Bankruptcy (5-year)", "target": "bankruptcy", "warning": "Auxiliary financial-distress signal; not a profitability guarantee."})
    OUT.write_text(json.dumps(artifact), encoding="utf-8")
    print(json.dumps({key: artifact[key] for key in ("dataset", "rows", "positiveRate", "testAccuracy", "testRecall")}, indent=2))
