"""API routes for project management — CRUD operations on projects."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.projects import ProjectCreateRequest, ProjectResponse
from src.common.database import get_async_db
from src.common.models import Project, Submission

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new project and persist to database."""
    project = Project(
        name=request.name,
        description=request.description,
        language=request.language,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        language=project.language,
        created_at=project.created_at.replace(tzinfo=timezone.utc).isoformat() if project.created_at else None,
        updated_at=project.updated_at.replace(tzinfo=timezone.utc).isoformat() if project.updated_at else None,
        submission_count=0,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_async_db),
):
    """List all projects with submission counts."""
    stmt = (
        select(
            Project,
            func.count(Submission.id).label("submission_count"),
        )
        .outerjoin(Submission, Project.id == Submission.project_id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    projects = []
    for row in rows:
        project = row[0]
        count = row[1] or 0
        projects.append(
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                language=project.language,
                created_at=project.created_at.replace(tzinfo=timezone.utc).isoformat() if project.created_at else None,
                updated_at=project.updated_at.replace(tzinfo=timezone.utc).isoformat() if project.updated_at else None,
                submission_count=count,
            )
        )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a single project by ID."""
    stmt = (
        select(
            Project,
            func.count(Submission.id).label("submission_count"),
        )
        .outerjoin(Submission, Project.id == Submission.project_id)
        .where(Project.id == project_id)
        .group_by(Project.id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    project = row[0]
    count = row[1] or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        language=project.language,
        created_at=project.created_at.replace(tzinfo=timezone.utc).isoformat() if project.created_at else None,
        updated_at=project.updated_at.replace(tzinfo=timezone.utc).isoformat() if project.updated_at else None,
        submission_count=count,
    )
