"""LLM backend: sends the proposal plus the green-tagging criteria to a large
language model and forces a schema-validated JSON answer (structured output).

Providers, selected with GREENTAG_PROVIDER:
- anthropic (default) – needs ANTHROPIC_API_KEY
- openai              – needs OPENAI_API_KEY
- ollama              – free local model, no key, data never leaves the machine
                        (OLLAMA_HOST, default http://localhost:11434)
"""
from __future__ import annotations

import json
import os

from .schema import GreenTag, ProjectProposal
from .taxonomy import BY_CODE, CATEGORIES, HARMFUL_KEYWORDS

PROVIDER = os.getenv("GREENTAG_PROVIDER", "anthropic").lower()
DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini", "ollama": "qwen2.5:7b"}
MODEL = os.getenv("GREENTAG_MODEL") or DEFAULT_MODELS.get(PROVIDER, "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def criteria_text() -> str:
    lines = []
    for c in CATEGORIES:
        lines.append(f"- {c.code} | {c.name} ({c.name_mn}) | objective: {c.objective} | SDGs: "
                     f"{', '.join(map(str, c.sdgs))} | frameworks: {', '.join(c.frameworks)} | "
                     f"typical activities: {', '.join(c.keywords[:6])}")
    return "\n".join(lines)


SYSTEM_PROMPT = f"""You are an analyst supporting the Ministry of Finance of Mongolia in green budget tagging
of public investment project proposals. Proposals may be written in Mongolian or English.

Classify each proposal against these green-tagging criteria:
{criteria_text()}

Definitions of green_relevance:
- green: the main purpose of the project is one of the categories above.
- partially_green: a significant but secondary component falls in a category (e.g. a school with solar panels).
- not_green: no material environmental or climate effect.
- harmful: likely to increase greenhouse-gas emissions or cause environmental damage
  (examples: {', '.join(HARMFUL_KEYWORDS[:6])}), unless it is clearly a transition measure.

Rules:
0. Default to not_green. Use partially_green only when the proposal explicitly describes a specific green
   component (e.g. solar panels, insulation, emission controls, water recycling). Ordinary schools, roads,
   offices, hospitals and renovations are not_green even if they cite a green policy or could be "efficient".
   Infrastructure whose main purpose is to extract, transport or burn fossil fuels (coal mines, coal railways
   or haul roads, coal or diesel power) is harmful.
   If green_relevance is not_green or harmful, taxonomy_categories must be an empty list.
1. Judge the substance of the activities, not labels. A project that only uses the word "green" in its name
   without green activities is not_green ("green-washing").
2. green_share_pct = your estimate of the share of the budget spent on green activities.
3. evidence = at most 2 short verbatim quotes (under 12 words each) from the proposal.
4. rationale = at most 2 short plain sentences (under 50 words) a non-technical civil servant can
   understand, written in {{lang}}. Do not repeat yourself.
5. needs_human_review = true when the proposal is vague, mixed, possibly harmful, or confidence < 0.7.
Return only the structured result."""


def _system(lang: str) -> str:
    return SYSTEM_PROMPT.replace("{lang}", lang)


LANG_RULE = {
    "Mongolian": ("Write the \"rationale\" field in the Mongolian language using Cyrillic script "
                  "(Монгол хэлээр, кирилл үсгээр). Do not write it in English or Chinese. "
                  "Keep \"evidence\" as verbatim quotes from the proposal."),
    "English": "Write the \"rationale\" field in English.",
}


def _cyrillic_share(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    return sum("\u0400" <= ch <= "\u04ff" for ch in letters) / len(letters) if letters else 0.0


def tag(p: ProjectProposal, lang: str = "Mongolian") -> GreenTag:
    rule = LANG_RULE.get(lang, f"Write the \"rationale\" field in {lang}.")
    user = "Tag this project proposal:\n\n" + p.as_text() + "\n\n" + rule
    data = _call(_system(lang), user)
    if lang == "Mongolian" and _cyrillic_share(data.get("rationale", "")) < 0.5:
        # Small models sometimes ignore the language instruction; ask once more, more firmly.
        data = _call(_system(lang), user + "\n\nIMPORTANT: the previous answer used the wrong language. "
                     "The rationale MUST be written in Mongolian Cyrillic (жишээ: \"Энэ төсөл нь ...\").")
    return enforce_consistency(GreenTag.model_validate(data))


def enforce_consistency(t: GreenTag) -> GreenTag:
    """Deterministic rules applied after the model, so the output is internally consistent:
    - only category codes that exist in the criteria are kept;
    - not_green / harmful projects carry no green categories, objective or green share;
    - the climate objective is derived from the categories (each category defines its objective);
    - a green tag without any category is sent to human review."""
    t.taxonomy_categories = sorted({c for c in t.taxonomy_categories if c in BY_CODE})
    if t.green_relevance in ("not_green", "harmful"):
        t.taxonomy_categories, t.sdg_goals, t.green_share_pct, t.climate_objective = [], [], 0, "none"
    elif t.taxonomy_categories:
        objs = {BY_CODE[c].objective for c in t.taxonomy_categories}
        t.climate_objective = ("both" if "both" in objs or {"mitigation", "adaptation"} <= objs
                               else objs.pop())
    else:
        t.needs_human_review = True
    if t.green_relevance == "harmful":
        t.needs_human_review = True
    return t


def _call(system: str, user: str) -> dict:
    schema = GreenTag.model_json_schema()
    if PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODEL, max_tokens=1024, system=system,
            tools=[{"name": "record_green_tag", "description": "Record the green-tagging result",
                    "input_schema": schema}],
            tool_choice={"type": "tool", "name": "record_green_tag"},
            messages=[{"role": "user", "content": user}],
        )
        data = next(b.input for b in msg.content if b.type == "tool_use")
    elif PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=MODEL, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system + "\nJSON schema:\n" + json.dumps(schema)},
                      {"role": "user", "content": user}],
        )
        data = json.loads(resp.choices[0].message.content)
    elif PROVIDER == "ollama":
        # Ollama structured outputs: the JSON schema is passed in "format" and the local
        # model is constrained to produce matching JSON.
        import urllib.request
        body = json.dumps({
            "model": MODEL, "stream": False, "format": schema,
            # num_predict caps the answer length: with JSON-constrained decoding some small models
            # can otherwise keep emitting whitespace until the request times out.
            "options": {"temperature": 0, "num_predict": int(os.getenv("GREENTAG_MAX_TOKENS", "1500")),
                        "num_ctx": 4096},
            # Qwen3-family models "think" by default; off = much faster, set GREENTAG_THINK=1 to enable
            "think": os.getenv("GREENTAG_THINK", "0") == "1",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }).encode("utf-8")
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        data = None
        for attempt in range(2):
            if attempt:  # second try: nudge sampling and ask for a shorter answer
                payload = json.loads(body)
                payload["options"].update({"temperature": 0.3, "seed": 7})
                payload["messages"][-1]["content"] += ("\n\nKeep the answer short: rationale under 40 words, "
                                                      "at most 2 evidence quotes, no repetition.")
                req = urllib.request.Request(f"{OLLAMA_HOST}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=int(os.getenv("GREENTAG_TIMEOUT", "180"))) as r:
                content = json.loads(r.read())["message"]["content"]
            try:
                data = json.loads(content)
                break
            except json.JSONDecodeError:
                continue
        if data is None:
            raise RuntimeError("The local model returned incomplete JSON twice (answer cut off / looping).")
    else:
        raise ValueError(f"Unknown provider {PROVIDER}")
    return data


def ollama_running() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=2):
            return True
    except Exception:
        return False
