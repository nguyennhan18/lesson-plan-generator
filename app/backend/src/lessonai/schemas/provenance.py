"""Public generation provenance; metadata describes a draft, never approval."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class GenerationMetadata(BaseModel):
    model_config = ConfigDict(extra='allow')
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    task: str = Field(min_length=1)
    generated_at: int = Field(ge=0)
    prompt_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    status: Literal['unverified_draft'] = 'unverified_draft'
