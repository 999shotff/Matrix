from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Model / connection settings (Settings modal in the UI)
# ---------------------------------------------------------------------------

class ModelSettings(BaseModel):
    base_url: str = Field(..., description="NVIDIA NIM or any OpenAI-compatible base URL")
    api_key: Optional[str] = Field(None, description="API key, if the endpoint requires one")
    model: str = Field(..., description="Model name, e.g. matraix/persona-8b")


# ---------------------------------------------------------------------------
# Step 1 — Source
# ---------------------------------------------------------------------------

class SourceInput(BaseModel):
    mode: str = Field(..., description="'search' or 'upload'")
    search_query: Optional[str] = None
    uploaded_file_ids: List[str] = Field(default_factory=list)
    syllabus: str = Field(..., description="Free-text description of chapters/topics to cover")


# ---------------------------------------------------------------------------
# Step 2 — Pattern
# ---------------------------------------------------------------------------

class PatternInput(BaseModel):
    uploaded_file_ids: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(
        None, description="Free-text pattern description if no file was uploaded"
    )


# ---------------------------------------------------------------------------
# Step 3 — Teacher behaviour (optional)
# ---------------------------------------------------------------------------

class TeacherBehaviourInput(BaseModel):
    enabled: bool = False
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Step 4 — PYQs (optional)
# ---------------------------------------------------------------------------

class PYQInput(BaseModel):
    enabled: bool = False
    uploaded_file_ids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Full generation request
# ---------------------------------------------------------------------------

class DifficultyFloor(str, Enum):
    """Questions must never be simpler than this, regardless of source material."""
    class9_and_above = "class9_and_above"


class GenerateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    session_id: str
    source: SourceInput
    pattern: PatternInput
    teacher_behaviour: TeacherBehaviourInput = TeacherBehaviourInput()
    pyq: PYQInput = PYQInput()
    difficulty_floor: DifficultyFloor = DifficultyFloor.class9_and_above
    model_settings: Optional[ModelSettings] = None  # falls back to server default / .env


# ---------------------------------------------------------------------------
# Structured output the model is asked to return
# ---------------------------------------------------------------------------

class Question(BaseModel):
    number: str
    text: str
    marks: int
    source_alignment: str = Field(
        "", description="Short note on which part of the source this maps to"
    )
    importance_weight: float = Field(
        0.5, ge=0.0, le=1.0, description="0-1 — how important/likely-to-be-asked this is"
    )
    origin: str = Field(
        "generated", description="'source' | 'pyq_pattern' | 'generated'"
    )


class Section(BaseModel):
    name: str
    instructions: str = ""
    questions: List[Question]


class QuestionPaper(BaseModel):
    title: str
    total_marks: int
    duration_minutes: Optional[int] = None
    sections: List[Section]
    important_topic_weight_pct: float = Field(
        0.0, description="Overall % of paper weighted toward historically-important topics"
    )
    newly_composed_count: int = 0
    notes: str = ""


class GenerateResponse(BaseModel):
    session_id: str
    paper: QuestionPaper
    pdf_url: str
    raw_model_notes: Optional[str] = None
