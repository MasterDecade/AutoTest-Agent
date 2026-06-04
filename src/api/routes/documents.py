"""API routes for document upload, analysis, and inspection plan management."""

import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.analyzer.document_analyzer import AnalyzedDocument, DocumentAnalyzer
from src.analyzer.inspection_plan import (
    InspectionPlan,
    InspectionPlanGenerator,
    PlanReviewRequest,
)
from src.analyzer.language_detector import LanguageDetector
from src.api.schemas.documents import (
    DocumentAnalysisResponse,
    InspectionPlanGenerateRequest,
    InspectionPlanResponse,
    PlanReviewResponse,
    PlanReviewSubmitRequest,
)
from src.llm.provider import get_provider_manager

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory storage for plans (will be replaced with DB in production)
_plans_store: dict[str, InspectionPlan] = {}


@router.post("/upload", response_model=DocumentAnalysisResponse)
async def upload_document(
    file: UploadFile = File(...),
    analyze: bool = True,
    project_context: Optional[str] = None,
):
    """Upload a document for analysis.

    Supports PDF, DOCX, MD, TXT, HTML, RST.

    If analyze=True, the document will be analyzed via LLM
    to extract testing requirements.
    """
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in DocumentAnalyzer.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}. Supported: {list(DocumentAnalyzer.SUPPORTED_FORMATS.keys())}",
        )

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extract text
        text = DocumentAnalyzer.extract_text(tmp_path)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Document contains no readable text")

        # Analyze if requested
        analysis_result = None
        if analyze:
            try:
                analysis_result = await DocumentAnalyzer.analyze_with_llm(
                    document_text=text,
                    provider_manager=get_provider_manager(),
                    additional_context=project_context or "",
                )
            except Exception as e:
                # Analysis failure shouldn't block upload
                analysis_result = AnalyzedDocument(raw_text=text[:5000])
                analysis_result.uncertainty_notes.append(f"LLM analysis failed: {str(e)}")

        return DocumentAnalysisResponse(
            file_name=file.filename,
            text_preview=text[:1000],
            text_length=len(text),
            analysis=analysis_result,
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/analyze-text", response_model=DocumentAnalysisResponse)
async def analyze_text(
    text: str,
    project_context: Optional[str] = None,
):
    """Analyze raw text content (without file upload)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text content is empty")

    try:
        analysis_result = await DocumentAnalyzer.analyze_with_llm(
            document_text=text,
            provider_manager=get_provider_manager(),
            additional_context=project_context or "",
        )
    except Exception as e:
        analysis_result = AnalyzedDocument(raw_text=text[:5000])
        analysis_result.uncertainty_notes.append(f"LLM analysis failed: {str(e)}")

    return DocumentAnalysisResponse(
        file_name="inline_text",
        text_preview=text[:1000],
        text_length=len(text),
        analysis=analysis_result,
    )


@router.post("/generate-plan", response_model=InspectionPlanResponse)
async def generate_inspection_plan(request: InspectionPlanGenerateRequest):
    """Generate an inspection plan based on code and documents.

    The plan will be pending review and must be approved
    before test execution begins.
    """
    # Detect language if not specified
    language = request.language
    if not language:
        language = LanguageDetector.from_content(request.code) or "python"

    # Analyze documents if provided
    analyzed_docs = []
    if request.document_texts:
        for doc_text in request.document_texts:
            try:
                doc = await DocumentAnalyzer.analyze_with_llm(
                    document_text=doc_text,
                    provider_manager=get_provider_manager(),
                )
                analyzed_docs.append(doc)
            except Exception:
                pass

    # Generate plan
    plan = await InspectionPlanGenerator.generate(
        project_name=request.project_name or "Unknown Project",
        code_samples=request.code,
        language=language,
        analyzed_documents=analyzed_docs or None,
        existing_test_cases=request.existing_test_cases,
        provider_manager=get_provider_manager(),
    )

    plan.project_id = request.project_id or ""
    _plans_store[plan.plan_id] = plan

    return InspectionPlanResponse(**plan.to_dict())


@router.get("/plans/{plan_id}", response_model=InspectionPlanResponse)
async def get_plan(plan_id: str):
    """Get an inspection plan by ID."""
    plan = _plans_store.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return InspectionPlanResponse(**plan.to_dict())


@router.get("/plans", response_model=list[InspectionPlanResponse])
async def list_plans(project_id: str = None, status: str = None):
    """List inspection plans, optionally filtered."""
    plans = list(_plans_store.values())
    if project_id:
        plans = [p for p in plans if p.project_id == project_id]
    if status:
        plans = [p for p in plans if p.status == status]
    return [InspectionPlanResponse(**p.to_dict()) for p in plans]


@router.post("/plans/{plan_id}/review", response_model=PlanReviewResponse)
async def review_plan(plan_id: str, review: PlanReviewSubmitRequest):
    """Submit a review decision for an inspection plan.

    approve=True: Plan is approved and ready for execution.
    approve=False: Plan is rejected; modifications can be suggested.
    """
    plan = _plans_store.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    from datetime import datetime, timezone

    if review.approve:
        plan.status = "approved"
        plan.reviewed_at = datetime.now(timezone.utc).isoformat()
        plan.reviewed_by = review.reviewer_name or "anonymous"
        plan.reviewer_notes = review.reviewer_notes or ""

        # Apply modifications if provided
        if review.modified_test_cases:
            plan.test_cases_plan = review.modified_test_cases
        if review.modified_scoring_dimensions:
            plan.scoring_dimensions = review.modified_scoring_dimensions
        if review.modified_code_style_checks:
            plan.code_style_checks = review.modified_code_style_checks

        return PlanReviewResponse(
            plan_id=plan_id,
            status="approved",
            message="Plan has been approved and is ready for execution",
        )
    else:
        plan.status = "rejected"
        plan.reviewed_at = datetime.now(timezone.utc).isoformat()
        plan.reviewed_by = review.reviewer_name or "anonymous"
        plan.reviewer_notes = review.reviewer_notes or "No reason provided"

        return PlanReviewResponse(
            plan_id=plan_id,
            status="rejected",
            message=f"Plan rejected. Reason: {plan.reviewer_notes}",
        )