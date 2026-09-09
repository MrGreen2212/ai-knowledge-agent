import { useState } from "react";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

function MessageInput({
  onSend,
  disabled = false,
}: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div>
      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Введите вопрос..."
        rows={3}
        disabled={disabled}
      />

      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !message.trim()}
      >
        {disabled ? "Отправка..." : "Отправить"}
      </button>
    </div>
  );
}

export default MessageInput;