"""
DIAGNOSTIC SPECIALIST: why. Compares members and ranks drivers, still with aggregates only.

Working tools: compare_members, rank_drivers.
TODO for your team: explain_change (why did month X differ), segment_driver (which segment carries the gap).
"""
import numpy as np

from agent import tools as T
from . import _data as D


@T.tool("compare_members", "Compare two members: outcome rates and the features whose means differ most (in sd units).",
        T.obj_schema({"member_a": ("string", "first member"), "member_b": ("string", "second member")}), kind="analyze")
def compare_members(member_a, member_b):
    a, b = D.member(member_a), D.member(member_b)
    feats = D.features()
    diff = a.X_train.mean(axis=0) - b.X_train.mean(axis=0)      # standardized, so already in sd units
    order = np.argsort(-np.abs(diff))[:5]
    return {"member_a": {"name": member_a, "rows": a.n, "outcome_rate": round(float(a.y_train.mean()), 3)},
            "member_b": {"name": member_b, "rows": b.n, "outcome_rate": round(float(b.y_train.mean()), 3)},
            "largest_feature_differences_sd": [{"feature": feats[i], "a_minus_b_sd": round(float(diff[i]), 2)} for i in order],
            "reading": "A rate gap with small feature differences points to a base-rate (label) difference; large feature differences point to a different population."}


@T.tool("rank_drivers", "Within one member, which features move with the outcome (correlation with the label, sign and strength).",
        T.obj_schema({"member": ("string", "member name"), "top_k": ("integer", "how many features to return, default 5")}, required=["member"]), kind="analyze")
def rank_drivers(member, top_k=5):
    c = D.member(member)
    feats = D.features()
    y = c.y_train - c.y_train.mean()
    X = c.X_train - c.X_train.mean(axis=0)
    denom = (np.sqrt((X ** 2).sum(axis=0)) * np.sqrt((y ** 2).sum())) + 1e-9
    corr = (X * y[:, None]).sum(axis=0) / denom
    order = np.argsort(-np.abs(corr))[:int(top_k)]
    return {"member": member, "rows": c.n,
            "drivers": [{"feature": feats[i], "correlation_with_outcome": round(float(corr[i]), 3)} for i in order],
            "reading": "Compare the sign of a driver across members. A feature that is positive at every member but negative at one is a concept difference: the charter must decide what to do for that member."}
