"""CLI entrypoint for running the Task Manager application."""

import uvicorn

from task_manager.config import get_settings


def main() -> None:
    """Run the FastAPI server via Uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "task_manager.api:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
