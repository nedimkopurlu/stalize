from fastapi import Header, HTTPException
from app.core.config import settings


async def verify_api_key(x_api_key: str = Header(None)):
    """API key guard for mutation endpoints.

    Local development may run without an API key, but production must fail closed
    if the deployment forgot to configure one.
    """
    if settings.API_KEY is None:
        if settings.ENVIRONMENT.lower() in {"prod", "production"}:
            raise HTTPException(status_code=503, detail="API key is not configured")
        return
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
