# Consortium data for the final project

Six consortia, one per team, assigned on Nov 16. Each folder holds one CSV per member (features in human units, descriptive columns, the label), the coordinator's `neutral_eval.csv` tagged by source member, a `DATA_CARD.md` (what the columns mean, reference means and sds for standardization, intended and prohibited uses, the prescriptive actions to govern) and `questions.md` (five starter business questions, one per lens and one that crosses lenses).

| Folder | Consortium | Members | Outcome |
|---|---|---|---|
| hospitals | Lakeshore Readmission Consortium | 5 hospitals | readmitted_30d |
| insurer | Sierra Mutual Claims Fraud Consortium | 4 regional offices | fraud_flag |
| bank | Cascade Community Banks Credit Consortium | 5 banks | default_12m |
| campus | Nazarian Advising Consortium | 4 departments | failed_course |
| retail | Pacific Peak Outdoor Stores Replenishment Consortium | 6 stores | stockout_next_week |
| security | Granite MSSP Alert Triage Consortium | 4 tenants | true_incident |

Rules: a member's rows never leave that member's file in your federation code (each member trains on its own CSV; only model updates move). The coordinator may use `neutral_eval.csv` for evaluation only. Standardize with the reference means and sds in the data card. Everything is synthetic; nothing here is a real person or record. The generator and ground truth stay with the instructor.
