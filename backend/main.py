"""FastAPI app: SSE endpoint, static serving, health check."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from databricks.sdk import WorkspaceClient

from backend.genie_client import stream_genie_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


def _get_client(request: Request) -> WorkspaceClient:
    """Create a WorkspaceClient using the user's forwarded token or local auth."""
    token = request.headers.get("x-forwarded-access-token")
    host = os.environ.get("DATABRICKS_HOST", "")

    if token:
        if host and not host.startswith("http"):
            host = f"https://{host}"
        logger.info("Using user forwarded token, host=%s", host)
        return WorkspaceClient(host=host, token=token)

    # Local dev fallback
    logger.info("No forwarded token, using default WorkspaceClient auth")
    return WorkspaceClient()


@app.get("/api/health")
async def health(request: Request):
    has_token = bool(request.headers.get("x-forwarded-access-token"))
    db_host = os.environ.get("DATABRICKS_HOST", "")
    return {
        "status": "ok",
        "space_id": GENIE_SPACE_ID,
        "has_user_token": has_token,
        "databricks_host": db_host,
    }


@app.get("/api/ask")
async def ask(request: Request, question: str, space_id: str = "", conversation_id: str = ""):
    sid = space_id or GENIE_SPACE_ID
    if not sid:
        return JSONResponse({"error": "No space_id provided"}, status_code=400)

    client = _get_client(request)
    conv_id = conversation_id if conversation_id else None

    return StreamingResponse(
        stream_genie_response(client, sid, question, conv_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Mount frontend static files (must be last)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
