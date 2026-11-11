"""Ingest worker — turns an uploaded resume file into anonymized text (docs/ARCHITECTURE.md, 6.3).

Skeleton: waits for jobs on the Redis queue and logs them. Steps to implement:
text layer / OCR -> language -> person_key -> anonymization -> chunks -> Postgres -> publish resume.ready.
"""
import json
import logging
import os
import signal
import time

import redis

QUEUE = "ingest"
BLOCK_SECONDS = 5                    # how long one BLPOP waits for a job
SOCKET_TIMEOUT = BLOCK_SECONDS + 10  # must be longer than BLPOP, or the client times out first
log = logging.getLogger("ingest")
running = True


def _stop(*_):
    global running
    running = False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, _stop)
    queue = redis.Redis.from_url(os.environ["REDIS_URL"], socket_timeout=SOCKET_TIMEOUT)
    log.info("waiting for jobs on '%s'", QUEUE)
    while running:
        try:
            item = queue.blpop([QUEUE], timeout=BLOCK_SECONDS)
        except (redis.ConnectionError, redis.TimeoutError) as exc:
            log.warning("redis unavailable (%s), retrying in 2 s", type(exc).__name__)
            time.sleep(2)
            continue
        if item is None:
            continue
        job = json.loads(item[1])
        log.info("got job for resume %s (processing not implemented yet)", job.get("resume_id"))
    log.info("stopped")


if __name__ == "__main__":
    main()
