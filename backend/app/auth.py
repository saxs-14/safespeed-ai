"""
Shared-secret API key auth, protecting every endpoint except /api/health.

This is a single-tenant "licensed instance" model - one API key per
deployment, set via the API_KEY env var - appropriate for an on-prem or
single-customer product rather than a multi-user SaaS. See README "Security
considerations" for the multi-tenant/per-user upgrade path.
"""
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings


async def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")
