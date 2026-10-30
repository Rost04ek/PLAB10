"""FastAPI application and endpoints for Task Manager (Variant 14)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from task_manager.config import get_settings
from task_manager.database import Base, engine, get_db
from task_manager.models import (
    TaskAssignUpdate,
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatistics,
    TaskStatus,
    TaskStatusUpdate,
    UserCreate,
    UserRead,
)
from task_manager.repositories import TaskRepository, UserRepository
from task_manager.services import TaskManagerService

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables on startup."""
    Base.metadata.create_all(bind=engine)
    logger.info(
        "Application '%s' started in '%s' mode",
        settings.app_name,
        settings.environment,
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-oriented Task Management System REST API",
    lifespan=lifespan,
)


def get_service(db: Session = Depends(get_db)) -> TaskManagerService:
    """Dependency injection for TaskManagerService."""
    return TaskManagerService(
        task_repo=TaskRepository(db),
        user_repo=UserRepository(db),
    )


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Healthcheck endpoint for Docker and monitoring."""
    return {
        "status": "ok",
        "environment": settings.environment,
    }


@app.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def create_user(
    payload: UserCreate,
    service: TaskManagerService = Depends(get_service),
) -> UserRead:
    """Register a new user."""
    user = service.create_user(payload)
    return UserRead.model_validate(user)


@app.get("/users", response_model=list[UserRead], tags=["Users"])
def list_users(
    service: TaskManagerService = Depends(get_service),
) -> list[UserRead]:
    """Get all users."""
    return [UserRead.model_validate(u) for u in service.list_users()]


@app.get("/users/{user_id}/tasks", response_model=list[TaskRead], tags=["Users"])
def get_user_tasks(
    user_id: int,
    service: TaskManagerService = Depends(get_service),
) -> list[TaskRead]:
    """Get all tasks assigned to a specific user."""
    try:
        tasks = service.get_user_tasks(user_id)
        return [TaskRead.model_validate(t) for t in tasks]
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(
    payload: TaskCreate,
    service: TaskManagerService = Depends(get_service),
) -> TaskRead:
    """Create a new task."""
    try:
        task = service.create_task(payload)
        return TaskRead.model_validate(task)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@app.get("/tasks", response_model=list[TaskRead], tags=["Tasks"])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = Query(default=None),
    search: str | None = Query(default=None),
    completed: bool | None = Query(default=None),
    service: TaskManagerService = Depends(get_service),
) -> list[TaskRead]:
    """List tasks with optional filtering by status, priority, completion, or search query."""
    tasks = service.list_tasks(
        status=status_filter,
        priority=priority,
        search=search,
        completed=completed,
    )
    return [TaskRead.model_validate(t) for t in tasks]


@app.get("/tasks/overdue", response_model=list[TaskRead], tags=["Tasks"])
def list_overdue_tasks(
    service: TaskManagerService = Depends(get_service),
) -> list[TaskRead]:
    """Get all overdue incomplete tasks."""
    tasks = service.get_overdue_tasks()
    return [TaskRead.model_validate(t) for t in tasks]


@app.patch("/tasks/{task_id}/status", response_model=TaskRead, tags=["Tasks"])
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    service: TaskManagerService = Depends(get_service),
) -> TaskRead:
    """Update status of a task."""
    try:
        task = service.change_status(task_id, payload.status)
        return TaskRead.model_validate(task)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@app.patch("/tasks/{task_id}/assign", response_model=TaskRead, tags=["Tasks"])
def assign_task(
    task_id: int,
    payload: TaskAssignUpdate,
    service: TaskManagerService = Depends(get_service),
) -> TaskRead:
    """Assign task to a user."""
    try:
        task = service.assign_task(task_id, payload.user_id)
        return TaskRead.model_validate(task)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@app.get("/statistics", response_model=TaskStatistics, tags=["Statistics"])
def get_statistics(
    service: TaskManagerService = Depends(get_service),
) -> TaskStatistics:
    """Get aggregated task statistics (completed, incomplete, overdue, by priority)."""
    return service.get_statistics()
