import re
import hashlib
from fastapi import APIRouter
from app.models.schemas import SegmentRequest, SegmentResponse, SegmentItem

router = APIRouter()

_PATTERNS = {
    "rechtspraak": [
        (r"\bOVERWEGINGEN\b", "considerations"),
        (r"\bBESLISSING\b", "decision"),
        (r"\bPROCESVERLOOP\b", "procedure"),
    ],
    "echr": [
        (r"Article\s+\d+", "article"),
        (r"Recital\s+\d+", "recital"),
    ],
    "cjeu": [
        (r"Judgment", "judgment"),
        (r"Article\s+\d+", "article"),
    ],
}

@router.post("/segment/ml", response_model=SegmentResponse)
def segment_ml(req: SegmentRequest):
    """
    Segment text using regex patterns based on source type.
    
    Request body:
      - text: str (full text)
      - source: str (rechtspraak, echr, cjeu, etc.)
    
    Returns:
      - segments: list of SegmentItem
    """
    patterns = _PATTERNS.get(req.source, [])
    
    segments = []
    
    if not patterns:
        # Default: split by paragraph
        parts = req.text.split("\n\n")
        for idx, part in enumerate(parts):
            if part.strip():
                segments.append(
                    SegmentItem(
                        start=req.text.find(part),
                        end=req.text.find(part) + len(part),
                        text=part.strip(),
                        segment_type="paragraph",
                    )
                )
        return SegmentResponse(segments=segments)
    
    # Find all pattern matches
    matches = []
    for pattern, seg_type in patterns:
        for match in re.finditer(pattern, req.text, re.IGNORECASE):
            matches.append((match.start(), match.end(), seg_type))
    
    # Sort by position
    matches.sort(key=lambda x: x[0])
    
    if not matches:
        # No patterns matched, return whole text
        segments.append(
            SegmentItem(
                start=0,
                end=len(req.text),
                text=req.text,
                segment_type="full_text",
            )
        )
        return SegmentResponse(segments=segments)
    
    # Create segments from matches
    for idx, (start, end, seg_type) in enumerate(matches):
        # Find the next match start or end of text
        next_start = matches[idx + 1][0] if idx + 1 < len(matches) else len(req.text)
        
        segment_text = req.text[start:next_start].strip()
        if segment_text:
            segments.append(
                SegmentItem(
                    start=start,
                    end=next_start,
                    text=segment_text,
                    segment_type=seg_type,
                )
            )
    
    return SegmentResponse(segments=segments)
