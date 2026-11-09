"""
EVIDENCE: every decision the agent and the policy made, one JSON line each.

The log is the agent's version of Week 6's federation_audit_log.jsonl.
An auditor who never saw the agent run should be able to reconstruct from it:
what the task was, which tools were proposed, which were allowed, refused or
sent to a human, what the human said, and what the agent finally told the user.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Audit:
    def __init__(self, policy):
        self.path = ROOT / policy["logging"]["audit_log"]
        self.path.parent.mkdir(exist_ok=True)
        self.log_args = policy["logging"].get("log_arguments", True)
        self.policy_id = f"{policy['policy_name']} v{policy['policy_version']}"

    def event(self, task_id, kind, **fields):
        rec = {"ts": _now(), "task_id": task_id, "policy": self.policy_id, "event": kind}
        if not self.log_args and "args" in fields:
            fields["args"] = "(not logged)"
        rec.update(fields)
        with open(self.path, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec


def read_log(policy):
    p = ROOT / policy["logging"]["audit_log"]
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(entries):
    """Counts an auditor would want first."""
    c = Counter(e["event"] for e in entries)
    tools = Counter(e.get("tool") for e in entries if e["event"] == "tool_allowed")
    refused = [(e.get("tool"), e.get("reason")) for e in entries if e["event"] == "tool_refused"]
    approvals = Counter(e.get("outcome") for e in entries if e["event"] == "approval")
    planners = Counter(e.get("planner") for e in entries if e["event"] == "task_start")
    return {"tasks": c.get("task_start", 0), "tool_calls_allowed": sum(tools.values()), "by_tool": dict(tools),
            "refusals": refused, "approvals": dict(approvals), "planners": dict(planners),
            "finals": c.get("task_end", 0)}


def agent_card(policy, model, summary, path="artifacts/agent_card.md"):
    """A system card for the agent, next to the model card the federation already published."""
    lines = [
        f"# Agent card: {policy['system']}",
        "",
        f"Policy: {policy['policy_name']} v{policy['policy_version']}. Owner: {policy['owner']}. Approved by: {policy['approved_by']}.",
        "",
        "## Purpose and limits",
        policy["purpose"],
        f"Allowed uses of the model: {', '.join(policy['model']['allowed_uses'])}. Prohibited: {', '.join(policy['model']['prohibited_uses'])}.",
        "",
        "## What the agent can do (tools on the allow list)",
        *[f"- {t}" + ("  (human approval required)" if t in policy.get("approval_required", []) else "") for t in policy["allowed_tools"]],
        "",
        "## What it may never do",
        *[f"- {t}" for t in policy.get("forbidden_for_any_agent", [])],
        f"- compute aggregates for members outside {policy['data_scope']['aggregate_members']}",
        f"- score or act on individual records outside {policy['data_scope']['record_level_members']}",
        f"- more than {policy['max_tool_calls_per_task']} tool calls or {policy['max_records_per_task']} record(s) per task",
        "",
        "## The model it relies on",
        f"{model['model_name']}. Neutral test accuracy {model['neutral_test_accuracy']} (policy floor {policy['model']['min_neutral_test_accuracy']}). "
        f"Per member: {model['per_member_accuracy']}. Trained under: {model['charter']}; gate {model.get('gate_decision')}. High-risk threshold {policy['model']['high_risk_threshold']}.",
        "",
        "## Evidence from the audit log so far",
        f"Tasks run: {summary['tasks']}. Tool calls allowed: {summary['tool_calls_allowed']} {summary['by_tool']}. "
        f"Refusals: {len(summary['refusals'])}. Approvals: {summary['approvals']}. Planners used: {summary['planners']}.",
        "",
        "## Open questions for the committee (answer these in docs/agent_card.md)",
        "- Who reviews this log, how often, and what would make them pull the agent?",
        "- Which approval could be automated later, and what evidence would justify that?",
        "",
    ]
    out = ROOT / path
    out.write_text("\n".join(lines))
    return out
