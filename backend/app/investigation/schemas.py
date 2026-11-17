"""Investigation schemas for case notes, information requests, and responses."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseNoteCreate(BaseModel):
    """Request to add a note to a case."""
    model_config = ConfigDict(from_attributes=True)
    
    note_text: str


class CaseNoteResponse(BaseModel):
    """Case note response."""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int
    case_id: int
    note_text: str
    created_by_user_id: int
    created_at: datetime


class InformationRequestCreate(BaseModel):
    """Request to create an information request."""
    model_config = ConfigDict(from_attributes=True)
    
    requested_what: str
    reason: str
    due_date: datetime


class InformationRequestResponse(BaseModel):
    """Information request response."""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int
    case_id: int
    requested_what: str
    reason: str
    due_date: datetime
    status: str
    requested_by_user_id: int
    created_at: datetime


class InformationResponseCreate(BaseModel):
    """Request to record an information response."""
    model_config = ConfigDict(from_attributes=True)
    
    response_text: str


class InformationResponseResponse(BaseModel):
    """Information response response."""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int
    information_request_id: int
    response_text: str
    responded_by_user_id: int
    responded_at: datetime


# Alias schemas for consistent router naming
AddNoteRequest = CaseNoteCreate
AddNoteResponse = CaseNoteResponse
RequestInformationRequest = InformationRequestCreate
RequestInformationResponse = InformationRequestResponse
RecordResponseRequest = InformationResponseCreate
RecordResponseResponse = InformationResponseResponse
