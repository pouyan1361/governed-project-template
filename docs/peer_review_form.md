# Peer review form (Nov 30)

Reviewing team: ______   Reviewed team: ______   Reviewers: ______

The reviewed team runs its cross-lens question with `--approve ask` and `python evaluation/run_eval.py`. Score each row 1 to 4.

| Rubric row | 1 | 2 | 3 | 4 | Score |
|---|---|---|---|---|---|
| Federation | Runs; overall accuracy only | Per-member table | Per-member table and the odd member found | Odd member found and a charter decision made from it | |
| Agents | One agent, no coordinator | Coordinator routes single-lens questions | Cross-lens question answered with the scripted planner | Cross-lens question with both planners; eight or more tools | |
| Governance of actions | Allow list only | Approval prompt exists | Approve and reject shown live | Approve, reject and a forbidden action refused, all in the log | |
| Evidence and CI | Tests only | Eval gate runs locally | Eval gate in CI, green | A red seeded run and a green run to show | |
| Documents | None drafted | Templates filled generically | Drafts with some of the team's numbers | Five drafts with the team's own numbers throughout | |
| Presentation readiness | No demo plan | Questions chosen | Rehearsed once | Three questions rehearsed, timed, with a fallback | |

The best thing about this system (one sentence):

The one thing to fix before Dec 7 (one sentence):
