"""Single entry point that picks a backend."""
from __future__ import annotations

import os

from . import rule_tagger
from .schema import GreenTag, ProjectProposal


def llm_available() -> bool:
    provider = os.getenv("GREENTAG_PROVIDER", "anthropic").lower()
    if provider == "ollama":
        from .llm_tagger import ollama_running
        return ollama_running()
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))


def tag(p: ProjectProposal, backend: str = "auto", lang: str = "Mongolian") -> tuple[GreenTag, str]:
    if backend == "rules" or (backend == "auto" and not llm_available()):
        return rule_tagger.tag(p, lang=lang), "rules"
    from . import llm_tagger
    return llm_tagger.tag(p, lang=lang), "llm"
