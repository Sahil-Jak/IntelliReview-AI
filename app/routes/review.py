import logging
import traceback
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.code_request import CodeRequest
from app.services.github_service import analyze_code_with_fix
from app.database import get_db, ReviewRecord

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/review-code")
async def review_code(request: CodeRequest, db: Session = Depends(get_db)):
    """
    Analyze submitted code using GPT-4.1-nano via GitHub Models.
    Returns multi-dimensional scores, issues, explanation, fixed code, token usage.
    """
    try:
        result = await analyze_code_with_fix(request.code, request.language)

        record = ReviewRecord(
            code            = request.code,
            language        = request.language,
            readability     = result.get("readability",     0.0),
            performance     = result.get("performance",     0.0),
            maintainability = result.get("maintainability", 0.0),
            security        = result.get("security",        0.0),
            best_practices  = result.get("best_practices",  0.0),
            overall_score   = result.get("overall_score",   0.0),
            issues          = result.get("issues",          ""),
            ai_explanation  = result.get("ai_explanation",  ""),
            fixed_code      = result.get("fixed_code",      ""),
            token_usage     = result.get("token_usage"),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return result

    except Exception as e:
        # Log full traceback internally — never expose to client
        logger.error(f"review_code error: {type(e).__name__}\n{traceback.format_exc()}")
        return {
            "readability":     0.0,
            "performance":     0.0,
            "maintainability": 0.0,
            "security":        0.0,
            "best_practices":  0.0,
            "overall_score":   0.0,
            "issues":          "An unexpected error occurred.",
            "ai_explanation":  "Internal error. Please try again.",
            "fixed_code":      "No fix generated.",
            "token_usage":     None,
        }


@router.get("/reviews")
def get_reviews(db: Session = Depends(get_db)):
    """Return the 20 most recent reviews from the database."""
    records = db.query(ReviewRecord).order_by(ReviewRecord.id.desc()).limit(20).all()
    return [
        {
            "id":              r.id,
            "language":        r.language,
            "readability":     r.readability,
            "performance":     r.performance,
            "maintainability": r.maintainability,
            "security":        r.security,
            "best_practices":  r.best_practices,
            "overall_score":   r.overall_score,
            "issues":          r.issues,
            "ai_explanation":  r.ai_explanation,
            "fixed_code":      r.fixed_code,
            "token_usage":     r.token_usage,
            "created_at":      r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]