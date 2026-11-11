"""Search service — multi-stage ranking pipeline (docs/ARCHITECTURE.md, 6.4).

Skeleton: only /health. Stages to add: query understanding -> keyword retrieval ->
(later) vector retrieval -> ranking -> post-ranking. The active ranker comes from
configs/serving.json, so swapping rankers never touches the rest of the system.
"""
import json
import os

from fastapi import FastAPI

VERSION = "0.1.0"
app = FastAPI(title="HR Platform Search", version=VERSION)


def load_serving_config() -> dict:
    path = os.environ.get("SERVING_CONFIG", "/app/configs/serving.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SERVING = load_serving_config()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "ranker": SERVING["ranker"],
        "index_version": SERVING.get("index_version"),
    }
