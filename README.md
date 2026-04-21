# LangSmith Lite

Observability and annotations for AI applications.

## Overview

This is a comprehensive tracing and annotation system that allows you to:
- **Manage tracing projects** - Organize traces into projects
- **Store and query traces** - Record AI execution traces with inputs, outputs, and metadata
- **Provide feedback** - Annotate traces with scores, comments, and span-level highlights
- **Create annotation queues** - Build review workflows for traces
- **Define rubrics** - Specify evaluation criteria for queue items
- **Process queues FIFO-style** - Pop traces from queues for review and mark them complete

## Getting Started

### Prerequisites

**Backend:**
- Python 3.11+
- PostgreSQL 14+ (running on localhost:5432)
- [uv](https://github.com/astral-sh/uv) package manager

**Frontend:**
- Node.js 18+
- [pnpm](https://pnpm.io/) package manager

### Quick Start

#### Backend

Run the complete backend setup with one command:
```bash
cd backend
make setup
```

This will:
1. Install all dependencies
2. Create the `langsmith` database (if it doesn't exist)
3. Run database migrations
4. Seed with sample data

Then start the backend server:
```bash
make run
```

To re-seed the data run:
```bash
make seed
```

The API will be available at http://localhost:8000

#### Frontend

Install dependencies and start the dev server:
```bash
cd client
pnpm install
pnpm dev
```

The frontend will be available at http://localhost:5173 (Vite default port)

## API

### Queues
- `POST /queues` - Create a queue
- `GET /queues` - List all queues
- `GET /queues/{queue_id}` - Get a specific queue
- `PATCH /queues/{queue_id}` - Update a queue
- `DELETE /queues/{queue_id}` - Delete a queue

### Queue Entries
- `POST /queues/{queue_id}/populate` - Add traces to a queue
- `GET /queues/{queue_id}/entries/next` - Get next pending entry
- `POST /queues/{queue_id}/entries/{entry_id}/complete` - Mark entry as complete (deletes it)
- `POST /queues/{queue_id}/entries/{entry_id}/requeue` - Re-queue an entry

### Queue Rubrics
- `POST /queues/{queue_id}/rubric` - Create a rubric item
- `GET /queues/{queue_id}/rubric` - List rubric items
- `PATCH /queues/{queue_id}/rubric/{item_id}` - Update a rubric item
- `DELETE /queues/{queue_id}/rubric/{item_id}` - Delete a rubric item

### Feedback
- `POST /feedback/batch` - Create multiple feedback items at once
- `PATCH /feedback/{feedback_id}` - Update feedback
- `DELETE /feedback/{feedback_id}` - Delete feedback

### Projects & Traces
- `POST /projects` - Create a tracing project
- `GET /projects` - List projects
- `GET /projects/{project_id}` - Get a specific project
- `DELETE /projects/{project_id}` - Delete a project
- `POST /traces` - Create a trace
- `POST /traces/query` - Query traces (filter by trace_ids, project_id, session_id)
- `GET /traces/{trace_id}` - Get a specific trace

## Database Schema

### Tables
- `tracing_projects` - Projects that contain traces
- `traces` - Individual traces with inputs, outputs, metadata
- `queues` - Annotation queues
- `queue_rubric_items` - Evaluation criteria for queues
- `queue_entries` - Entries in queues (with status field)
- `feedback` - Annotations on traces

### Key Features
- Cascade deletes: Deleting a project deletes its traces, which deletes queue entries and feedback
- FIFO ordering: Queue entries are returned in order of `added_at`
- Concurrency control: Uses `FOR UPDATE SKIP LOCKED` to prevent concurrent access to the same entry
- Span highlighting: Feedback can reference specific paths in the outputs JSON, with optional start/end indices for strings
## Development

### Code Quality

Format code with ruff:
```bash
cd backend
make format
```

Lint code with ruff and mypy:
```bash
cd backend
make lint
```

### Running Tests

The backend includes comprehensive unit tests for all endpoints (69 tests covering projects, traces, queues, rubrics, and feedback).

```bash
cd backend
make test
```

### Database Migrations

All commands should be run from the `backend` directory:

Create a new migration:
```bash
cd backend
uv run alembic revision -m "Description of changes"
```

Apply migrations:
```bash
make migrate
```

Rollback last migration:
```bash
uv run alembic downgrade -1
```

## Tech Stack

**Backend:**
- **FastAPI** - Modern async Python web framework
- **asyncpg** - High-performance PostgreSQL driver
- **Alembic** - Database migrations
- **PostgreSQL** - Database with JSONB support
- **Pydantic** - Data validation and schema management
- **pytest** - Testing framework with async support

**Frontend:**
- **React** - UI library for building interactive interfaces
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **pnpm** - Fast, efficient package manager

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
.
├── backend/                    # Backend Python service
│   ├── alembic/               # Database migrations
│   │   └── versions/
│   ├── scripts/               # Helper scripts
│   │   ├── create_db.py
│   │   └── seed_data.py
│   ├── src/
│   │   ├── routers/           # API route handlers
│   │   │   ├── queues.py
│   │   │   ├── rubrics.py
│   │   │   ├── feedback.py
│   │   │   ├── projects.py
│   │   │   └── traces.py
│   │   ├── services/          # Business logic layer
│   │   │   ├── queues.py
│   │   │   ├── rubrics.py
│   │   │   ├── feedback.py
│   │   │   ├── projects.py
│   │   │   └── traces.py
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database connection pool
│   │   ├── models.py          # SQLAlchemy models (for Alembic only)
│   │   ├── schemas.py         # Pydantic models
│   │   ├── sql_utils.py       # SQL query utilities
│   │   └── main.py            # FastAPI app
│   ├── tests/                 # Test files
│   ├── docker-compose.yml     # PostgreSQL container
│   ├── Makefile               # Common commands
│   ├── pyproject.toml         # Python dependencies
│   ├── alembic.ini            # Alembic configuration
│   └── uv.lock                # Locked dependencies
├── client/                     # Frontend React application
│   ├── src/                   # React source files
│   ├── public/                # Static assets
│   ├── package.json           # Node dependencies
│   ├── pnpm-lock.yaml         # Locked dependencies
│   ├── vite.config.ts         # Vite configuration
│   ├── tsconfig.json          # TypeScript configuration
│   └── tailwind.config.js     # Tailwind CSS configuration
├── .gitignore                 # Git ignore patterns
├── .python-version            # Python version for the project
├── INTERVIEW.md               # Interview task description
└── README.md                  # This file
```

