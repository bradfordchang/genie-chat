"""Genie API polling + SSE event generator."""

import asyncio
import json
import time
from typing import AsyncGenerator, Optional

from databricks.sdk import WorkspaceClient

STATUS_LABELS = {
    "SUBMITTED": "Submitting...",
    "FETCHING_METADATA": "Reading table schemas...",
    "FILTERING_CONTEXT": "Analyzing context...",
    "ASKING_AI": "Generating SQL query...",
    "PENDING_WAREHOUSE": "Starting warehouse...",
    "EXECUTING_QUERY": "Running query...",
    "COMPLETED": "Done",
    "FAILED": "Failed",
    "CANCELLED": "Cancelled",
}

MAX_RESULT_ROWS = 100
POLL_INTERVAL = 1.5
MAX_POLL_TIME = 300  # 5 minutes


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def stream_genie_response(
    client: WorkspaceClient,
    space_id: str,
    question: str,
    conversation_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Poll Genie API and yield SSE events as intermediary responses arrive."""

    try:
        # 1. Start conversation or send follow-up
        if conversation_id:
            wait = await asyncio.to_thread(
                client.genie.create_message,
                space_id=space_id,
                conversation_id=conversation_id,
                content=question,
            )
        else:
            wait = await asyncio.to_thread(
                client.genie.start_conversation,
                space_id=space_id,
                content=question,
            )

        # Extract IDs — start_conversation returns GenieStartConversationResponse,
        # create_message returns GenieMessage (different attribute names)
        resp = wait.response
        conv_id = resp.conversation_id
        msg_id = getattr(resp, 'message_id', None) or getattr(resp, 'id', None)

        yield _sse_event({
            "type": "conversation_started",
            "conversation_id": conv_id,
            "message_id": msg_id,
        })

        # 2. Poll loop
        last_status = None
        query_yielded = False
        result_yielded = False
        text_yielded = False
        start_time = time.time()

        while time.time() - start_time < MAX_POLL_TIME:
            message = await asyncio.to_thread(
                client.genie.get_message,
                space_id=space_id,
                conversation_id=conv_id,
                message_id=msg_id,
            )

            # Status update
            status_str = message.status.value if message.status else "UNKNOWN"
            if status_str != last_status:
                last_status = status_str
                yield _sse_event({
                    "type": "status",
                    "status": status_str,
                    "label": STATUS_LABELS.get(status_str, status_str),
                })

            # Process attachments
            if message.attachments:
                for attachment in message.attachments:
                    # Query attachment — SQL
                    if attachment.query and not query_yielded:
                        sql = attachment.query.query or ""
                        desc = attachment.query.description or ""
                        if sql:
                            query_yielded = True
                            yield _sse_event({
                                "type": "query",
                                "sql": sql,
                                "description": desc,
                            })

                    # Query result data
                    att_id = getattr(attachment, 'attachment_id', None) or getattr(attachment, 'id', None)
                    if attachment.query and att_id and not result_yielded:
                        try:
                            data_result = await asyncio.to_thread(
                                client.genie.get_message_query_result_by_attachment,
                                space_id=space_id,
                                conversation_id=conv_id,
                                message_id=msg_id,
                                attachment_id=att_id,
                            )
                            if data_result.statement_response:
                                sr = data_result.statement_response
                                columns = []
                                rows = []
                                total_rows = 0

                                if sr.manifest and sr.manifest.schema and sr.manifest.schema.columns:
                                    columns = [c.name for c in sr.manifest.schema.columns]

                                if sr.result and sr.result.data_array:
                                    total_rows = len(sr.result.data_array)
                                    rows = sr.result.data_array[:MAX_RESULT_ROWS]

                                if columns:
                                    result_yielded = True
                                    yield _sse_event({
                                        "type": "query_result",
                                        "columns": columns,
                                        "rows": rows,
                                        "row_count": total_rows,
                                    })
                        except Exception:
                            pass

                    # Text attachment
                    if attachment.text and attachment.text.content and not text_yielded:
                        text_yielded = True
                        yield _sse_event({
                            "type": "text",
                            "content": attachment.text.content,
                        })

                    # Suggested questions
                    if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                        questions_list = []
                        if hasattr(attachment.suggested_questions, 'questions'):
                            questions_list = [q for q in attachment.suggested_questions.questions if q]
                        if questions_list:
                            yield _sse_event({
                                "type": "suggestions",
                                "questions": questions_list,
                            })

            # Terminal states
            if status_str in ("COMPLETED", "FAILED", "CANCELLED"):
                if status_str == "FAILED":
                    error_msg = message.error if hasattr(message, 'error') and message.error else "Query failed"
                    yield _sse_event({"type": "error", "message": str(error_msg)})
                yield _sse_event({"type": "done"})
                return

            await asyncio.sleep(POLL_INTERVAL)

        # Timeout
        yield _sse_event({"type": "error", "message": "Request timed out after 5 minutes"})
        yield _sse_event({"type": "done"})

    except Exception as e:
        yield _sse_event({"type": "error", "message": str(e)})
        yield _sse_event({"type": "done"})
