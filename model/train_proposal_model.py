"""Train the FundBridge proposal model after real outcomes are collected.

Use anonymised historical records only. Do not fill this file with invented
labels. The output is intentionally separate from the public-company model.
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import random

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "model" / "proposal_outcomes.csv"
OUT = ROOT / "model" / "proposal_model.json"
FIELDS = ["monthlyRevenue", "monthlyExpenses", "startupCosts", "totalAssets", "totalLiabilities", "cashOnHand", "customerCount", "employees", "monthlyGrowthPercent"]


def read_rows():
    if not DATA.exists():
        raise SystemExit(f"Create {DATA.name} from proposal_training_template.csv and add real labelled outcomes first.")
    with DATA.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 50:
        raise SystemExit("At least 50 real labelled outcomes are required before training.")
    x = np.asarray([[float(row[field]) for field in FIELDS] for row in rows], dtype=float)
    y = np.asarray([int(row["profitableWithin18Months"]) for row in rows], dtype=float)
    if len(set(y.tolist())) < 2:
        raise SystemExit("The training data must contain both profitable (1) and not profitable (0) outcomes.")
    return x, y


def train(x, y):
    rng = random.Random(42); indexes = list(range(len(y))); rng.shuffle(indexes); split = int(len(y) * .8); train_idx, test_idx = indexes[:split], indexes[split:]
    mean = x[train_idx].mean(axis=0); scale = x[train_idx].std(axis=0); scale[scale < 1e-8] = 1
    tx = np.column_stack([np.ones(len(train_idx)), (x[train_idx] - mean) / scale]); vx = np.column_stack([np.ones(len(test_idx)), (x[test_idx] - mean) / scale]); weights = np.zeros(tx.shape[1])
    for _ in range(1800):
        probability = 1 / (1 + np.exp(-np.clip(tx @ weights, -30, 30))); weights -= .05 * ((tx.T @ (probability - y[train_idx])) / len(train_idx) + .001 * weights)
    prediction = (1 / (1 + np.exp(-np.clip(vx @ weights, -30, 30)))) >= .5
    return {"features": FIELDS, "weights": weights.tolist(), "mean": mean.tolist(), "scale": scale.tolist(), "rows": len(y), "testAccuracy": float((prediction == y[test_idx]).mean()), "warning": "Advisory estimate trained on anonymised FundBridge outcomes; not a funding decision."}


if __name__ == "__main__":
    x, y = read_rows(); artifact = train(x, y); OUT.write_text(json.dumps(artifact), encoding="utf-8"); print(json.dumps(artifact, indent=2))
