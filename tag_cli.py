"""Tag the sample file (or your own CSV) from the command line and write JSON lines.

    python tag_cli.py data/sample_projects.csv --backend auto > results/tags.jsonl
"""
import argparse
import json
from pathlib import Path

from greentag.evaluate import load
from greentag.tagger import tag

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--backend", default="auto", choices=["auto", "rules", "llm"])
ap.add_argument("--lang", default="Mongolian", choices=["Mongolian", "English"])
a = ap.parse_args()
for p, _ in load(Path(a.csv)):
    t, used = tag(p, backend=a.backend, lang=a.lang)
    print(json.dumps({"project_id": p.project_id, "engine": used, **t.model_dump()}, ensure_ascii=False))
