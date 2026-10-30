"""ORM models and Pydantic schemas for Task Manager."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from task_manager.database import Base


class TaskPriority(StrEnum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(StrEnum):
    """Task execution statuses."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class UserModel(Base):
    """SQLAlchemy model representing a user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    tasks: Mapped[list["TaskModel"]] = relationship(
        "TaskModel", back_populates="assignee", cascade="all, delete-orphan"
    )


class TaskModel(Base):
    """SQLAlchemy model representing a task."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    priority: Mapped[str] = mapped_column(
        String(20), default=TaskPriority.MEDIUM.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.TODO.value, index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    assignee: Mapped[UserModel | None] = relationship(
        "UserModel", back_populates="tasks"
    )


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)


class UserRead(BaseModel):
    """Schema for reading user data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: date | None = None
    user_id: int | None = None


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""

    status: TaskStatus


class TaskAssignUpdate(BaseModel):
    """Schema for assigning a task to a user."""

    user_id: int


class TaskRead(BaseModel):
    """Schema for reading task data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    due_date: date | None
    user_id: int | None


class TaskStatistics(BaseModel):
    """Schema for overall task statistics."""

    total: int
    completed: int
    incomplete: int
    overdue: int
    by_priority: dict[str, int]
