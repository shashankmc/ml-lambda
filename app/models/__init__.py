from pydantic import BaseModel
from typing import Optional, List

class SummarizeRequest(BaseModel):
    case_id: int
    ecli: str
    source: str = "local"
    caller: str = "on_demand"  # "etl" | "on_demand" | "regeneration"
    force_regenerate: bool = False

class SummaryItem(BaseModel):
    case_id: int
    summary_text: str
    version_id: int
    generation_source: str
    from_cache: bool

class SummarizeResponse(BaseModel):
    job_id: str
    status: str
    summaries: List[SummaryItem]

class SegmentRequest(BaseModel):
    text: str
    source: str = "local_upload"

class SegmentItem(BaseModel):
    start: int
    end: int
    text: str
    segment_type: str
    label: Optional[str] = None

class SegmentResponse(BaseModel):
    segments: List[SegmentItem]

class StatusResponse(BaseModel):
    status: str  # "completed" | "pending" | "failed"
    results: Optional[dict] = None
    error: Optional[str] = None
