from fastapi import APIRouter, HTTPException
from app.models import ModelSettings
from app.services.ai_client import get_client

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/test")
async def test_connection(settings: ModelSettings):
    """Called when the user hits 'Save' in the Settings modal, so they get
    immediate feedback instead of only finding out at generation time.
    The actual settings values stay client-side (localStorage) per the
    'no auth yet' design — this endpoint just verifies they work."""
    client, model = get_client(settings)
    try:
        client.chat.completions.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not reach model: {e}")
    return {"status": "connected", "model": model}
