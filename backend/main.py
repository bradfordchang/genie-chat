"""FastAPI app: SSE endpoint, static serving, health check."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.agent_client import stream_supervisor_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")
SUPERVISOR_APP = os.environ.get("SUPERVISOR_APP", "bc-agent-openai-multi")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


def _get_credentials(request: Request) -> tuple[str, str]:
    """Extract token and host from the request / environment."""
    token = request.headers.get("x-forwarded-access-token", "")
    host = os.environ.get("DATABRICKS_HOST", "")

    if host and not host.startswith("http"):
        host = f"https://{host}"

    if not token:
        # Local dev fallback: use Databricks CLI / env token
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        config = w.config
        token = config.token
        host = host or config.host

    return token, host


@app.get("/api/health")
async def health(request: Request):
    has_token = bool(request.headers.get("x-forwarded-access-token"))
    db_host = os.environ.get("DATABRICKS_HOST", "")
    return {
        "status": "ok",
        "supervisor_app": SUPERVISOR_APP,
        "space_id": GENIE_SPACE_ID,
        "has_user_token": has_token,
        "databricks_host": db_host,
    }


@app.get("/api/ask")
async def ask(request: Request, question: str, space_id: str = "", conversation_id: str = ""):
    token, host = _get_credentials(request)
    if not token:
        return JSONResponse({"error": "No authentication token available"}, status_code=401)

    model = f"apps/{SUPERVISOR_APP}"

    return StreamingResponse(
        stream_supervisor_response(question, token, host, model=model),
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
