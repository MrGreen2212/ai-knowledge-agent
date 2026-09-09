import { useEffect, useState, type MouseEvent } from "react";
import {
  deleteConversation,
  getConversations,
} from "../../api/conversations";
import type { Conversation } from "../../types/chat";

interface ConversationsListProps {
  selectedConversationId?: string | null;
  onSelectConversation?: (conversationId: string | null) => void;
}

function ConversationsList({
  selectedConversationId = null,
  onSelectConversation,
}: ConversationsListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadConversations = async () => {
    setLoading(true);
    setError("");

    try {
      const items = await getConversations();
      setConversations(items);
    } catch (err) {
      console.error(err);
      setError("Не удалось загрузить список диалогов");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadConversations();
  }, []);

  const handleNewConversation = () => {
    onSelectConversation?.(null);
  };

  const handleSelectConversation = (conversationId: string) => {
    onSelectConversation?.(conversationId);
  };

  const handleDeleteConversation = async (
    event: MouseEvent<HTMLButtonElement>,
    conversationId: string
  ) => {
    event.stopPropagation();

    if (deletingId) {
      return;
    }

    setDeletingId(conversationId);

    try {
      await deleteConversation(conversationId);

      setConversations((current) =>
        current.filter((conversation) => conversation.id !== conversationId)
      );

      if (selectedConversationId === conversationId) {
        onSelectConversation?.(null);
      }
    } catch (err) {
      console.error(err);
      setError("Не удалось удалить диалог");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside>
      <button type="button" onClick={handleNewConversation}>
        + Новый диалог
      </button>

      {loading && <p>Загрузка диалогов...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && conversations.length === 0 && !error && (
        <p>Диалогов пока нет</p>
      )}

      <ul>
        {conversations.map((conversation) => {
          const isSelected = conversation.id === selectedConversationId;

          return (
            <li key={conversation.id}>
              <button
                type="button"
                onClick={() => handleSelectConversation(conversation.id)}
                style={{
                  fontWeight: isSelected ? 700 : 400,
                  background: isSelected ? "#eaf2ff" : "transparent",
                }}
              >
                <span>{conversation.title ?? "Без названия"}</span>
                <small>
                  {new Date(conversation.updated_at).toLocaleString("ru-RU")}
                </small>
              </button>

              <button
                type="button"
                onClick={(event) =>
                  void handleDeleteConversation(event, conversation.id)
                }
                disabled={deletingId === conversation.id}
              >
                {deletingId === conversation.id ? "Удаление..." : "Удалить"}
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

export default ConversationsList;
