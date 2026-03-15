# Halleyx Workflow Management System — Backend

A production-ready Django REST API backend for a workflow management system with rule-based execution engine, multi-tenant architecture, and full audit logging.

## Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Core language |
| Django | 4.2.7 | Web framework |
| Django REST Framework | 3.14.0 | API framework |
| PostgreSQL | 15 | Primary database |
| Redis | 7 | Caching + sessions |
| RabbitMQ | 3 | Message queue |
| Celery | 5.3.4 | Background tasks |
| Celery Beat | — | Scheduled tasks |
| SimpleJWT | 5.3.0 | JWT authentication |
| drf-yasg | 1.21.7 | Swagger docs |
| Docker + Compose | — | Containerization |
| GitHub Actions | — | CI/CD |

## Architecture Overview

```
halleyx-workflow-backend/
├── apps/
│   ├── authentication/    # Company + User models, JWT auth
│   ├── workflows/         # Workflow CRUD + versioning
│   ├── steps/             # Step CRUD + reorder
│   ├── rules/             # Rule CRUD + condition validator
│   ├── executions/        # Execution engine + approval flow
│   └── engine/            # Rule engine (safe parser) + executor
├── config/
│   ├── settings/          # base / development / production
│   ├── celery.py          # Celery app config
│   ├── middleware.py      # Company isolation middleware
│   └── urls.py            # Root URL config + Swagger
└── management/commands/   # create_sample_data command
```

## Quick Start

```bash
# 1. Clone
git clone <repo>
cd halleyx-workflow-backend

# 2. Configure
cp .env.example config/.env
# Edit config/.env as needed

# 3. Start all services
docker-compose up --build

# 4. Run migrations
docker-compose exec api python manage.py migrate

# 5. Create sample data
docker-compose exec api python manage.py create_sample_data
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000/api/ | — |
| Swagger UI | http://localhost:8000/swagger/ | — |
| ReDoc | http://localhost:8000/redoc/ | — |
| Django Admin | http://localhost:8000/admin/ | superuser |
| RabbitMQ UI | http://localhost:15672/ | guest/guest |

## Sample Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tcs.com | Admin123! |
| Manager | manager@tcs.com | Manager123! |
| Employee | employee@tcs.com | Employee123! |
| Director | director@tcs.com | Director123! |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register company + admin |
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/token/refresh/` | Refresh JWT |
| POST | `/api/auth/logout/` | Logout (blacklist token) |
| GET/PUT | `/api/auth/me/` | Get/update own profile |
| GET/POST | `/api/auth/users/` | List/create company users |

### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/workflows/` | List/create workflows |
| GET | `/api/workflows/{id}/` | Workflow detail (nested) |
| PUT | `/api/workflows/{id}/` | Update (creates new version!) |
| DELETE | `/api/workflows/{id}/` | Soft delete |
| GET | `/api/workflows/{id}/versions/` | Version history |
| POST | `/api/workflows/{id}/rollback/` | Rollback to version |

### Steps & Rules
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/workflows/{id}/steps/` | List/create steps |
| GET/PUT/DELETE | `/api/steps/{id}/` | Step detail |
| POST | `/api/steps/reorder/` | Bulk reorder |
| GET/POST | `/api/steps/{id}/rules/` | List/create rules |
| GET/PUT/DELETE | `/api/rules/{id}/` | Rule detail |
| POST | `/api/rules/validate/` | Validate condition |
| POST | `/api/steps/{id}/rules/reorder/` | Bulk reorder rules |

### Executions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflows/{id}/execute/` | Start execution |
| GET | `/api/executions/` | List executions |
| GET | `/api/executions/{id}/` | Execution detail |
| POST | `/api/executions/{id}/approve/` | Approve step |
| POST | `/api/executions/{id}/reject/` | Reject step |
| POST | `/api/executions/{id}/return/` | Return step |
| POST | `/api/executions/{id}/cancel/` | Cancel execution |
| POST | `/api/executions/{id}/retry/` | Retry failed step |
| GET | `/api/audit/` | Audit log + stats |

## Multi-Tenant Architecture

All data is automatically scoped to the authenticated user's company:
- JWT token carries user identity
- `CompanyMiddleware` injects `request.user_company` on every request
- All queries filtered by `company` — **zero cross-company data leakage**

## Workflow Versioning

- Editing a workflow **always** creates a new version
- Old versions are **locked forever** (is_active=False) — never deleted
- All steps and rules are copied to the new version
- Rollback creates a new version copying from any historical version

## Rule Engine

Custom safe parser — **never uses `eval()` or `exec()`**:

```
Comparison : == != > < >= <=
Logical    : && (AND)  || (OR)
String     : contains(field, "value")
             startsWith(field, "prefix")
             endsWith(field, "suffix")
Special    : DEFAULT → always matches (required fallback)
```

Examples:
```
amount > 100 && country == 'US'
priority == 'High' || amount > 500
contains(department, 'Finance')
DEFAULT
```

## Loop Prevention

Every execution tracks `iteration_count` vs `max_iterations` (default 10).  
When `iteration_count > max_iterations`:
- Status → `failed`
- Logs the error with the step name
- Stops immediately

## Execution Retry

`POST /api/executions/{id}/retry/` resumes from the **failed step only**,  
NOT from the beginning of the workflow.

## Running Tests

```bash
# With Docker
docker-compose exec api python manage.py test --verbosity=2

# Locally
python manage.py test --verbosity=2 --settings=config.settings.development
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DB_*` | PostgreSQL connection details |
| `REDIS_URL` | Redis connection URL |
| `RABBITMQ_URL` | RabbitMQ connection URL |
| `DJANGO_SETTINGS_MODULE` | Settings to use |
