import type { Message } from "../../types/chat";

interface MessageListProps {
  messages: Message[];
}

function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return <div>Начните новый диалог</div>;
  }

  return (
    <div>
      {messages.map((message) => (
        <div key={message.id}>
          <strong>
            {message.role === "user" ? "Вы" : "AI"}
          </strong>

          <p>{message.content}</p>
        </div>
      ))}
    </div>
  );
}

export default MessageList;