"""Simple in-memory sliding-window rate limiter for compute-heavy endpoints.

Per-process only - fine for a single-instance deployment. A multi-instance
deployment behind a load balancer should move this to shared storage
(Redis) so limits apply across instances, not per-process.
"""
import time
from typing import Dict, List

from fastapi import HTTPException, Request

_hits: Dict[str, List[float]] = {}


def rate_limit(max_requests: int = 20, window_seconds: int = 60):
    async def _check(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        recent = [t for t in _hits.get(ip, []) if now - t < window_seconds]
        if len(recent) >= max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded - try again shortly")
        recent.append(now)
        _hits[ip] = recent

    return _check
