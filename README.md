# AML Transaction Monitoring Platform

An AI-powered Anti-Money Laundering (AML) transaction monitoring platform that screens transactions using deterministic rules, generates alerts, and supports end-to-end case investigation and decisioning workflows.

## Architecture

- **Backend**: Python 3.11+ with FastAPI framework
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite (local development), PostgreSQL (deployed environments)
- **Auth**: JWT-based authentication with role-based access control

## Features

- Transaction ingestion with eight deterministic AML rule evaluation
- Risk-based alert generation with priority scoring
- Case management with state machine-driven workflows
- Separation-of-duties enforcement for case decisions
- Immutable audit trail across all workflow events
- Role-based access control (Analyst, Officer, Manager, Admin, Auditor)

## Prerequisites

- **Python 3.11 or higher** - [Download Python](https://python.org)
- **Node.js 18 or higher** - [Download Node.js](https://nodejs.org)
- **Git Bash** (Windows users only) - [Download Git for Windows](https://git-scm.com/download/win)

## Quick Start

### Local Development

**All platforms (Linux, macOS, Windows):**

```bash
./start.sh
```

**Windows users can also use:**

```batch
start.bat
```

The startup script will:
1. Check prerequisites (Python 3.11+, Node.js 18+)
2. Create Python virtual environment and install backend dependencies
3. Install frontend dependencies
4. Apply database migrations
5. Seed default users and reference data
6. Start the backend API server (auto-detected port, default 9000)
7. Start the frontend development server (auto-detected port, default 5173)

### Stop Services

```bash
./stop.sh
```

Or on Windows:

```batch
stop.bat
```

### Access Points

After starting the application:

- **Frontend**: http://127.0.0.1:5173 (port may vary)
- **Backend API**: http://127.0.0.1:9000 (port may vary)
- **API Documentation**: http://127.0.0.1:9000/docs
- **ReDoc**: http://127.0.0.1:9000/redoc

**Note:** The startup script will display the actual ports if defaults are unavailable.

### Default Credentials

Use these credentials to log in to the application:

| Role | Email | Password |
|------|-------|----------|
| **Analyst** | analyst@example.com | Analyst-pass-1 |
| **Officer** | officer@example.com | Officer-pass-1 |
| **Manager** | manager@example.com | Manager-pass-1 |
| **Admin** | admin@example.com | Admin-pass-1 |
| **Auditor** | auditor@example.com | Auditor-pass-1 |

## API Documentation

All API routes are mounted at the prefix: `/api/v1`

Examples:
- Transaction ingestion: `POST /api/v1/transactions/`
- Transaction detail: `GET /api/v1/transactions/{id}`
- Alert detail: `GET /api/v1/alerts/{id}`
- Case creation: `POST /api/v1/cases/`
- Case detail: `GET /api/v1/cases/{id}`

Interactive API documentation is available at:
- **Swagger UI**: http://127.0.0.1:9000/docs
- **ReDoc**: http://127.0.0.1:9000/redoc

## Docker Deployment

### Build and Run with Docker Compose

```bash
docker compose up --build
```

This will:
- Build both backend and frontend Docker images
- Run database migrations automatically
- Seed default users and reference data
- Start all services

### Verify Running Containers

```bash
docker compose ps
```

You should see both `backend` and `frontend` services running.

### Access the Application

- **Frontend**: http://127.0.0.1:80
- **Backend API**: Internal only (accessed through frontend proxy at `/api`)

### Stop Docker Services

```bash
docker compose down
```

### Clean Up (Including Volumes)

```bash
docker compose down -v
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration from environment
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── seed.py              # Database seeding script
│   │   ├── common/              # Cross-cutting concerns (enums, errors, pagination)
│   │   ├── security/            # Authentication and authorization
│   │   ├── customer/            # Customer and account management
│   │   ├── transaction/         # Transaction ingestion and screening
│   │   ├── rules/               # Rule evaluation engine
│   │   ├── alert/               # Alert generation and management
│   │   ├── case_management/     # Case lifecycle and state machine
│   │   ├── investigation/       # Notes, information requests, responses
│   │   ├── risk/                # Country risk reference data
│   │   └── audit/               # Audit event logging
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Migration scripts
│   ├── tests/                   # Backend tests
│   ├── pyproject.toml           # Python dependencies
│   ├── alembic.ini              # Alembic configuration
│   ├── dev.env                  # Default development environment variables
│   ├── Dockerfile               # Backend container image
│   └── docker-entrypoint.sh     # Container startup script
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # Vite entry point
│   │   ├── App.tsx              # Router and auth wrapper
│   │   ├── lib/                 # API client, auth context, utils
│   │   ├── components/          # Reusable UI components
│   │   │   ├── auth/            # Login, require auth
│   │   │   ├── layout/          # Header, sidebar, layout
│   │   │   ├── alerts/          # Alert components
│   │   │   ├── cases/           # Case components
│   │   │   └── transactions/    # Transaction components
│   │   ├── features/            # Feature-scoped pages
│   │   │   ├── auth/            # Login page
│   │   │   ├── dashboard/       # Dashboard
│   │   │   ├── transactions/    # Transaction pages
│   │   │   ├── alerts/          # Alert pages
│   │   │   └── cases/           # Case pages
│   │   └── types/               # TypeScript interfaces
│   ├── e2e/                     # End-to-end tests (Playwright)
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.ts           # Vite configuration with proxy
│   ├── Dockerfile               # Frontend container image (multi-stage)
│   └── nginx.conf.template      # Nginx configuration for production
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── docker-compose.yml           # Docker Compose orchestration
├── start.sh                     # Startup script (all platforms)
├── start.bat                    # Windows wrapper for start.sh
├── stop.sh                      # Shutdown script (all platforms)
├── stop.bat                     # Windows wrapper for stop.sh
└── README.md                    # This file
```

## Development Guide

### Backend Development

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows (Git Bash):
source .venv/Scripts/activate

# Install dependencies
pip install .

# Install development dependencies
pip install pytest ruff mypy httpx

# Run migrations
alembic upgrade head

# Seed database
python app/seed.py

# Start development server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Running Tests

#### Backend Tests

```bash
cd backend
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_transaction_service.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

#### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run unit tests in watch mode
npm run test:watch

# Run E2E tests
npx playwright test

# Run specific E2E test
npx playwright test e2e/wireframe_01_j01_s01_s02.spec.ts
```

### Code Quality

#### Backend Linting and Type Checking

```bash
cd backend
source .venv/bin/activate

# Run ruff linter
ruff check app/

# Run ruff with auto-fix
ruff check app/ --fix

# Run mypy type checker
mypy app/ --ignore-missing-imports
```

#### Frontend Linting and Type Checking

```bash
cd frontend

# Run ESLint
npm run lint

# Run TypeScript compiler (type check only)
npx tsc --noEmit
```

## Environment Configuration

### Backend Environment Variables

The backend uses `backend/dev.env` for local development. This file contains safe defaults and is copied to `backend/.env` automatically by `start.sh`.

**Configuration options:**

```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**For production or custom environments:**

- `DATABASE_URL`: Database connection string
  - Local: `sqlite:///./app.db`
  - PostgreSQL: `postgresql://user:password@localhost:5432/aml_db`
- `SECRET_KEY`: JWT signing key (minimum 32 characters)
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRY_MINUTES`: JWT token expiration (default: 60 minutes)
- `CORS_ORIGINS`: Comma-separated list of allowed frontend origins

### Frontend Configuration

The frontend uses Vite's default configuration with a proxy to the backend. **No `.env` file is required for local development.**

The Vite proxy is configured in `frontend/vite.config.ts` and automatically forwards `/api` requests to the backend using the `BACKEND_PORT` environment variable.

## Database Migrations

### Create a New Migration

```bash
cd backend
source .venv/bin/activate
alembic revision -m "description of change"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback One Migration

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

### Check Current Version

```bash
alembic current
```

## Continuous Integration

The project uses GitHub Actions for CI/CD. The workflow runs on every push and pull request to `main` and `develop` branches.

**CI Pipeline includes:**

- **Backend**:
  - Dependency installation
  - Database migrations (PostgreSQL test database)
  - Ruff linting
  - Type checking with mypy
  - Unit and integration tests with pytest

- **Frontend**:
  - Dependency installation
  - ESLint linting
  - TypeScript type checking
  - Production build
  - Unit tests

See `.github/workflows/ci.yml` for complete configuration.

## Troubleshooting

### Port Already in Use

If the default ports (9000 for backend, 5173 for frontend) are already in use, the startup script will automatically find and use the next available port. The actual ports will be displayed in the startup output.

### Database Migration Errors

If you encounter migration errors:

```bash
cd backend
source .venv/bin/activate

# Check current migration version
alembic current

# View migration history
alembic history

# Force to latest (careful: may lose data)
alembic upgrade head
```

### Frontend Build Errors

If the frontend fails to build:

```bash
cd frontend

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf dist node_modules/.vite

# Rebuild
npm run build
```

### Docker Issues

If Docker containers fail to start:

```bash
# View logs
docker compose logs backend
docker compose logs frontend

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Authentication Issues

If you cannot log in:

1. Verify you're using the correct credentials from the "Default Credentials" section
2. Check that the database was seeded properly: `python backend/app/seed.py`
3. Verify the backend is running and accessible
4. Check browser console for errors

### Windows-Specific Issues

**Git Bash Not Found:**
Install Git for Windows from https://git-scm.com/download/win

**Python Not Found:**
Ensure Python 3.11+ is installed and added to PATH. You can verify with:
```bash
python --version
```

**Virtual Environment Activation:**
Use `source .venv/Scripts/activate` instead of `source .venv/bin/activate` on Windows.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `pytest` (backend) and `npm test` (frontend)
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Create a Pull Request

## License

This is a demonstration project for educational purposes.

## Support

For issues and questions, please open an issue on the project repository.
