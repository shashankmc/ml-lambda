from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

def find_current_summary(
    db: Session,
    case_id: int,
    model: str = "default",
) -> dict | None:
    """
    Query case_summary_version for a current (non-rejected) summary.
    
    Args:
        db: SQLAlchemy session
        case_id: Case ID
        model: Summarization model name
    
    Returns:
        Summary dict or None if not found
    """
    result = db.execute(
        text("""
            SELECT id, summary_text, generation_source, created_at
            FROM case_summary_version
            WHERE case_id = :case_id
              AND summarization_model = :model
              AND is_current = true
              AND rejected_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"case_id": case_id, "model": model}
    ).first()
    
    if result:
        return {
            "version_id": result[0],
            "summary_text": result[1],
            "generation_source": result[2],
            "created_at": result[3],
        }
    return None

def insert_summary_version(
    db: Session,
    case_id: int,
    summary_text: str,
    generation_source: str = "on_demand",
    model: str = "default",
    parent_version_id: int | None = None,
) -> int:
    """
    Insert a new summary version into case_summary_version.
    
    Args:
        db: SQLAlchemy session
        case_id: Case ID
        summary_text: The summary text
        generation_source: "etl" | "on_demand" | "regeneration"
        model: Model name
        parent_version_id: ID of previous version (for regeneration)
    
    Returns:
        New version ID
    """
    # Mark previous versions as not current
    db.execute(
        text("""
            UPDATE case_summary_version
            SET is_current = false
            WHERE case_id = :case_id
              AND summarization_model = :model
              AND is_current = true
              AND rejected_at IS NULL
        """),
        {"case_id": case_id, "model": model}
    )
    
    # Insert new version
    result = db.execute(
        text("""
            INSERT INTO case_summary_version
            (case_id, summary_text, generation_source, summarization_model, parent_version_id, is_current)
            VALUES (:case_id, :summary_text, :generation_source, :model, :parent_version_id, true)
            RETURNING id
        """),
        {
            "case_id": case_id,
            "summary_text": summary_text,
            "generation_source": generation_source,
            "model": model,
            "parent_version_id": parent_version_id,
        }
    )
    
    new_version_id = result.scalar()
    logger.info(f"Inserted summary version {new_version_id} for case {case_id}")
    return new_version_id
