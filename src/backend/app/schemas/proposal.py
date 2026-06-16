import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProposalCreate(BaseModel):
    theme: str = Field(..., max_length=200)


class MeasureSelect(BaseModel):
    index: int
    title: str


class DeepenRequest(BaseModel):
    selected_measures: list[MeasureSelect]
    future_vision: str = ""


class ContentUpdateRequest(BaseModel):
    content_text: str


class RefinementRequest(BaseModel):
    instruction: str


class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    municipality_name: str
    theme: str
    status: str
    content_url: str | None = None
    content_text: str | None = None
    parent_proposal_id: uuid.UUID | None = None
    # 入力フィールド
    future_vision: str | None = None
    current_state: str | None = None
    challenges: str | None = None
    root_causes: str | None = None
    reference_urls: list[str] = []
    attachment_names: list[str] = []
    refine_instruction: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("reference_urls", "attachment_names", mode="before")
    @classmethod
    def _parse_json_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else []
            except (json.JSONDecodeError, ValueError):
                return []
        if isinstance(v, list):
            return v
        return []


class EvidenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_name: str
    source_url: str | None
    excerpt: str | None
    classification: str


class ProposalDetail(ProposalRead):
    content_url: str | None
    parent_proposal_id: uuid.UUID | None
    approved_at: datetime | None
    evidence: list[EvidenceItem] = []
