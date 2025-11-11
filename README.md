


# Wellora Smart Nutrition & Insights API

## Project Overview
A production-grade multi-user Smart Nutrition API for logging meals, tracking analytics, and receiving personalized nutrition recommendations. Built with FastAPI, async SQLAlchemy, JWT authentication, Redis caching, and RBAC.

## Architecture
- **FastAPI** for async API and automatic docs.
- **Async SQLAlchemy 2.0** for non-blocking DB queries.
- **Redis** for caching and rate limiting.
- **Clean Architecture**: `api`, `core`, `models`, `schemas`, `services`, `db`, `tasks`, `utils`.

### ERD
```mermaid
erDiagram
    USERS ||--o{ MEALS : logs
    FOODS ||--o{ MEALS : consumed_in
````

## Setup

```bash
git clone https://github.com/<username>/wellora-python-assessment-advanced.git
cd wellora-python-assessment-advanced
cp .env.example .env
# configure DATABASE_URL, JWT_SECRET_KEY, etc.
make up
docker-compose exec api sh
alembic upgrade head
```

* API: `http://localhost:8000`
* Swagger UI: `/docs`
* ReDoc: `/redoc`

## Authentication

* `POST /auth/register` – create user
* `POST /auth/login` – get JWT tokens
* `POST /auth/refresh` – refresh access token
* `POST /auth/logout` – client-side logout

## API Endpoints (Highlights)

* **Users**: `/users/profile` (GET, PATCH), `/users/` (Admin)
* **Foods**: `/foods/` (CRUD, Admin for create/update/delete)
* **Meals**: `/meals/` (log, list, update, delete)
* **Analytics**: `/analytics/daily`, `/analytics/weekly`, `/analytics/reco` (cached 5 min)

## Testing

```bash
PYTHONPATH=. pytest --cov=app --cov-report=html --cov-report=term-missing
```

## Decisions & Future Work

* **Async + caching** improves performance and reduces DB load.
* **Rate limiting** per user via Redis sliding window.
* **Future:** Full scheduler integration, advanced security, multi-tenancy, and enhanced observability.


