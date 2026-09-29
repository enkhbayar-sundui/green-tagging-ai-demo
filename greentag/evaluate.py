"""Benchmark a backend against the manually tagged sample set.

    python -m greentag.evaluate --backend rules
    python -m greentag.evaluate --backend llm
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from .schema import ProjectProposal
from .tagger import tag

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = ProjectProposal(project_id=r["project_id"], title=r["title"], ministry=r["ministry"],
                                budget_mnt_million=float(r["budget_mnt_million"] or 0),
                                description=r["description"], objectives=r["objectives"], location=r["location"])
            gold = {"relevance": r["gold_relevance"], "objective": r["gold_objective"],
                    "categories": set(filter(None, r["gold_categories"].split(";")))}
            yield p, gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="rules", choices=["rules", "llm"])
    ap.add_argument("--data", default=str(ROOT / "data" / "sample_projects.csv"))
    args = ap.parse_args()

    rows, rel_ok, obj_ok, tp, fp, fn, errors = [], 0, 0, 0, 0, 0, 0
    items = list(load(Path(args.data)))
    for i, (p, g) in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {p.project_id} {p.title[:50]} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            t, used = tag(p, backend=args.backend)
        except Exception as ex:
            print(f"ERROR after {time.time() - t0:.0f}s: {type(ex).__name__}: {ex}", flush=True)
            errors += 1
            continue
        print(f"{t.green_relevance} ({time.time() - t0:.1f}s, {used})", flush=True)
        pred = set(t.taxonomy_categories)
        rel_ok += t.green_relevance == g["relevance"]
        obj_ok += t.climate_objective == g["objective"]
        tp += len(pred & g["categories"]); fp += len(pred - g["categories"]); fn += len(g["categories"] - pred)
        rows.append({"id": p.project_id, "title": p.title, "gold": g["relevance"], "pred": t.green_relevance,
                     "gold_cat": ";".join(sorted(g["categories"])), "pred_cat": ";".join(sorted(pred)),
                     "review": t.needs_human_review})
    n = len(rows)
    if not n:
        print("No proposal could be tagged."); return
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    summary = {"backend": args.backend, "n": n, "relevance_accuracy": round(rel_ok / n, 3),
               "objective_accuracy": round(obj_ok / n, 3), "category_precision": round(prec, 3),
               "category_recall": round(rec, 3),
               "category_f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0, "errors": errors}
    label = args.backend
    if args.backend == "llm":
        from .llm_tagger import MODEL, PROVIDER
        label = f"llm_{PROVIDER}_{MODEL}".replace(":", "-").replace("/", "-")
    out = ROOT / "results" / f"evaluation_{label}.md"
    lines = [f"# Evaluation – {label}", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in summary.items() if k != "backend"]
    lines += ["", "| ID | Project | Gold | Predicted | Gold categories | Predicted categories | Review |",
              "|---|---|---|---|---|---|---|"]
    for r in rows:
        mark = "" if r["gold"] == r["pred"] else " ✗"
        lines.append(f"| {r['id']} | {r['title'][:55]} | {r['gold']} | {r['pred']}{mark} | {r['gold_cat']} | "
                     f"{r['pred_cat']} | {'yes' if r['review'] else ''} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
