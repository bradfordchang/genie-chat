export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming: boolean;
  status?: string;
  statusLabel?: string;
  sql?: string;
  sqlDescription?: string;
  columns?: string[];
  rows?: string[][];
  rowCount?: number;
  suggestions?: string[];
  error?: string;
  conversationId?: string;
}

export type SSEEvent =
  | { type: "conversation_started"; conversation_id: string; message_id: string }
  | { type: "status"; status: string; label: string }
  | { type: "query"; sql: string; description: string }
  | { type: "query_result"; columns: string[]; rows: string[][]; row_count: number }
  | { type: "text"; content: string }
  | { type: "suggestions"; questions: string[] }
  | { type: "error"; message: string }
  | { type: "done" };
