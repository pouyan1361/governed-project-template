"""
POLICY AS CODE for the agent team: what it may do, what needs a human, whose data, how much, is the model fit.

Scope has two levels, matching the federation's privacy promise:
  data_scope.aggregate_members     members whose AGGREGATES (counts, rates, comparisons) the agent may compute
  data_scope.record_level_members  members whose INDIVIDUAL records the agent may score or act on
A tool call with a `member` argument is checked against the first list; one with a record id (an argument
ending in _id) or listed in record_level_tools against the second.
"""
import json
from pathlib import Path

from . import model as M

ROOT = Path(__file__).resolve().parents[1]


def load_policy(path="governance/agent_policy.json"):
    with open(ROOT / path) as f:
        return json.load(f)


def precheck(policy):
    problems = []
    for t in policy.get("approval_required", []):
        if t not in policy["allowed_tools"]:
            problems.append(f"approval_required lists {t} but it is not an allowed tool")
    for t in policy.get("forbidden_for_any_agent", []):
        if t in policy["allowed_tools"]:
            problems.append(f"{t} is forbidden for any agent but appears in allowed_tools")
    if policy["max_tool_calls_per_task"] < 1:
        problems.append("max_tool_calls_per_task must be at least 1")
    rl = set(policy["data_scope"]["record_level_members"])
    if not rl <= set(policy["data_scope"]["aggregate_members"]):
        problems.append("record_level_members must be a subset of aggregate_members")
    try:
        m = M.load_model(policy["model"]["path"])
    except FileNotFoundError:
        problems.append(f"model file {policy['model']['path']} is missing: run python run_federation.py first")
        return problems
    if m["neutral_test_accuracy"] < policy["model"]["min_neutral_test_accuracy"]:
        problems.append(f"model accuracy {m['neutral_test_accuracy']} is below the policy floor {policy['model']['min_neutral_test_accuracy']}")
    if m.get("gate_decision") not in (None, "PASS"):
        problems.append(f"the model file records gate decision {m['gate_decision']}; only a PASS model may be used")
    return problems


class Decision:
    def __init__(self, verdict, reason):
        self.verdict, self.reason = verdict, reason

    def __repr__(self):
        return f"{self.verdict}: {self.reason}"


def check(policy, name, args, state):
    if name in policy.get("forbidden_for_any_agent", []):
        return Decision("refuse", f"{name} is forbidden for any agent by {policy['policy_name']}")
    if name not in policy["allowed_tools"]:
        return Decision("refuse", f"{name} is not on the allow list")
    if state["calls_made"] >= policy["max_tool_calls_per_task"]:
        return Decision("refuse", f"call budget exhausted: max_tool_calls_per_task = {policy['max_tool_calls_per_task']}")
    scope = policy["data_scope"]
    member = args.get("member")
    for key in ("member_a", "member_b"):
        if key in args and args[key] not in scope["aggregate_members"]:
            return Decision("refuse", f"{args[key]} is outside aggregate scope {scope['aggregate_members']}")
    if member is not None and member not in scope["aggregate_members"]:
        return Decision("refuse", f"{member} is outside aggregate scope {scope['aggregate_members']}")
    if name in policy.get("record_level_tools", []) and member not in scope["record_level_members"]:
        return Decision("refuse", f"{name} returns or touches individual records; allowed only for {scope['record_level_members']}, not {member}")
    rid = next((v for k, v in args.items() if k.endswith("_id")), None)
    if rid is not None:
        if member is None or member not in scope["record_level_members"]:
            return Decision("refuse", f"record-level access to {rid} is allowed only for {scope['record_level_members']}; member given: {member}")
        touched = set(state["records_touched"])
        if rid not in touched and len(touched) >= policy["max_records_per_task"]:
            return Decision("refuse", f"max_records_per_task = {policy['max_records_per_task']}; already touched {sorted(touched)}")
    if name in policy.get("approval_required", []):
        return Decision("approval", f"{name} is high stakes under {policy['policy_name']} v{policy['policy_version']}: a human must approve")
    return Decision("allow", f"on allow list; call {state['calls_made'] + 1} of {policy['max_tool_calls_per_task']}")
