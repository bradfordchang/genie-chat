import { useState, useCallback, useRef } from "react";
import type { ChatMessage, SSEEvent } from "../types";

let nextId = 0;

export function useGenieChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const conversationIdRef = useRef<string | null>(null);

  const ask = useCallback(
    async (question: string) => {
      if (!question.trim() || isStreaming) return;

      const userMsg: ChatMessage = {
        id: `msg-${nextId++}`,
        role: "user",
        content: question,
        isStreaming: false,
      };

      const assistantId = `msg-${nextId++}`;
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
        statusLabel: "Submitting...",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const params = new URLSearchParams({ question });
      if (conversationIdRef.current) {
        params.set("conversation_id", conversationIdRef.current);
      }

      try {
        const response = await fetch(`/api/ask?${params}`);
        if (!response.ok || !response.body) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            let event: SSEEvent;
            try {
              event = JSON.parse(jsonStr);
            } catch {
              continue;
            }

            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                return applyEvent(m, event, conversationIdRef);
              })
            );

            if (event.type === "done" || event.type === "error") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, isStreaming: false } : m
                )
              );
              setIsStreaming(false);
            }
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, isStreaming: false, error: String(err) }
              : m
          )
        );
        setIsStreaming(false);
      }
    },
    [isStreaming]
  );

  return { messages, isStreaming, ask };
}

function applyEvent(
  msg: ChatMessage,
  event: SSEEvent,
  convRef: React.MutableRefObject<string | null>
): ChatMessage {
  switch (event.type) {
    case "conversation_started":
      convRef.current = event.conversation_id;
      return { ...msg, conversationId: event.conversation_id };
    case "status":
      return { ...msg, status: event.status, statusLabel: event.label };
    case "query":
      return { ...msg, sql: event.sql, sqlDescription: event.description };
    case "query_result":
      return {
        ...msg,
        columns: event.columns,
        rows: event.rows,
        rowCount: event.row_count,
      };
    case "text":
      return { ...msg, content: event.content };
    case "suggestions":
      return { ...msg, suggestions: event.questions };
    case "error":
      return { ...msg, error: event.message };
    case "done":
      return msg;
    default:
      return msg;
  }
}
