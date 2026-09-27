import re
from statistics import mean, median

def citation_validity(answer: str, citation_count: int) -> float:
    ids = [int(x) for x in re.findall(r"\[S(\d+)\]", answer)]
    return 1.0 if ids and all(1 <= i <= citation_count for i in ids) else 0.0

def context_precision(retrieved_ids: list[str], gold_ids: list[str]) -> float:
    if not retrieved_ids: return 1.0 if not gold_ids else 0.0
    relevant = [1 if any(g in rid for g in gold_ids) else 0 for rid in retrieved_ids]
    precisions, hits = [], 0
    for rank, value in enumerate(relevant, 1):
        hits += value
        if value: precisions.append(hits / rank)
    return mean(precisions) if precisions else 0.0

def faithfulness(answer: str, contexts: list[str]) -> float:
    # Transparent local proxy: compare answer claim terms with cited snippets.
    # This is not a substitute for human review or a full evaluator model.
    if not contexts: return 1.0 if "couldn" in answer.lower() or "unavailable" in answer.lower() else 0.0
    claims = [x.strip() for x in re.split(r"[.!?。！]", answer) if x.strip() and "[S" not in x]
    if not claims: return 1.0
    joined = " ".join(contexts).lower()
    scores = []
    for claim in claims:
        terms = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", claim.lower())
        scores.append(1.0 if terms and sum(t in joined for t in terms) / len(terms) >= 0.35 else 0.0)
    return mean(scores)

def percentile(values, p):
    if not values: return 0.0
    vals = sorted(values)
    return vals[min(len(vals)-1, int(round((p / 100) * (len(vals)-1))))]
