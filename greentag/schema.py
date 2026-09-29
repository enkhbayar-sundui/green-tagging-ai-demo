"""Structured input and output models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectProposal(BaseModel):
    """Fields modelled on a budget-proposal green questionnaire."""
    project_id: str
    title: str
    ministry: str = ""
    budget_mnt_million: float | None = None
    description: str
    objectives: str = ""
    location: str = ""

    def as_text(self) -> str:
        parts = [f"Title: {self.title}", f"Ministry: {self.ministry}", f"Location: {self.location}",
                 f"Budget (MNT million): {self.budget_mnt_million}", f"Description: {self.description}",
                 f"Objectives: {self.objectives}"]
        return "\n".join(p for p in parts if not p.endswith(": ") and not p.endswith(": None"))


class GreenTag(BaseModel):
    """Structured tagging result returned by every backend."""
    green_relevance: Literal["green", "partially_green", "not_green", "harmful"] = Field(
        description="green = main purpose is environmental/climate; partially_green = significant green "
                    "component; not_green = no material green effect; harmful = likely increases emissions or "
                    "environmental damage")
    climate_objective: Literal["mitigation", "adaptation", "both", "none"]
    taxonomy_categories: list[str] = Field(description="Category codes from the criteria list, e.g. ['RE','EE']")
    sdg_goals: list[int] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list, description="National frameworks the project supports")
    green_share_pct: int = Field(ge=0, le=100, description="Estimated share of budget that is green")
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(description="2-3 sentence explanation in plain language")
    evidence: list[str] = Field(default_factory=list, description="Short quotes from the proposal")
    needs_human_review: bool
