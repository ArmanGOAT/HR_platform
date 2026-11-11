# HR Platform

A platform for matching IT candidates to job descriptions. Candidates upload their resumes;
HR pastes a job description and gets the top 50 relevant candidates with an explanation of what matched.

Course project, Artificial Intelligence [SOC4040], Inha University in Tashkent, Fall 2026.

| Document | What it covers |
|---|---|
| [docs/DESIGN_DOC.md](docs/DESIGN_DOC.md) | Problem space and solution space: problem, cost of errors, goals, metrics, plan |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Services, storage, flows, deployment |
| [docs/API.md](docs/API.md) | Contract between the web app and the gateway (draft) |

## Quick start

Requirements: Docker Desktop (running).

```bash
cp .env.example .env        # then set your own passwords in .env
docker compose up --build
```

Then open:

| What | Address |
|---|---|
| Web app (placeholder for now) | http://localhost:3000 |
| Gateway health | http://localhost:8000/api/health |
| MinIO console (development) | http://localhost:9001 |

All services are healthy when `/api/health` returns `"status": "ok"`.

Stop: `docker compose down`. Stop and delete all stored data: `docker compose down -v`.

## Services

| Service | Folder | Role |
|---|---|---|
| web | `services/web/` | Interface for candidates and HR; nginx forwards `/api` to the gateway |
| gateway | `services/gateway/` | Single API entry point |
| ingest | `services/ingest/` | Background worker: file → text (OCR) → language → anonymization → chunks |
| search | `services/search/` | Ranking pipeline, top 50 |
| postgres / minio / redis | `infra/` | Metadata / files / job queue |

Shared preprocessing code lives in `packages/hr_core/` and is used by ingest, search and the offline scripts.

## Repository layout

```
configs/serving.json   which ranker and index the demo uses
docs/                  design doc, architecture, API contract
infra/                 Postgres schema, MinIO bucket setup
packages/hr_core/      shared preprocessing library
services/              gateway, ingest, search, web
offline/               bootstrap import, training, evaluation, index build
notebooks/             data exploration and analysis
reports/               experiment folders (config.json, metrics.json) and leaderboard.csv
```

## Rules for the team

- Never commit `.env`, `*.session`, `resumes_pdfs/` or `data/` — they hold secrets and personal data (`.gitignore` covers them).
- Notebooks must not show personal data in their outputs.
- Every experiment gets a folder in `reports/experiments/`; no folder means the experiment did not happen.

## Reused components

Disclosed as required by the course: Tesseract OCR (planned), PostgreSQL, MinIO, Redis, nginx, FastAPI.
The web app is built with the help of an AI assistant (Claude).
