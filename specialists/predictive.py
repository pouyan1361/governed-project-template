"""
PREDICTIVE SPECIALIST: what will happen. The federated model as a tool, with its card facts attached.

Working tools: model_card_facts, predict_record, rank_records_by_risk.
TODO for your team: calibration_check per member (predicted vs actual rate on neutral_eval), what_if (change one feature).
"""
import numpy as np

from agent import model as M
from agent import tools as T
from . import _data as D


def _m():
    return M.load_model()


@T.tool("model_card_facts", "Provenance of the federated model: members, charter, gate decision, accuracy overall and per member, prohibited uses.",
        T.obj_schema({}), kind="read")
def model_card_facts():
    m = _m()
    return {k: m[k] for k in ("model_name", "charter", "gate_decision", "neutral_test_accuracy", "per_member_accuracy", "intended_use", "prohibited_uses", "threshold_high_risk")}


@T.tool("predict_record", "Probability of the outcome for ONE record of a member, with band and top drivers. Record-level: scope applies.",
        T.obj_schema({"member": ("string", "the member that holds the record"), "record_id": ("string", "the record's id, for example LG-00042")}), kind="model")
def predict_record(member, record_id):
    r = D.record(member, record_id)
    if r is None:
        return {"error": f"no record {record_id} at {member}"}
    m = _m()
    p = M.score(r, m)
    return {"member": member, "record_id": record_id, "probability": round(p, 3), "band": M.band(p, m["threshold_high_risk"]),
            "threshold": m["threshold_high_risk"], "drivers": M.top_drivers(r, m), "model": m["model_name"],
            "model_neutral_test_accuracy": m["neutral_test_accuracy"]}


@T.tool("rank_records_by_risk", "The top_k highest-risk records of a member, optionally restricted to one month. Record-level: scope applies.",
        T.obj_schema({"member": ("string", "member name"), "top_k": ("integer", "how many records, default 5"), "month": ("integer", "1 to 12, optional")}, required=["member"]), kind="model")
def rank_records_by_risk(member, top_k=5, month=None):
    c = D.member(member)
    m = _m()
    w = np.array(m["weights"])
    probs = 1 / (1 + np.exp(-(c.X_train @ w + m["bias"])))
    idx = [i for i in range(c.n) if month is None or int(c.rows[i]["month"]) == int(month)]
    idx.sort(key=lambda i: -probs[i])
    top = idx[:int(top_k)]
    return {"member": member, "month": month, "considered": len(idx),
            "records": [{"record_id": c.ids[i], "probability": round(float(probs[i]), 3), "band": M.band(float(probs[i]), m["threshold_high_risk"])} for i in top],
            "high_risk_share": round(float((probs[idx] >= m["threshold_high_risk"]).mean()), 3) if idx else None}
