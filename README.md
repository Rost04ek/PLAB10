# Task Manager (`task-manager`)

Production-oriented система керування завданнями (Варіант 14, Лабораторна робота №10) з підтримкою REST API (FastAPI), SQLAlchemy 2.0 persistence, конфігурацією через змінні середовища, пакуванням у Python-пакет (`wheel`/`sdist`), Docker-контейнеризацією та GitHub Actions CI/CD.

## Features
- Створення та перегляд користувачів (`/users`).
- Створення завдань із пріоритетом (`low`, `medium`, `high`), статусом (`todo`, `in_progress`, `completed`) та дедлайном (`due_date`).
- Зміна статусу завдання та призначення виконавця.
- Пошук за текстом, фільтрація за статусом, пріоритетом та станом виконання (`completed` / `incomplete`).
- Автоматичний контроль прострочених завдань (`/tasks/overdue`).
- Агрегована статистика за завданнями (`/statistics`).
- Перевірка стану сервісу через `/health`.

## Requirements
- Python 3.11+
- Docker (для контейнеризованого запуску)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS або .venv\Scripts\activate для Windows
pip install -e ".[dev]"
```

## Configuration

Скопіюйте шаблон змінних середовища:

```bash
cp .env.example .env
```

Основні змінні середовища:
- `APP_NAME` — назва застосунку (за замовчуванням `Task Manager API`).
- `ENVIRONMENT` — середовище виконання (`development`, `test`, `production`).
- `DATABASE_URL` — рядок підключення до БД (за замовчуванням `sqlite:///./tasks.db`).
- `LOG_LEVEL` — рівень логування (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

## Running Locally

```bash
uvicorn task_manager.api:app --reload
# або через CLI-скрипт встановленого пакета:
task-manager
```

Інтерактивна документація Swagger: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

## Building Package (Wheel & sdist)

```bash
python -m build
```
Артефакти створюються у директорії `dist/`:
- `task_manager-1.0.0-py3-none-any.whl`
- `task_manager-1.0.0.tar.gz`

## Running with Docker

Збірка образу:
```bash
docker build -t task-manager:1.0 .
```

Запуск контейнера з передаванням змінних середовища та persistent volume для SQLite:
```bash
docker run --rm -p 8000:8000 \
  -v task_data:/app/data \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -e DATABASE_URL=sqlite:////app/data/tasks.db \
  task-manager:1.0
```

## API Endpoints

| Метод | Endpoint | Опис |
|---|---|---|
| `GET` | `/health` | Статус працездатності сервісу та поточне середовище |
| `POST` | `/users` | Створення нового користувача |
| `GET` | `/users` | Список усіх користувачів |
| `GET` | `/users/{user_id}/tasks` | Завдання, призначені конкретному користувачу |
| `POST` | `/tasks` | Створення нового завдання |
| `GET` | `/tasks` | Список завдань (фільтри: `status`, `priority`, `completed`, `search`) |
| `GET` | `/tasks/overdue` | Список прострочених невиконаних завдань |
| `PATCH` | `/tasks/{task_id}/status` | Зміна статусу завдання |
| `PATCH` | `/tasks/{task_id}/assign` | Призначення завдання користувачу |
| `GET` | `/statistics` | Загальна статистика (total, completed, incomplete, overdue, by_priority) |

## Testing & Code Quality

```bash
ruff check .
ruff format --check .
mypy src
pytest -v --cov=task_manager
```

## CI/CD
GitHub Actions pipeline (`.github/workflows/ci.yml`) автоматично виконує перевірку коду (`ruff`), статичну типізацію (`mypy`), тести (`pytest`), збірку пакета (`python -m build`) та побудову Docker-образу при кожному `push` та `pull_request`.
