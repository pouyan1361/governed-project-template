"""
THE MODEL TOOL: the model your federation trained (python run_federation.py writes models/federated_model.json).

The file holds weights, bias, feature names, the reference means and sds, and the
model card facts (accuracy overall and per member, charter, gate decision). No row is in it.

The agent never trains anything. It USES this model as one tool among several.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_model(path="models/federated_model.json"):
    with open(ROOT / path) as f:
        return json.load(f)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def standardize(record, m):
    """Human units in, z-scores out, in the model's feature order."""
    return np.array([(float(record[f]) - m["human_units_mean_sd"][f][0]) / m["human_units_mean_sd"][f][1]
                     for f in m["features"]])


def score(record, m):
    """Probability of the outcome for one record in human units (the Lab 1 formula)."""
    z = standardize(record, m)
    logit = z @ np.array(m["weights"]) + m["bias"]
    return float(sigmoid(logit))


def top_drivers(record, m, k=3):
    """The k features pushing this patient's risk up the most (weight times z-score)."""
    z = standardize(record, m)
    w = np.array(m["weights"])
    contrib = w * z
    order = np.argsort(-contrib)[:k]
    return [{"feature": m["features"][i], "value": record[m["features"][i]], "push": round(float(contrib[i]), 3)} for i in order]


def band(p, threshold):
    if p >= threshold:
        return "HIGH"
    if p >= threshold - 0.2:
        return "MEDIUM"
    return "LOW"
