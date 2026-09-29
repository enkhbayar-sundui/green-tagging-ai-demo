from greentag import rule_tagger
from greentag.llm_tagger import SYSTEM_PROMPT, criteria_text
from greentag.schema import GreenTag, ProjectProposal
from greentag.taxonomy import CATEGORIES


def P(desc, title="Project"):
    return ProjectProposal(project_id="T", title=title, description=desc)


def test_solar_is_green():
    t = rule_tagger.tag(P("Build a 10 MW solar plant", title="Solar plant"))
    assert t.green_relevance == "green" and "RE" in t.taxonomy_categories


def test_mongolian_text():
    t = rule_tagger.tag(P("Гэр хорооллын өрхүүдэд сайжруулсан зуух нийлүүлнэ", title="Агаарын бохирдол бууруулах"))
    assert "PP" in t.taxonomy_categories


def test_coal_is_harmful():
    assert rule_tagger.tag(P("New coal-fired power unit")).green_relevance == "harmful"


def test_output_matches_schema():
    GreenTag.model_validate(rule_tagger.tag(P("School building")).model_dump())


def test_prompt_contains_every_category():
    assert all(c.code in criteria_text() for c in CATEGORIES)
    assert "{lang}" in SYSTEM_PROMPT


def test_llm_path_with_mocked_anthropic(monkeypatch):
    """Checks the tool-use / structured-output plumbing without a network call."""
    import sys
    import types

    from greentag import llm_tagger

    captured = {}

    class Block:
        type = "tool_use"
        input = {"green_relevance": "partially_green", "climate_objective": "mitigation",
                 "taxonomy_categories": ["RE", "EE"], "sdg_goals": [7], "frameworks": ["NDC"],
                 "green_share_pct": 20, "confidence": 0.8, "rationale": "ok", "evidence": ["rooftop solar"],
                 "needs_human_review": False}

    class Messages:
        def create(self, **kw):
            captured.update(kw)
            return types.SimpleNamespace(content=[Block()])

    fake = types.SimpleNamespace(Anthropic=lambda: types.SimpleNamespace(messages=Messages()))
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    monkeypatch.setattr(llm_tagger, "PROVIDER", "anthropic")
    t = llm_tagger.tag(P("Dormitory with rooftop solar"), lang="Mongolian")
    assert t.green_relevance == "partially_green"
    assert captured["tool_choice"]["name"] == "record_green_tag"
    assert "Mongolian" in captured["system"]
    assert "Cyrillic" in captured["messages"][0]["content"]


def test_ollama_path_with_mocked_server(monkeypatch):
    import io
    import json
    import urllib.request

    from greentag import llm_tagger

    sent = {}
    answer = {"green_relevance": "green", "climate_objective": "mitigation", "taxonomy_categories": ["RE", "XX"],
              "sdg_goals": [7], "frameworks": [], "green_share_pct": 90, "confidence": 0.9, "rationale": "ok",
              "evidence": [], "needs_human_review": False}

    def fake_urlopen(req, timeout=0):
        sent.update(json.loads(req.data))
        return io.BytesIO(json.dumps({"message": {"content": json.dumps(answer)}}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm_tagger, "PROVIDER", "ollama")
    t = llm_tagger.tag(P("10 MW solar plant"))
    assert sent["format"]["title"] == "GreenTag"      # schema-constrained output requested
    assert t.taxonomy_categories == ["RE"]            # invented code "XX" filtered out


def test_ollama_retries_on_truncated_json(monkeypatch):
    import io
    import json
    import urllib.request

    from greentag import llm_tagger

    good = {"green_relevance": "green", "climate_objective": "adaptation", "taxonomy_categories": ["WA"],
            "sdg_goals": [6], "frameworks": [], "green_share_pct": 90, "confidence": 0.9,
            "rationale": "Энэ төсөл нь бохир ус цэвэрлэнэ.", "evidence": [], "needs_human_review": False}
    replies = [json.dumps(good)[:40], json.dumps(good)]      # first answer cut off, second complete
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(json.loads(req.data))
        return io.BytesIO(json.dumps({"message": {"content": replies.pop(0)}}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm_tagger, "PROVIDER", "ollama")
    t = llm_tagger.tag(P("Wastewater treatment plant"), lang="Mongolian")
    assert t.taxonomy_categories == ["WA"] and len(calls) == 2
    assert calls[1]["options"]["temperature"] == 0.3


def test_consistency_rules():
    from greentag.llm_tagger import enforce_consistency
    base = dict(sdg_goals=[7], frameworks=[], green_share_pct=50, confidence=0.9, rationale="x", evidence=[],
                needs_human_review=False)
    t = enforce_consistency(GreenTag(green_relevance="harmful", climate_objective="mitigation",
                                     taxonomy_categories=["RE", "EE", "AD"], **base))
    assert t.taxonomy_categories == [] and t.climate_objective == "none" and t.needs_human_review
    t = enforce_consistency(GreenTag(green_relevance="green", climate_objective="mitigation",
                                     taxonomy_categories=["AG", "ZZ"], **base))
    assert t.taxonomy_categories == ["AG"] and t.climate_objective == "both"
