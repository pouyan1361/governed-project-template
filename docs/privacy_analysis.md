# Privacy analysis

## What the federation protects
Rows never leave a member (how your loader and run_federation.py guarantee it).

## What it does not protect (Week 6)
Updates can leak (gradient reconstruction with small batches); a member can poison the model; the coordinator sees updates unless secure aggregation is on; membership inference against the model.

## The control you implemented and its measured cost
Secure aggregation, DP noise, clipping or robust aggregation: the accuracy cost per member from your runs.

## Residual risk and who accepts it
