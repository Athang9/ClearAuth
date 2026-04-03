from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PAStatus(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING_INFO = "pending_info"


class ClinicalNote(BaseModel):
    raw_text: str
    source_file: str


class ExtractedFields(BaseModel):
    patient_id: str
    patient_age: Optional[int] = None
    diagnosis_codes: list[str]
    procedure_codes: list[str]
    clinical_justification: str
    ordering_provider: str
    payer: str
    urgency: str


class PADecision(BaseModel):
    case_id: str
    status: PAStatus
    confidence_score: float
    reason: str
    missing_criteria: list[str]
    recommended_action: str


class AppealLetter(BaseModel):
    case_id: str
    denial_reason: str
    letter_text: str
    evidence_cited: list[str]
