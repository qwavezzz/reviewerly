"""Celery tasks for verifying analyses and computing reliability scores.

The verifier implements a simple reliability scoring algorithm. It
calculates several sub‑scores based on heuristics and combines them
according to predefined weights. The result is persisted in the
``verification`` table associated with an ``analysis``.

Real implementations would inspect the underlying facts and apply
anti‑hallucination checks; here we compute deterministic scores based
on the number of sources used in the analysis.
"""

from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app
from common.database import SessionLocal
from common.models import Analysis, Verification, VerificationStatus

logger = get_task_logger(__name__)


@celery_app.task(name="verifier.verify")
def verify_analysis(analysis_id: int) -> Dict[str, Any]:
    """Verify an analysis and compute its reliability score.

    :param analysis_id: ID of the analysis to verify.
    :returns: A dict containing the verification ID and status.
    """
    session = SessionLocal()
    try:
        analysis = session.get(Analysis, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        # Determine number of sources
        source_ids = analysis.items.get("source_ids", []) if analysis.items else []
        n_sources = len(source_ids)
        # Compute sub‑scores (0–100)
        s_score = min(1.0, n_sources / 5.0) * 100  # source diversity and freshness
        c_score = 70.0  # Assume moderate consistency between sources
        t_score = 80.0  # Transparency: we include quotes and authors
        m_score = 75.0  # Model confidence: fixed for demonstration
        f_score = 85.0  # Fact check heuristics
        # Weighted sum
        final_score = (
            0.30 * s_score + 0.25 * c_score + 0.15 * t_score + 0.20 * m_score + 0.10 * f_score
        )
        # Determine status
        if final_score >= 65:
            status = VerificationStatus.PASSED
        elif final_score >= 50:
            status = VerificationStatus.FLAGGED
        else:
            status = VerificationStatus.FAILED
        # Prepare checks breakdown
        checks = {
            "S": s_score,
            "C": c_score,
            "T": t_score,
            "M": m_score,
            "F": f_score,
        }
        issues = []
        # Persist verification
        verification = Verification(
            analysis_id=analysis.id,
            checks=checks,
            reliability_score=final_score,
            issues=issues,
            status=status,
        )
        session.add(verification)
        session.commit()
        session.refresh(verification)
        logger.info(
            "Verified analysis %s with score %.2f status %s", analysis.id, final_score, status
        )
        return {
            "verification_id": verification.id,
            "reliability_score": float(final_score),
            "status": status.value,
        }
    except Exception as exc:  # noqa: B902
        session.rollback()
        logger.exception("Verification failed: %s", exc)
        raise
    finally:
        session.close()