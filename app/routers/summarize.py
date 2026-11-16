import uuid
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.models.schemas import SummarizeRequest, SummarizeResponse, SummaryItem, StatusResponse
from app.services.cache import find_current_summary, insert_summary_version
from app.services.generator import summarize_text, embed_text
from app.db import get_db
from sqlalchemy import text

router = APIRouter()

# In-memory job store (for dev; replace with Redis for production)
_jobs: dict[str, dict] = {}

@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    """
    Summarize a case: check cache, generate if needed, store result.
    
    Request body:
      - case_id: int
      - ecli: str
      - source: str (for logging)
      - caller: str ("etl" | "on_demand" | "regeneration")
      - force_regenerate: bool (default false)
    """
    job_id = str(uuid.uuid4())
    logger.info(f"[{job_id}] Starting summarization for case_id={req.case_id} (ecli={req.ecli}), has_text={bool(req.text)}, caller={req.caller}")
    
    try:
        with get_db() as db:
            if req.text:
                full_text = req.text
            else:
                if not req.case_id:
                    logger.warning(f"[{job_id}] Neither text nor case_id provided")
                    raise HTTPException(status_code=400, detail="Either text or case_id must be provided")
                # Fetch full text
                result = db.execute(
                    text("SELECT full_text FROM case_text WHERE case_id = :case_id ORDER BY created_at DESC LIMIT 1"),
                    {"case_id": req.case_id}
                ).first()
                
                if not result:
                    logger.warning(f"[{job_id}] No text found for case {req.case_id}")
                    raise HTTPException(status_code=404, detail=f"No text found for case {req.case_id}")
                
                full_text = result[0]
            
            # Check cache (unless force_regenerate or case_id is not provided)
            from_cache = False
            summary_item = None
            
            if req.case_id and not req.force_regenerate:
                cached = find_current_summary(db, req.case_id)
                if cached:
                    logger.info(f"[{job_id}] Cache hit for case {req.case_id}")
                    from_cache = True
                    summary_item = SummaryItem(
                        case_id=req.case_id,
                        summary_text=cached["summary_text"],
                        version_id=cached["version_id"],
                        generation_source=cached["generation_source"],
                        from_cache=True,
                    )
            
            # Generate if not in cache
            if not summary_item:
                logger.info(f"[{job_id}] Generating new summary...")
                summary_text = summarize_text(full_text)
                
                version_id = None
                if req.case_id:
                    # Store in DB
                    version_id = insert_summary_version(
                        db,
                        case_id=req.case_id,
                        summary_text=summary_text,
                        generation_source=req.caller,
                        model="default",
                    )
                
                summary_item = SummaryItem(
                    case_id=req.case_id,
                    summary_text=summary_text,
                    version_id=version_id,
                    generation_source=req.caller,
                    from_cache=False,
                )
                
                logger.info(f"[{job_id}] Generated summary")
        
        # Store job result
        _jobs[job_id] = {
            "status": "completed",
            "summaries": [summary_item],
            "from_cache": from_cache,
        }
        
        return SummarizeResponse(
            job_id=job_id,
            status="completed",
            summaries=[summary_item],
        )
    
    except Exception as e:
        logger.error(f"[{job_id}] Summarization failed: {e}")
        _jobs[job_id] = {"status": "failed", "error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str):
    """Get the status of a summarization job."""
    job = _jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return StatusResponse(
        status=job["status"],
        results=job.get("summaries") if job["status"] == "completed" else None,
        error=job.get("error"),
    )
