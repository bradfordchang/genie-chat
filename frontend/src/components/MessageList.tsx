import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  onSuggestionClick: (question: string) => void;
}

export function MessageList({ messages, onSuggestionClick }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="empty-state">
          <p>Ask a question to get started</p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onSuggestionClick={onSuggestionClick} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
