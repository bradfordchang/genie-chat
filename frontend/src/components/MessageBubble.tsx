import Markdown from "react-markdown";
import type { ChatMessage } from "../types";
import { StatusIndicator } from "./StatusIndicator";
import { SqlBlock } from "./SqlBlock";
import { ResultTable } from "./ResultTable";
import { SuggestedQuestions } from "./SuggestedQuestions";

interface Props {
  message: ChatMessage;
  onSuggestionClick: (question: string) => void;
}

export function MessageBubble({ message, onSuggestionClick }: Props) {
  if (message.role === "user") {
    return (
      <div className="message user">
        <div className="bubble user-bubble">{message.content}</div>
      </div>
    );
  }

  return (
    <div className="message assistant">
      <div className="bubble assistant-bubble">
        {message.isStreaming && message.statusLabel && (
          <StatusIndicator label={message.statusLabel} />
        )}
        {message.sql && <SqlBlock sql={message.sql} description={message.sqlDescription} />}
        {message.columns && message.rows && (
          <ResultTable columns={message.columns} rows={message.rows} rowCount={message.rowCount} />
        )}
        {message.content && <div className="text-content"><Markdown>{message.content}</Markdown></div>}
        {message.error && <div className="error-content">{message.error}</div>}
        {message.suggestions && !message.isStreaming && (
          <SuggestedQuestions questions={message.suggestions} onClick={onSuggestionClick} />
        )}
      </div>
    </div>
  );
}
