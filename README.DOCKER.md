This project includes a Dockerfile and docker-compose.yml for local and small-production testing.

Recommended sizing for 25-50 active users
- Gunicorn workers: 4
- Threads per worker: 4
  - Total concurrency ~= workers * threads = 16 concurrent requests. For 25-50 active users this is a reasonable starting point; increase workers or threads if the DB and CPU allow.
- DB pool (per-process):
  - DB_POOL_SIZE=10
  - DB_MAX_OVERFLOW=20
  - DB_POOL_TIMEOUT=60
  - Note: total DB connections ~ workers * (DB_POOL_SIZE + DB_MAX_OVERFLOW) — ensure your Postgres server can handle this.

How to run locally with Docker Compose
1. Build and start services:

```powershell
docker compose up --build
```

2. Open http://localhost:8000

Adjust environment variables in `docker-compose.yml` for production values and secrets.
