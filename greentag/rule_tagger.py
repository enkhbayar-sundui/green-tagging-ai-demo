"""Offline keyword baseline. Runs without an API key and gives the LLM
backend something to be benchmarked against."""
from __future__ import annotations

import re

from .schema import GreenTag, ProjectProposal
from .taxonomy import CATEGORIES, HARMFUL_KEYWORDS


def _hits(text: str, words) -> list[str]:
    return [w for w in words if re.search(r"(?<!\w)" + re.escape(w), text)]


def tag(p: ProjectProposal, lang: str = "Mongolian") -> GreenTag:
    text = p.as_text().lower()
    title = (p.title + " " + p.objectives).lower()
    cats, evidence, sdgs, fws, objs = [], [], set(), set(), set()
    strong = 0
    for c in CATEGORIES:
        h = _hits(text, c.keywords)
        if h:
            cats.append(c.code)
            evidence += h[:2]
            sdgs.update(c.sdgs)
            fws.update(c.frameworks)
            objs.add(c.objective)
            if _hits(title, c.keywords):
                strong += 1
    harm = _hits(text, HARMFUL_KEYWORDS)

    if harm and not strong:
        rel, share = "harmful", 0
    elif strong:
        rel, share = "green", 80
    elif cats:
        rel, share = "partially_green", 30
    else:
        rel, share = "not_green", 0

    if {"mitigation", "adaptation"} <= objs or "both" in objs:
        obj = "both"
    elif objs:
        obj = objs.pop()
    else:
        obj = "none"
    if rel in ("not_green", "harmful") and not cats:
        obj = "none"

    conf = 0.8 if (strong or (not cats and not harm)) else 0.5
    return GreenTag(
        green_relevance=rel, climate_objective=obj, taxonomy_categories=cats,
        sdg_goals=sorted(sdgs), frameworks=sorted(fws), green_share_pct=share, confidence=conf,
        rationale=_explain(cats, harm, lang),
        evidence=evidence + harm, needs_human_review=conf < 0.7 or bool(harm and cats),
    )


def _explain(cats, harm, lang):
    if lang == "Mongolian":
        txt = ("Түлхүүр үгийн шалгалт: " + (", ".join(cats) + " ангилалд тохирох үг илэрсэн" if cats
                                             else "ногоон ангилалд тохирох үг илрээгүй"))
        return txt + (f"; хор хөнөөлтэй үг: {', '.join(harm)}." if harm else ".")
    return ("Keyword baseline: matched " + (", ".join(cats) if cats else "no green categories")
            + (f"; harmful terms: {', '.join(harm)}" if harm else "") + ".")
