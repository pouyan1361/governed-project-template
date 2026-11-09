"""
THE GOVERNED FEDERATION for your consortium. Trains the predictive model the agents will use.

    python run_federation.py                        your consortium (config.CONSORTIUM), the charter in governance/
    python run_federation.py --baselines            also report local-only and centralized accuracy per member
    python run_federation.py --attack boost --attacker "St. Brigid"
    python run_federation.py --policy governance/federation_policy.json

Writes models/federated_model.json (weights, bias, reference means and sds, card facts) for the predictive specialist,
plus the evidence in artifacts/.

The coordinator reads governance/federation_policy.json (the charter) and
enforces it on every round. The run leaves evidence in artifacts/:
    federation_audit_log.jsonl   one line per round: who, what the coordinator saw, what it did
    federated_model_card.md      the model card for the federated model
    federation_gate_report.json  PASS or BLOCKED, check by check
Exit code 0 means PASS, 1 means BLOCKED or a policy pre-check failed.

Week 1's control triad, federated:
    OWNER     the coordinator role, named in the charter, rotating
    TRIGGER   every round, automatically
    EVIDENCE  the three files above
"""
import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fl import audit, federation as F, ui  # noqa: E402
from fl.consortium import load_world  # noqa: E402
import config  # noqa: E402

ROBUST = {"median", "trimmed_mean", "krum"}


def load_policy(path):
    with open(path) as f:
        return json.load(f)


def check(name, value, threshold, passed, why):
    return {"check": name, "value": value, "threshold": threshold, "passed": bool(passed), "why": why}


def precheck(policy):
    """Preventive: a charter that asks for the impossible stops the run before it starts."""
    problems = []
    if policy["secure_aggregation"] and policy["aggregation"] in ROBUST:
        problems.append(f"secure_aggregation is true but aggregation is {policy['aggregation']}: the coordinator cannot "
                        "robustly aggregate updates it cannot see. Choose one.")
    if policy["secure_aggregation"] and policy.get("reject_update_norm_above"):
        problems.append("secure_aggregation is true but reject_update_norm_above is set: the coordinator cannot see norms.")
    if policy["min_clients_per_round"] < 2:
        problems.append("min_clients_per_round below 2: with one participant the aggregate IS that member's update.")
    if policy["min_clients_per_round"] > len(policy["members"]):
        problems.append("min_clients_per_round exceeds the number of members.")
    if policy["aggregation"] not in {"mean", "simple_mean"} | ROBUST:
        problems.append(f"unknown aggregation {policy['aggregation']}")
    return problems


def gate(policy, history, world):
    last = history[-1]
    accs = last["per_client"]
    results = []
    results.append(check("all_participants_are_members",
                         sorted({p for e in history for p in e["participants"]} - set(policy["members"])) or "none", "none",
                         all(p in policy["members"] for e in history for p in e["participants"]),
                         "Only charter members may contribute updates."))
    min_part = min(len(e["participants"]) - len(e["rejected"]) for e in history)
    results.append(check("min_clients_every_round", min_part, policy["min_clients_per_round"],
                         min_part >= policy["min_clients_per_round"],
                         "Below the minimum, an aggregate reveals an individual member."))
    results.append(check("global_accuracy", round(last["global_acc"], 4), policy["min_global_accuracy"],
                         last["global_acc"] >= policy["min_global_accuracy"], "The model must be useful overall."))
    worst = min(accs, key=accs.get)
    results.append(check(f"min_member_accuracy[{worst}]", round(accs[worst], 4), policy["min_member_accuracy"],
                         accs[worst] >= policy["min_member_accuracy"],
                         "The model must work for every member's population, not just the largest."))
    gap = max(accs.values()) - min(accs.values())
    results.append(check("member_accuracy_gap", round(gap, 4), policy["max_member_accuracy_gap"],
                         gap <= policy["max_member_accuracy_gap"],
                         "No member may be served much worse than another."))
    results.append(check("privacy_control_present",
                         "secagg on" if policy["secure_aggregation"] else f"dp {policy['dp_noise_multiplier']}",
                         "secagg or dp>=0.1",
                         policy["secure_aggregation"] or policy["dp_noise_multiplier"] >= 0.1,
                         "Updates must be protected from the coordinator by at least one mechanism."))
    passed = all(r["passed"] for r in results)
    return {"decision": "PASS" if passed else "BLOCKED", "policy_version": policy["policy_version"], "checks": results}


def print_gate(report):
    line = "=" * 78
    print(line)
    print(f"  FEDERATION GATE   charter v{report['policy_version']}")
    print(line)
    print(f"  {'check':<36}{'value':>12}{'threshold':>20}   result")
    print("-" * 78)
    for r in report["checks"]:
        print(f"  {r['check']:<36}{str(r['value']):>12}{str(r['threshold']):>20}   {'pass' if r['passed'] else 'FAIL  <--'}")
    print(line)
    if report["decision"] == "PASS":
        print("  DECISION: PASS. The federated model may proceed to deployment review.")
    else:
        print("  DECISION: BLOCKED. The federated model may NOT be deployed.")
        for r in report["checks"]:
            if not r["passed"]:
                print(f"    - {r['check']}: {r['why']}")
    print(line)


def export_model(world, policy, theta, history, report):
    """The predictive specialist's tool: weights plus the card facts, never a row."""
    last = history[-1]
    schema = world.schema
    out = {
        "model_name": f"{world.title}: {world.label} model, federated (FedAvg across {len(world.clients)} members)",
        "consortium": world.name, "label": world.label, "unit": world.unit,
        "charter": f"{policy['policy_name']} v{policy['policy_version']}",
        "gate_decision": report["decision"],
        "members": [c.name for c in world.clients], "training_rows": {c.name: int(c.n) for c in world.clients},
        "neutral_test_accuracy": round(float(last["global_acc"]), 4),
        "per_member_accuracy": {k: round(float(v), 3) for k, v in last["per_client"].items()},
        "features": world.features,
        "human_units_mean_sd": {f["name"]: [f["mean"], f["sd"]] for f in schema["features"]},
        "weights": [round(float(w), 6) for w in theta[:-1]], "bias": round(float(theta[-1]), 6),
        "threshold_high_risk": policy.get("high_risk_threshold", 0.5),
        "intended_use": schema["intended_use"], "prohibited_uses": schema["prohibited_uses"],
    }
    (ROOT / "models").mkdir(exist_ok=True)
    path = ROOT / "models" / "federated_model.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"  models/federated_model.json  (the predictive specialist's tool; gate {report['decision']})")
    return path


def main():
    ap = argparse.ArgumentParser(description="Run the governed federation")
    ap.add_argument("--policy", default="governance/federation_policy.json")
    ap.add_argument("--attack", default=None, choices=[None, "flip", "boost", "backdoor"])
    ap.add_argument("--attacker", default=None)
    ap.add_argument("--scale", type=float, default=10.0)
    ap.add_argument("--consortium", default=config.CONSORTIUM)
    ap.add_argument("--baselines", action="store_true", help="also train local-only and centralized baselines and report per member")
    a = ap.parse_args()

    policy = load_policy(ROOT / a.policy)
    run_info = {"run_id": uuid.uuid4().hex[:8], "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "policy_hash": audit.sha256_file(ROOT / a.policy), "policy_version": policy["policy_version"]}
    ui.title(f"GOVERNED FEDERATION  |  charter v{policy['policy_version']}  |  run {run_info['run_id']}")

    print("[stage 1] Charter pre-check (preventive)")
    problems = precheck(policy)
    if problems:
        for p in problems:
            print(f"  STOPPED: {p}")
        audit.append_round({**run_info, "stage": "precheck", "decision": "STOPPED", "problems": problems})
        sys.exit(1)
    print("  charter is internally consistent")

    world = load_world(a.consortium)
    if [c.name for c in world.clients] != policy["members"]:
        print(f"STOPPED: charter members {policy['members']} do not match the data folder's members {[c.name for c in world.clients]}")
        sys.exit(2)
    # members must match the charter (checked above)
    print(f"\n[stage 2] Members and data ({a.consortium})")
    print(world.describe())

    cfg = F.Config(rounds=policy["rounds"], E=policy["max_local_epochs"], C=1.0,
                   aggregator=policy["aggregation"], clip_norm=policy["max_update_norm"],
                   reject_norm_above=policy.get("reject_update_norm_above"), secagg=policy["secure_aggregation"],
                   dp_noise=policy["dp_noise_multiplier"], attack=a.attack, attacker=a.attacker if a.attack else None,
                   attack_scale=a.scale, verbose=True)
    print(f"\n[stage 3] Federated training: {cfg.rounds} rounds, E<={cfg.E}, aggregation={cfg.aggregator}, "
          f"clip={cfg.clip_norm}, secure_aggregation={cfg.secagg}, dp_noise={cfg.dp_noise}"
          + (f", SIMULATED ATTACK {a.attack} by {a.attacker}" if a.attack else ""))
    log_path = audit.ARTIFACTS / "federation_audit_log.jsonl"
    theta, history = F.run(world, cfg, on_round=lambda e: audit.append_round({**run_info, **e}))

    print("\n[stage 4] Federation gate")
    report = gate(policy, history, world)
    audit.write_json(report, "federation_gate_report.json")
    print_gate(report)

    if a.baselines:
        print("\n[stage 4b] Baselines per member (accuracy on the neutral evaluation set)")
        from fl import model as M
        loc = F.local_only(world)
        cen = F.centralized(world)
        print(f"  {'member':<28} {'local only':>10} {'FedAvg':>10} {'centralized':>12} {'gain':>8}")
        for k, c in enumerate(world.clients):
            Xt, yt = world.test_for(k)
            la, fa, ca = M.accuracy(loc[c.name], Xt, yt), M.accuracy(theta, Xt, yt), M.accuracy(cen, Xt, yt)
            print(f"  {c.name:<28} {la:>10.3f} {fa:>10.3f} {ca:>12.3f} {fa - la:>+8.3f}")
        print(f"  {'overall':<28} {'':>10} {M.accuracy(theta, world.X_test, world.y_test):>10.3f} {M.accuracy(cen, world.X_test, world.y_test):>12.3f}")

    print("\n[stage 5] Evidence")
    export_model(world, policy, theta, history, report)
    card = audit.model_card(policy, cfg, history, report, world, run_info)
    print(f"  {log_path.relative_to(ROOT)}  ({len(history)} round entries appended)")
    print(f"  {card.relative_to(ROOT)}")
    print(f"  artifacts/federation_gate_report.json")
    sys.exit(0 if report["decision"] == "PASS" else 1)


if __name__ == "__main__":
    main()
