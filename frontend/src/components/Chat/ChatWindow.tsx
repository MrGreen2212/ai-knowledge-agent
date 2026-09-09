import { useState } from "react";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { sendMessage } from "../../api/chat";
import { getConversation } from "../../api/conversations";
import ConversationsList from "./ConversationsList";
import type { Message } from "../../types/chat";

function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const resetCurrentChat = () => {
    setMessages([]);
    setConversationId(null);
    setError("");
  };

  const handleSelectConversation = async (selectedConversationId: string | null) => {
    if (!selectedConversationId) {
      resetCurrentChat();
      return;
    }

    setError("");
    setLoading(true);

    try {
      const conversation = await getConversation(selectedConversationId);
      setConversationId(selectedConversationId);
      setMessages(conversation.messages);
    } catch (err) {
      console.error(err);
      setError("Не удалось загрузить выбранный диалог");
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (question: string) => {
    setLoading(true);
    setError("");

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      created_at: new Date().toISOString(),
    };

    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendMessage({
        question,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        created_at: new Date().toISOString(),
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      console.error(err);
      setError("Не удалось получить ответ от сервера");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: "16px" }}>
      <ConversationsList
        selectedConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
      />

      <div style={{ flex: 1 }}>
        <h1>AI Knowledge Agent</h1>

        <MessageList messages={messages} />

        {error && <p>{error}</p>}

        <MessageInput
          onSend={handleSend}
          disabled={loading}
        />
      </div>
    </div>
  );
}

export default ChatWindow;