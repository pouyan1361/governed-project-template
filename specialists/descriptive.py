"""
DESCRIPTIVE SPECIALIST: what happened. Aggregates only; a member's rows never leave its file.

Working tools: summarize_member, segment_breakdown, trend_by_month.
TODO for your team: at least one more (for example compare_month_over_month, top_segments_consortium_wide).
"""
from collections import Counter, defaultdict

from agent import tools as T
from . import _data as D


@T.tool("summarize_member", "Row count, outcome rate and segment mix for one member. Aggregate only.",
        T.obj_schema({"member": ("string", "member name exactly as in the data card")}), kind="read")
def summarize_member(member):
    c = D.member(member)
    lab = D.label()
    out = {"member": member, "rows": c.n, "outcome_rate": round(float(c.y_train.mean()), 3), "segments": {}}
    for seg in D.world().segments:
        cnt = Counter(r[seg] for r in c.rows)
        out["segments"][seg] = {k: v for k, v in cnt.most_common()}
    return out


@T.tool("segment_breakdown", "Outcome rate by one segment column for one member (for example by ward or by claim_type).",
        T.obj_schema({"member": ("string", "member name"), "segment": ("string", "a segment column from the data card")}), kind="read")
def segment_breakdown(member, segment):
    c = D.member(member)
    if segment not in D.world().segments:
        return {"error": f"{segment} is not a segment column; choose from {D.world().segments}"}
    lab = D.label()
    tot, pos = Counter(), Counter()
    for r in c.rows:
        tot[r[segment]] += 1
        pos[r[segment]] += int(r[lab])
    return {"member": member, "segment": segment,
            "rates": {k: {"rows": tot[k], "outcome_rate": round(pos[k] / tot[k], 3)} for k in sorted(tot, key=lambda k: -pos[k] / tot[k])}}


@T.tool("trend_by_month", "Outcome rate by month (1 to 12) for one member.",
        T.obj_schema({"member": ("string", "member name")}), kind="read")
def trend_by_month(member):
    c = D.member(member)
    lab = D.label()
    tot, pos = defaultdict(int), defaultdict(int)
    for r in c.rows:
        m = int(r["month"])
        tot[m] += 1
        pos[m] += int(r[lab])
    rates = {m: round(pos[m] / tot[m], 3) for m in sorted(tot)}
    hi = max(rates, key=rates.get)
    lo = min(rates, key=rates.get)
    return {"member": member, "rate_by_month": rates, "highest_month": hi, "lowest_month": lo}
