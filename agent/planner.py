"""
PLANNERS decide the next action. Interface:  next_actions(task, history) -> list of actions
  {"type": "tool", "name": ..., "args": {...}}   or   {"type": "final", "text": "..."}

OpenAIPlanner lives here (function calling). The scripted planner for your consortium lives in
coordinator.py (ScriptedCoordinator), because its routing rules are about your questions, not about the loop.
The loop, policy and audit log do not care which planner is in charge.
"""
import json
import os

from . import tools as T


class OpenAIPlanner:
    name = "openai"

    def __init__(self, policy, system_prompt, expose="all"):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise SystemExit("The openai package is missing: python -m pip install -r requirements.txt") from e
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY is not set. In the terminal:  export OPENAI_API_KEY=sk-...")
        self.client = OpenAI()
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        names = list(T.TOOLS) if expose == "all" else policy["allowed_tools"]
        self.schemas = T.openai_schemas(names)
        self.messages = [{"role": "system", "content": system_prompt}]

    def next_actions(self, task, history):
        if not history:
            self.messages.append({"role": "user", "content": task})
        else:
            for h in history:
                if h.get("_returned"):
                    continue
                h["_returned"] = True
                content = json.dumps(h["result"], default=str) if h["status"] in ("allowed", "approved") else f"REFUSED by policy ({h['status']}): {h.get('reason', '')}"
                self.messages.append({"role": "tool", "tool_call_id": h["call_id"], "content": content})
        kw = dict(model=self.model, messages=self.messages, tools=self.schemas, tool_choice="auto")
        if self.model.startswith("gpt-4"):
            kw["temperature"] = 0
        resp = self.client.chat.completions.create(**kw)
        msg = resp.choices[0].message
        self.messages.append(msg)
        if msg.tool_calls:
            out = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                out.append({"type": "tool", "name": tc.function.name, "args": args, "call_id": tc.id})
            return out
        return [{"type": "final", "text": msg.content or ""}]
