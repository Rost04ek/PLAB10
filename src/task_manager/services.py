"""Business logic layer for Task Manager."""

from datetime import date

from task_manager.models import (
    TaskCreate,
    TaskModel,
    TaskPriority,
    TaskStatistics,
    TaskStatus,
    UserCreate,
    UserModel,
)
from task_manager.repositories import TaskRepository, UserRepository


class TaskManagerService:
    """Service coordinating users and tasks operations."""

    def __init__(
        self, task_repo: TaskRepository, user_repo: UserRepository
    ) -> None:
        self.task_repo = task_repo
        self.user_repo = user_repo

    def create_user(self, data: UserCreate) -> UserModel:
        """Create a new user."""
        return self.user_repo.create(data)

    def list_users(self) -> list[UserModel]:
        """List all registered users."""
        return self.user_repo.get_all()

    def create_task(self, data: TaskCreate) -> TaskModel:
        """Create a task, validating user existence if user_id is provided."""
        if data.user_id is not None:
            user = self.user_repo.get_by_id(data.user_id)
            if user is None:
                raise ValueError(f"User with id={data.user_id} does not exist.")
        return self.task_repo.create(data)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
        completed: bool | None = None,
    ) -> list[TaskModel]:
        """List tasks with filters."""
        return self.task_repo.list_tasks(
            status=status,
            priority=priority,
            search=search,
            completed=completed,
        )

    def change_status(self, task_id: int, status: TaskStatus) -> TaskModel:
        """Change status of an existing task."""
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            raise LookupError(f"Task with id={task_id} not found.")
        return self.task_repo.update_status(task, status)

    def assign_task(self, task_id: int, user_id: int) -> TaskModel:
        """Assign an existing task to an existing user."""
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            raise LookupError(f"Task with id={task_id} not found.")
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError(f"User with id={user_id} not found.")
        return self.task_repo.assign_user(task, user_id)

    def get_user_tasks(self, user_id: int) -> list[TaskModel]:
        """Return tasks for a specific user."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError(f"User with id={user_id} not found.")
        return self.task_repo.get_by_user(user_id)

    def get_overdue_tasks(self, today: date | None = None) -> list[TaskModel]:
        """Return overdue tasks."""
        ref_date = today or date.today()
        return self.task_repo.get_overdue(ref_date)

    def get_statistics(self, today: date | None = None) -> TaskStatistics:
        """Compute task statistics."""
        ref_date = today or date.today()
        raw = self.task_repo.get_statistics(ref_date)
        return TaskStatistics(
            total=int(raw["total"]),  # type: ignore[arg-type]
            completed=int(raw["completed"]),  # type: ignore[arg-type]
            incomplete=int(raw["incomplete"]),  # type: ignore[arg-type]
            overdue=int(raw["overdue"]),  # type: ignore[arg-type]
            by_priority=dict(raw["by_priority"]),  # type: ignore[arg-type]
        )
