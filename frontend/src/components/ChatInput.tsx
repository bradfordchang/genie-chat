import { useState, type KeyboardEvent } from "react";

interface Props {
  onSend: (question: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  const submit = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim());
      setValue("");
    }
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-input">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKey}
        placeholder={disabled ? "Waiting for response..." : "Ask a question about your data..."}
        disabled={disabled}
      />
      <button onClick={submit} disabled={disabled || !value.trim()}>
        Send
      </button>
    </div>
  );
}
