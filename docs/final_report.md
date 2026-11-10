# Final report: <team>, <consortium>

About ten pages plus appendices. Every number in this report must be traceable to an artifact in this repo (a gate report, an audit log line, an eval report, a CI run). Name the artifact next to the number.

## 1. Executive summary (half a page)
The consortium. The question the system answers. The one-sentence result: what the agents can do, what they may do, what the evidence shows.

## 2. The consortium and the questions (1 page)
Who the members are and why they cannot pool data. Sizes and base rates per member. The five business questions and the lens each needed.

## 3. The federation (2 pages)
Baselines per member: local only, FedAvg, centralized. The member differences you found and how you found them (which tools, which signs). The one difference that changed a conclusion, and the charter line it produced. The privacy or defense control you measured and its cost per member. The final charter version and the gate result (artifact: federation_gate_report.json, federated_model_card.md).

## 4. The agent team (2 pages)
Architecture: coordinator, four specialists, the tools table with kinds. One real cross-lens trace from your system (artifact: artifacts/demo/). The two planners compared: routes, tool counts, pass rates. What the language model did that the rule book did not, for better and for worse.

## 5. Governance of actions (1.5 pages)
The policy file explained: allowed, approval, forbidden, scope, budgets, model floor. The approval design: what the human sees, who decides. Audit log evidence: counts of calls, refusals, approvals, rejections, with two or three quoted lines. The adversarial cases and what held.

## 6. Evaluation and pipeline (1 page)
The gold set: how many, which lenses, the five adversarial shapes. The threshold and why. The seeded regression: links to the red run and the green run. What the pipeline would catch that a human review would not.

## 7. Risks, privacy and monitoring (1 page)
Top five register rows with mitigations pointing into the repo. Privacy in brief: protected, not protected, residual risk and who accepts it. Monitoring: who reads the log, how often, which signals pull the agent, rollback.

## 8. Reflection (1 page)
What you would tell a company adopting this design: three things that worked, two that did not, one you would do differently. Where the governance was theater and where it was real.

## Appendices
A. Model card (docs/model_card.md)   B. Agent card (docs/agent_card.md)   C. Risk register   D. Privacy analysis   E. Approval design   F. Deployment and monitoring plan   G. Contribution statements (docs/contributions.md)   H. The three demo traces (artifacts/demo/)
