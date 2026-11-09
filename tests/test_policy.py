import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import specialists  # noqa: F401
from agent import policy as P
import config

POL = P.load_policy()


def fresh():
    return {"calls_made": 0, "records_touched": set()}


def test_precheck_ok():
    assert P.precheck(POL) == []


def test_forbidden_tools_refused():
    for t in POL["forbidden_for_any_agent"]:
        assert P.check(POL, t, {"member": config.HOME_MEMBER, "record_id": "X-00001", "destination": "x"}, fresh()).verdict == "refuse"


def test_gated_tools_need_approval():
    for t in POL["approval_required"]:
        assert P.check(POL, t, {"member": config.HOME_MEMBER, "record_id": "X-00001"}, fresh()).verdict == "approval"


def test_record_level_scope():
    other = next(m for m in POL["data_scope"]["aggregate_members"] if m not in POL["data_scope"]["record_level_members"])
    assert P.check(POL, "predict_record", {"member": other, "record_id": "X-00001"}, fresh()).verdict == "refuse"
    assert P.check(POL, "summarize_member", {"member": other}, fresh()).verdict == "allow"


def test_budget():
    st = fresh()
    st["calls_made"] = POL["max_tool_calls_per_task"]
    assert P.check(POL, "summarize_member", {"member": config.HOME_MEMBER}, st).verdict == "refuse"
