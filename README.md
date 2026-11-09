# Governed analytics agent team on federated data: project template

BANA 690A, AI Governance (CSUN, Fall 2026). Final project starter. It runs end to end on the hospital consortium out of the box; your team switches it to the consortium you drew and builds from there.

## Step 0: make it yours

1. One team member clicks **Use this template** (green button), names the repo, makes it public or shares it with the instructor, and adds the team as collaborators.
2. Everyone: **Code**, **Codespaces**, **Create codespace on main**. Wait for `Setup complete`.
3. Run the three commands below. If `No module named numpy`: `python -m pip install -r requirements.txt`.

```
python run_federation.py --baselines                 # trains the federated model on config.CONSORTIUM, writes models/federated_model.json
python coordinator.py --list-questions               # the five starter questions for your consortium
python coordinator.py --approve ask --question "Which of this month's discharges at Lakeshore General are high risk, and whom should the nurses call first? Month 11."
python evaluation/run_eval.py                        # the gold set and the evaluation gate
python -m pytest -q tests/
```

## Step 1: switch to your consortium (after the Nov 16 draw)

1. `config.py`: set `CONSORTIUM` to your folder name and `HOME_MEMBER` to the member whose records your agent may score and act on.
2. `governance/federation_policy.json`: `members` must list your consortium's members exactly as in `data/consortia/<name>/schema.json`; set the floors you can defend.
3. `governance/agent_policy.json`: `data_scope` members, the action tools from your data card (`schema.json` "actions"), what is gated, what is forbidden.
4. Run `python run_federation.py --baselines`. Then `python coordinator.py --list-questions` and run each starter question.
5. Rewrite `evaluation/gold_set.json` for your consortium (keep the four adversarial shapes), then `python evaluation/run_eval.py`.

## What is here

```
config.py                 CONSORTIUM and HOME_MEMBER: the two lines you change first
data/consortia/<name>/    one CSV per member, neutral_eval.csv, DATA_CARD.md, schema.json, questions.md
fl/                       the Week 6 engine (model, FedAvg, aggregators, privacy, attacks, audit) + consortium.py (loads your folder)
run_federation.py         charter pre-check, training, gate, model card, baselines; writes models/federated_model.json
agent/                    the loop, policy as code, audit log, OpenAI planner, model tool, tool registry
specialists/              descriptive, diagnostic, predictive, prescriptive: working tools plus TODOs
coordinator.py            scripted router (no key) and the OpenAI coordinator; --question, --planner, --approve
governance/               federation_policy.json (charter), agent_policy.json (agent policy)
evaluation/               gold_set.json and run_eval.py (the evaluation gate)
tests/                    pytest: loader, policy, tools
.github/workflows/ci.yml  tests, federation, evaluation gate; evidence uploaded as an artifact
docs/                     templates for the six governance documents
artifacts/                run-time evidence (logs, gate reports, cards, eval report); ignored by git except what you commit on purpose
```

## The build, in order

| Step | What | Done when |
|---|---|---|
| 1 | Switch consortium; charter members and floors; agent policy scope and actions | `run_federation.py --baselines` PASSes with per-member accuracies; `coordinator.py` answers a starter question |
| 2 | Federation: one member difference measured and shown to matter; one defense or privacy control with its cost | Numbers in `docs/model_card.md` |
| 3 | Specialists: finish the TODO tools so all five starter questions get real answers; at least eight tools | Every starter question runs through the loop |
| 4 | Coordinator: your routing rules in `ScriptedCoordinator`; the OpenAI planner answers the cross-lens question | Cross-lens question runs with an approval and a refusal in the log |
| 5 | Gold set (20+, 5+ adversarial), eval gate threshold justified in this README; CI green; fails on a seeded regression | `evaluation/run_eval.py` and the Actions tab |
| 6 | Governance package in `docs/`; demo logs in `artifacts/demo/`; video; contribution statements | Dec 11 |

## Using the OpenAI planner

```
export OPENAI_API_KEY=sk-...          # this terminal only; never a file in the repo
python coordinator.py --planner openai --approve ask --question "..."
```

Default model `gpt-4o-mini`; set `OPENAI_MODEL` to another chat model your key can use. CI uses the scripted planner so it is deterministic and free. Rehearse the demo with both.

## Rules

Members' rows never leave their file; only model updates move. The coordinator uses `neutral_eval.csv` for evaluation only and reports per member. No real data may be added. Keys never in the repo. See the specification for grading.
