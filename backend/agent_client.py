"""Multi-agent supervisor client: streams Responses API events as SSE."""

import json
import logging
from typing import AsyncGenerator

from databricks_openai import AsyncDatabricksOpenAI

logger = logging.getLogger(__name__)


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def stream_supervisor_response(
    question: str,
    token: str,
    host: str,
    model: str = "apps/bc-agent-openai-multi",
) -> AsyncGenerator[str, None]:
    """Call the multi-agent supervisor and translate streamed events to SSE."""

    base_url = f"{host}/serving-endpoints"
    client = AsyncDatabricksOpenAI(api_key=token, base_url=base_url)

    try:
        stream = client.responses.create(
            model=model,
            input=[{"role": "user", "content": question}],
            stream=True,
        )

        async for event in await stream:
            evt_type = event.type

            # Text deltas
            if evt_type == "response.output_text.delta":
                yield _sse_event({"type": "text_delta", "content": event.delta})

            # Full text output item done
            elif evt_type == "response.output_text.done":
                yield _sse_event({"type": "text", "content": event.text})

            # Tool / function call started
            elif evt_type == "response.output_item.added":
                item = event.item
                if getattr(item, "type", None) == "function_call":
                    name = getattr(item, "name", "tool")
                    yield _sse_event({"type": "status", "label": f"Using tool: {name}..."})

            # Stream finished
            elif evt_type == "response.completed":
                yield _sse_event({"type": "done"})
                return

        # If we exit the loop without response.completed
        yield _sse_event({"type": "done"})

    except Exception as e:
        logger.exception("Supervisor stream error")
        yield _sse_event({"type": "error", "message": str(e)})
        yield _sse_event({"type": "done"})
    finally:
        await client.close()
