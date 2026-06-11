"""API routes for scoring and template management."""

from fastapi import APIRouter, HTTPException

from src.api.schemas.scoring import (
    ComputeScoreRequest,
    ScoreResponse,
    ScoredSubmission,
    TemplateCreateRequest,
    TemplateResponse,
)
from src.standards.scoring import ScoringEngine
from src.standards.template_manager import get_template_manager

router = APIRouter(prefix="/api/scoring", tags=["scoring"])

template_manager = get_template_manager()


@router.get("/templates")
async def list_templates():
    """List all scoring templates."""
    templates = template_manager.list_all()
    return {
        "templates": [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "is_default": t.is_default,
                "dimension_count": len(t.dimensions),
            }
            for t in templates
        ],
        "total": len(templates),
    }


@router.get("/templates/default", response_model=TemplateResponse)
async def get_default_template():
    """Get the default scoring template with all dimensions."""
    template = template_manager.get_default()
    return TemplateResponse(**template.to_dict())


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """Get a specific scoring template."""
    template = template_manager.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return TemplateResponse(**template.to_dict())


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(request: TemplateCreateRequest):
    """Create a custom scoring template."""
    template = template_manager.create(
        name=request.name,
        dimensions=[d.model_dump() for d in request.dimensions],
        description=request.description or "",
    )
    return TemplateResponse(**template.to_dict())


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a scoring template (cannot delete the default)."""
    success = template_manager.delete(template_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete default template or template not found")
    return {"message": f"Template {template_id} deleted"}


@router.post("/compute", response_model=ScoreResponse)
async def compute_score(request: ComputeScoreRequest):
    """Compute multi-dimensional scores from analysis and test results.

    Uses the specified template (or default if not provided).
    """
    # Get dimensions
    if request.template_id:
        template = template_manager.get(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {request.template_id} not found")
        dimensions = template.dimensions
    else:
        dimensions = ScoringEngine.default_dimensions()

    # Compute scores
    analysis_dict = request.analysis.model_dump() if request.analysis else {}
    test_dict = request.tests.model_dump() if request.tests else {}

    result = ScoringEngine.compute(
        analysis_result=analysis_dict,
        test_result=test_dict,
        coverage_percent=request.coverage or 0.0,
        dimensions=dimensions,
    )

    return ScoreResponse(
        overall_score=result.overall_score,
        grade=result.grade,
        dimension_scores=result.dimension_scores,
        dimension_weights=result.dimension_weights,
    )


@router.post("/compare", response_model=list[ScoredSubmission])
async def compare_submissions(submissions: list[ComputeScoreRequest]):
    """Batch score multiple submissions and return sorted rankings.

    Used for the scoring dashboard to compare all students in a project.
    """
    results = []
    for sub in submissions:
        try:
            analysis_dict = sub.analysis.model_dump() if sub.analysis else {}
            test_dict = sub.tests.model_dump() if sub.tests else {}

            dimensions = ScoringEngine.default_dimensions()
            if sub.template_id:
                template = template_manager.get(sub.template_id)
                if template:
                    dimensions = template.dimensions

            result = ScoringEngine.compute(
                analysis_result=analysis_dict,
                test_result=test_dict,
                coverage_percent=sub.coverage or 0.0,
                dimensions=dimensions,
            )
            results.append(ScoredSubmission(
                submission_id=sub.submission_id or "",
                submitter_name=sub.submitter_name or "Unknown",
                overall_score=result.overall_score,
                grade=result.grade,
                dimension_scores=result.dimension_scores,
            ))
        except Exception:
            pass

    # Sort by overall score descending
    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results