import { useGenieChat } from "./hooks/useGenieChat";
import { MessageList } from "./components/MessageList";
import { ChatInput } from "./components/ChatInput";

export default function App() {
  const { messages, isStreaming, ask } = useGenieChat();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Genie Chat</h1>
        <span className="subtitle">Ask questions about your data</span>
      </header>
      <MessageList messages={messages} onSuggestionClick={ask} />
      <ChatInput onSend={ask} disabled={isStreaming} />
    </div>
  );
}
