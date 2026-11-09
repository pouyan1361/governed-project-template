"""
TOOL REGISTRY: what the system CAN do. Specialists register their tools here;
the policy (governance/agent_policy.json) decides which of them the agent MAY use.

    from agent import tools as T
    @T.tool("summarize_member", "One member's rows, rate and segment mix.", {...schema...}, kind="read")
    def summarize_member(member): ...

kind is one of: read (aggregate data), analyze (computation), model (prediction),
write (reversible record), act (changes the world; usually approval), never (forbidden).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
TOOLS = {}


def tool(name, description, parameters, kind="read"):
    def deco(fn):
        TOOLS[name] = {"fn": fn, "description": description, "parameters": parameters, "kind": kind}
        return fn
    return deco


def openai_schemas(names):
    return [{"type": "function", "function": {"name": n, "description": TOOLS[n]["description"], "parameters": TOOLS[n]["parameters"]}}
            for n in names if n in TOOLS]


def call(name, args):
    if name not in TOOLS:
        return {"error": f"unknown tool {name}"}
    try:
        return TOOLS[name]["fn"](**args)
    except TypeError as e:
        return {"error": f"bad arguments for {name}: {e}"}
    except Exception as e:  # a tool failure is a result, not a crash of the loop
        return {"error": f"{type(e).__name__}: {e}"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_artifact(fname, rec):
    ARTIFACTS.mkdir(exist_ok=True)
    with open(ARTIFACTS / fname, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def obj_schema(props, required=None):
    """Shorthand for a JSON schema: props = {name: (type, description)}."""
    return {"type": "object",
            "properties": {k: {"type": t, "description": d} for k, (t, d) in props.items()},
            "required": required if required is not None else list(props)}
