"""Gateway — the single entry point of the HR platform API (contract: docs/API.md).

Skeleton: only /api/health. Upload, resumes, search and feedback endpoints come next.
"""
import os

import boto3
import httpx
import psycopg
import redis
from botocore.config import Config
from fastapi import FastAPI

VERSION = "0.1.0"
app = FastAPI(title="HR Platform Gateway", version=VERSION)


def _check(probe) -> str:
    """Runs one dependency probe; health must never crash because a dependency is down."""
    try:
        probe()
        return "ok"
    except Exception as exc:
        return f"error: {type(exc).__name__}"


def _db() -> None:
    with psycopg.connect(os.environ["POSTGRES_DSN"], connect_timeout=2) as conn:
        conn.execute("SELECT 1")


def _storage() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}),
    )
    s3.head_bucket(Bucket="raw-pii")


def _queue() -> None:
    redis.Redis.from_url(os.environ["REDIS_URL"], socket_timeout=2).ping()


def _search() -> None:
    httpx.get(f"{os.environ['SEARCH_URL']}/health", timeout=2).raise_for_status()


@app.get("/api/health")
def health() -> dict:
    services = {
        "db": _check(_db),
        "storage": _check(_storage),
        "queue": _check(_queue),
        "search": _check(_search),
    }
    status = "ok" if all(v == "ok" for v in services.values()) else "degraded"
    return {"status": status, "version": VERSION, "services": services}
