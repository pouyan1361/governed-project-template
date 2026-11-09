# Model card: <your consortium>, federated <outcome> model

Start from artifacts/federated_model_card.md (written by run_federation.py) and add what the generator cannot know.

## Intended use and prohibited uses
From your data card. Who uses the prediction, for what decision, and what it must never be used for.

## Members and data
| Member | Rows | Base rate | How this member differs (your finding) |
|---|---|---|---|

Provenance: instructor-generated synthetic data, data/consortia/<name>, generated <date>, schema.json reference statistics.

## Training
Charter version, rounds, local epochs, aggregation, clipping, secure aggregation or DP and its measured cost.

## Performance
| Member | Local only | FedAvg | Centralized | Gain |
|---|---|---|---|---|

Overall. The member difference that changed a conclusion, and what you did about it (fine-tuning, a separate model, a charter floor).

## Limitations and fairness
Per-member evaluation only unless you evaluated segments: did you? Say what you found.
