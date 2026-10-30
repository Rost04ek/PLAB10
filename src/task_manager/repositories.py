"""Repository layer for database operations."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from task_manager.models import (
    TaskCreate,
    TaskModel,
    TaskPriority,
    TaskStatus,
    UserCreate,
    UserModel,
)


class UserRepository:
    """Repository for managing UserModel persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: UserCreate) -> UserModel:
        """Create and persist a new user."""
        user = UserModel(username=data.username, email=data.email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_all(self) -> list[UserModel]:
        """Return all users."""
        stmt = select(UserModel).order_by(UserModel.id)
        return list(self.session.scalars(stmt).all())

    def get_by_id(self, user_id: int) -> UserModel | None:
        """Find user by ID."""
        return self.session.get(UserModel, user_id)


class TaskRepository:
    """Repository for managing TaskModel persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: TaskCreate) -> TaskModel:
        """Create and persist a new task."""
        task = TaskModel(
            title=data.title,
            description=data.description,
            priority=data.priority.value,
            status=data.status.value,
            due_date=data.due_date,
            user_id=data.user_id,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> TaskModel | None:
        """Retrieve a task by ID."""
        return self.session.get(TaskModel, task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
        completed: bool | None = None,
    ) -> list[TaskModel]:
        """List tasks with optional filtering and search."""
        stmt = select(TaskModel)

        if status is not None:
            stmt = stmt.where(TaskModel.status == status.value)
        if priority is not None:
            stmt = stmt.where(TaskModel.priority == priority.value)
        if completed is not None:
            if completed:
                stmt = stmt.where(TaskModel.status == TaskStatus.COMPLETED.value)
            else:
                stmt = stmt.where(TaskModel.status != TaskStatus.COMPLETED.value)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                TaskModel.title.ilike(pattern) | TaskModel.description.ilike(pattern)
            )

        stmt = stmt.order_by(TaskModel.id)
        return list(self.session.scalars(stmt).all())

    def get_by_user(self, user_id: int) -> list[TaskModel]:
        """Return all tasks assigned to a specific user."""
        stmt = (
            select(TaskModel)
            .where(TaskModel.user_id == user_id)
            .order_by(TaskModel.id)
        )
        return list(self.session.scalars(stmt).all())

    def get_overdue(self, reference_date: date) -> list[TaskModel]:
        """Return incomplete tasks whose due_date is strictly before reference_date."""
        stmt = (
            select(TaskModel)
            .where(
                TaskModel.due_date.is_not(None),
                TaskModel.due_date < reference_date,
                TaskModel.status != TaskStatus.COMPLETED.value,
            )
            .order_by(TaskModel.due_date)
        )
        return list(self.session.scalars(stmt).all())

    def update_status(self, task: TaskModel, status: TaskStatus) -> TaskModel:
        """Update task status."""
        task.status = status.value
        self.session.commit()
        self.session.refresh(task)
        return task

    def assign_user(self, task: TaskModel, user_id: int) -> TaskModel:
        """Assign task to a user."""
        task.user_id = user_id
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_statistics(self, reference_date: date) -> dict[str, int | dict[str, int]]:
        """Calculate aggregated statistics using SQL queries."""
        total = (
            self.session.scalar(select(func.count()).select_from(TaskModel)) or 0
        )
        completed = (
            self.session.scalar(
                select(func.count())
                .select_from(TaskModel)
                .where(TaskModel.status == TaskStatus.COMPLETED.value)
            )
            or 0
        )
        incomplete = total - completed
        overdue = (
            self.session.scalar(
                select(func.count())
                .select_from(TaskModel)
                .where(
                    TaskModel.due_date.is_not(None),
                    TaskModel.due_date < reference_date,
                    TaskModel.status != TaskStatus.COMPLETED.value,
                )
            )
            or 0
        )

        priority_rows = self.session.execute(
            select(TaskModel.priority, func.count()).group_by(TaskModel.priority)
        ).all()
        by_priority: dict[str, int] = {p.value: 0 for p in TaskPriority}
        for prio, cnt in priority_rows:
            by_priority[str(prio)] = int(cnt)

        return {
            "total": total,
            "completed": completed,
            "incomplete": incomplete,
            "overdue": overdue,
            "by_priority": by_priority,
        }
