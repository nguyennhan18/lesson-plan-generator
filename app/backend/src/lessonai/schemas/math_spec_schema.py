"""Contracts for the math gate: one status per math claim, proof records bound to a claim hash."""
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

ClaimStatus = Literal["verified", "unverified", "failed"]
_SYMBOL = r"^[A-DF-Za-z]$"  # one letter; E is the constant e


class MathFunction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variable: str = Field(default="x", pattern=_SYMBOL, description="Biến của hàm")
    parameters: List[str] = Field(default_factory=list, max_length=2, description="Tên tham số thực")
    expression: str = Field(min_length=1, max_length=500, description="Công thức hàm theo biến và tham số")

    @model_validator(mode="after")
    def distinct_real_symbols(self) -> "MathFunction":
        names = [self.variable, *self.parameters]
        if any(not re.fullmatch(_SYMBOL, name) for name in self.parameters) or len(set(names)) != len(names):
            raise ValueError("Tham số phải là một chữ cái, khác biến và không trùng nhau")
        return self


class MathClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100, description="ID ổn định của mệnh đề")
    kind: str = Field(min_length=1, max_length=50, description="Loại mệnh đề, ví dụ derivative")
    expression: str = Field(min_length=1, max_length=500, description="Biểu thức nhãn được khẳng định")


class MathSpecVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function: MathFunction
    claims: List[MathClaim] = Field(min_length=1, max_length=50)


class VerificationCheck(BaseModel):
    name: str
    version: str


class ClaimStatement(BaseModel):
    function: MathFunction
    kind: str
    expression: str


class VerificationRecord(BaseModel):
    statement: ClaimStatement
    claim_hash: str
    hash_version: int
    check: VerificationCheck
    scope: str
    method: str


class ClaimResult(BaseModel):
    id: str
    kind: str
    status: ClaimStatus
    reason: str
    claim_hash: str
    hash_version: int
    record: Optional[VerificationRecord] = None


class MathSpecVerifyResponse(BaseModel):
    claims: List[ClaimResult]
