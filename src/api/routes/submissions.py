"""API routes for code file submission — upload, extract, and store code for testing."""

import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analyzer.language_detector import LanguageDetector
from src.api.schemas.submissions import (
    BatchUploadResponse,
    SubmissionFileInfo,
    SubmissionListResponse,
    SubmissionUploadResponse,
)
from src.common.database import get_async_db
from src.common.models import Project, Submission

router = APIRouter(prefix="/api/projects", tags=["submissions"])

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Supported code file extensions for language detection
SUPPORTED_CODE_EXTENSIONS = set(LanguageDetector.get_supported_extensions())


def _detect_language_from_zip(file_list: list[dict]) -> Optional[str]:
    """Detect the primary language from extracted zip contents."""
    lang_counts: dict[str, int] = {}
    for f in file_list:
        ext = Path(f["file_name"]).suffix.lower()
        lang = LanguageDetector.from_file_extension(f["file_name"])
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    if not lang_counts:
        return None
    return max(lang_counts, key=lang_counts.get)


def _extract_zip(zip_path: str, extract_dir: str) -> list[dict]:
    """Extract a zip file and return list of extracted files.

    Args:
        zip_path: Path to the zip file.
        extract_dir: Directory to extract into.

    Returns:
        List of dicts with file_name, file_path, language, size_bytes.
    """
    files = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            # Skip directories and hidden files
            if member.endswith("/") or member.startswith("__MACOSX") or member.startswith("."):
                continue
            # Skip files in hidden directories
            if any(part.startswith(".") for part in member.split("/") if part):
                continue

            # Extract file
            zf.extract(member, extract_dir)
            extracted_path = Path(extract_dir) / member
            ext = Path(member).suffix.lower()

            if ext in SUPPORTED_CODE_EXTENSIONS:
                lang = LanguageDetector.from_file_extension(member)
                try:
                    size = extracted_path.stat().st_size
                except OSError:
                    size = 0
                files.append({
                    "file_name": Path(member).name,
                    "file_path": member,
                    "language": lang,
                    "size_bytes": size,
                })

    return files


@router.post("/{project_id}/submissions/upload", response_model=SubmissionUploadResponse)
async def upload_submission(
    project_id: str,
    files: list[UploadFile] = File(...),
    submitter_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db),
):
    """Upload code files or zip archives for a project.

    Supports:
    - Single source file (e.g., main.py)
    - Multiple source files
    - Zip archive containing a multi-file project (preserves directory structure)
    """
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    all_files: list[dict] = []
    extracted_dir = None

    for file in files:
        # Save uploaded file to temp location
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if suffix == ".zip":
                # Extract zip archive
                extract_dir = os.path.join(UPLOAD_DIR, project_id)
                zip_files = _extract_zip(tmp_path, extract_dir)
                all_files.extend(zip_files)
            elif suffix in SUPPORTED_CODE_EXTENSIONS:
                # Single code file - copy to uploads
                dest_dir = os.path.join(UPLOAD_DIR, project_id)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, file.filename)
                with open(dest_path, "wb") as f:
                    f.write(content)

                lang = LanguageDetector.from_file_extension(file.filename)
                all_files.append({
                    "file_name": file.filename,
                    "file_path": file.filename,
                    "language": lang,
                    "size_bytes": len(content),
                })
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {suffix}. Supported: {sorted(SUPPORTED_CODE_EXTENSIONS)} or .zip",
                )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if not all_files:
        raise HTTPException(status_code=400, detail="No valid code files found in upload")

    # Detect primary language
    detected_language = _detect_language_from_zip(all_files)

    # Create submission record
    file_names = "; ".join(f["file_path"] for f in all_files[:5])
    if len(all_files) > 5:
        file_names += f" (+{len(all_files) - 5} more)"

    submission = Submission(
        project_id=project_id,
        submitter_name=submitter_name,
        file_name=file_names[:500],
        code_content=None,  # Files stored on disk
        language=detected_language or project.language,
        status="pending",
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return SubmissionUploadResponse(
        submission_id=submission.id,
        project_id=project_id,
        submitter_name=submitter_name,
        files=[
            SubmissionFileInfo(
                file_name=f["file_name"],
                file_path=f["file_path"],
                language=f.get("language"),
                size_bytes=f.get("size_bytes", 0),
            )
            for f in all_files
        ],
        detected_language=detected_language,
        total_files=len(all_files),
        status=submission.status,
    )


@router.get("/{project_id}/submissions", response_model=list[SubmissionListResponse])
async def list_submissions(
    project_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """List all code submissions for a project."""
    stmt = (
        select(Submission)
        .where(Submission.project_id == project_id)
        .order_by(Submission.submitted_at.desc())
    )
    result = await db.execute(stmt)
    submissions = result.scalars().all()

    return [
        SubmissionListResponse(
            submission_id=s.id,
            project_id=s.project_id,
            submitter_name=s.submitter_name,
            file_name=s.file_name,
            language=s.language,
            status=s.status,
            submitted_at=s.submitted_at.replace(tzinfo=timezone.utc).isoformat() if s.submitted_at else None,
            completed_at=s.completed_at.replace(tzinfo=timezone.utc).isoformat() if s.completed_at else None,
        )
        for s in submissions
    ]


@router.post("/{project_id}/submissions/batch", response_model=BatchUploadResponse)
async def batch_upload_submissions(
    project_id: str,
    files: list[UploadFile] = File(...),
    submitter_names: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db),
):
    """Batch upload: multiple students' submissions for the same project.

    submitter_names is a comma-separated string mapping to files.
    Each file group belongs to one submitter.
    """
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Parse submitter names
    names = []
    if submitter_names:
        names = [n.strip() for n in submitter_names.split(",") if n.strip()]

    responses = []

    for i, file in enumerate(files):
        submitter = names[i] if i < len(names) else f"submitter_{i + 1}"

        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            all_files: list[dict] = []

            if suffix == ".zip":
                extract_dir = os.path.join(UPLOAD_DIR, project_id, submitter)
                zip_files = _extract_zip(tmp_path, extract_dir)
                all_files.extend(zip_files)
            elif suffix in SUPPORTED_CODE_EXTENSIONS:
                dest_dir = os.path.join(UPLOAD_DIR, project_id, submitter)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, file.filename)
                with open(dest_path, "wb") as f:
                    f.write(content)

                lang = LanguageDetector.from_file_extension(file.filename)
                all_files.append({
                    "file_name": file.filename,
                    "file_path": file.filename,
                    "language": lang,
                    "size_bytes": len(content),
                })

            if not all_files:
                continue

            detected_language = _detect_language_from_zip(all_files)

            file_names = "; ".join(f["file_path"] for f in all_files[:5])
            if len(all_files) > 5:
                file_names += f" (+{len(all_files) - 5} more)"

            submission = Submission(
                project_id=project_id,
                submitter_name=submitter,
                file_name=file_names[:500],
                language=detected_language or project.language,
                status="pending",
            )
            db.add(submission)
            await db.commit()
            await db.refresh(submission)

            responses.append(SubmissionUploadResponse(
                submission_id=submission.id,
                project_id=project_id,
                submitter_name=submitter,
                files=[
                    SubmissionFileInfo(
                        file_name=f["file_name"],
                        file_path=f["file_path"],
                        language=f.get("language"),
                        size_bytes=f.get("size_bytes", 0),
                    )
                    for f in all_files
                ],
                detected_language=detected_language,
                total_files=len(all_files),
                status=submission.status,
            ))

        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return BatchUploadResponse(
        submissions=responses,
        total=len(responses),
        message=f"Successfully uploaded {len(responses)} submissions",
    )
