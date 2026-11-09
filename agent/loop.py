"""
THE LOOP: observe, plan, check, act, log. Repeat until the planner says "final"
or the policy says stop.

   task ──► planner proposes an action ──► POLICY decides ──► allow: run the tool
                 ▲                              │                approval: ask a human
                 │                              │                refuse: log, stop
                 └──────── result ◄─────────────┘

Nothing reaches a tool without passing policy.check(), and nothing happens
without a line in the audit log. Those two sentences are the whole lecture.
"""
import json
import uuid

from . import audit as A
from . import policy as P
from . import tools as T

W = 78


def title(t):
    print("=" * W)
    print(t)
    print("=" * W)


def section(t):
    print()
    print(t)
    print("-" * W)


def short(obj, n=110):
    s = json.dumps(obj, default=str) if not isinstance(obj, str) else obj
    return s if len(s) <= n else s[: n - 3] + "..."


def ask_human(name, args):
    """Approval at the terminal. The human sees exactly what would happen."""
    print(f"        HUMAN  approval needed for {name}({json.dumps(args)})")
    while True:
        ans = input("        approve? [y/n] ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


def run_task(task, planner, policy, approve="ask", max_steps=12, quiet=False):
    """
    approve: "ask" (terminal prompt), "auto" (always yes), "deny" (always no)
    Returns the list of history entries for this task.
    """
    aud = A.Audit(policy)
    task_id = uuid.uuid4().hex[:8]
    state = {"calls_made": 0, "records_touched": set()}
    history = []
    aud.event(task_id, "task_start", task=task, planner=planner.name)
    if not quiet:
        title(f"TASK {task_id}: {task}")
        print(f"planner: {planner.name}    policy: {policy['policy_name']} v{policy['policy_version']}    approval mode: {approve}")

    for step in range(1, max_steps + 1):
        actions = planner.next_actions(task, history)
        stop = False
        for act in actions:
            if act["type"] == "final":
                aud.event(task_id, "task_end", final=act["text"], steps=step, tool_calls=state["calls_made"])
                if not quiet:
                    section("FINAL")
                    print(act["text"])
                    print(f"\naudit: events for task {task_id} appended to {policy['logging']['audit_log']}")
                return history

            name, args = act["name"], act["args"]
            call_id = act.get("call_id", f"call_{uuid.uuid4().hex[:6]}")
            entry = {"tool": name, "args": args, "call_id": call_id}
            if not quiet:
                print(f"\nstep {step:<2} PLAN   {name}({', '.join(f'{k}={json.dumps(v)}' for k, v in args.items())})")

            d = P.check(policy, name, args, state)
            if d.verdict == "refuse":
                aud.event(task_id, "tool_refused", tool=name, args=args, reason=d.reason)
                entry.update(status="refused", reason=d.reason)
                history.append(entry)
                if not quiet:
                    print(f"        POLICY REFUSED: {d.reason}")
                if policy.get("stop_on_violation", True):
                    stop = True
                    break
                continue

            if d.verdict == "approval":
                if not quiet:
                    print(f"        POLICY approval required: {d.reason}")
                ok = {"auto": True, "deny": False}.get(approve)
                if ok is None:
                    ok = ask_human(name, args)
                aud.event(task_id, "approval", tool=name, args=args, outcome="approved" if ok else "rejected", mode=approve)
                if not ok:
                    entry.update(status="rejected", reason="human rejected the action")
                    history.append(entry)
                    if not quiet:
                        print("        HUMAN  rejected; the action did not run")
                    if policy.get("stop_on_violation", True):
                        stop = True
                        break
                    continue
                if not quiet:
                    print(f"        HUMAN  approved ({approve})")
                status = "approved"
            else:
                if not quiet:
                    print(f"        POLICY allowed: {d.reason}")
                status = "allowed"

            result = T.call(name, args)
            state["calls_made"] += 1
            rid = next((v for k, v in args.items() if k.endswith("_id")), None)
            if rid is not None:
                state["records_touched"].add(rid)
            aud.event(task_id, "tool_allowed", tool=name, args=args, result=result, approval=(status == "approved"))
            entry.update(status=status, result=result)
            history.append(entry)
            if not quiet:
                print(f"        RESULT {short(result)}")

        if stop:
            last = history[-1]
            final = f"Stopped after {state['calls_made']} tool call(s): {last['tool']} was {last['status']}. {last.get('reason', '')}"
            aud.event(task_id, "task_end", final=final, steps=step, tool_calls=state["calls_made"], stopped=True)
            if not quiet:
                section("FINAL")
                print(final)
                print(f"\naudit: events for task {task_id} appended to {policy['logging']['audit_log']}")
            return history

    aud.event(task_id, "task_end", final="step limit reached", steps=max_steps, tool_calls=state["calls_made"])
    if not quiet:
        section("FINAL")
        print(f"Step limit ({max_steps}) reached without a final answer.")
    return history
