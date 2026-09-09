import { useEffect, useState } from "react";
import { getDocuments } from "../../api/documents";
import type { Document } from "../../api/documents";

interface DocumentsListProps {
  refreshKey: number;
}

function DocumentsList({ refreshKey }: DocumentsListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDocuments = async () => {
      setLoading(true);
      setError("");

      try {
        const items = await getDocuments();
        setDocuments(items);
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить список документов");
      } finally {
        setLoading(false);
      }
    };

    void loadDocuments();
  }, [refreshKey]);

  return (
    <section>
      <h2>Документы</h2>

      {loading && <p>Загрузка документов...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && documents.length === 0 && !error && (
        <p>Документов пока нет</p>
      )}

      {!loading && documents.length > 0 && (
        <ul>
          {documents.map((document) => (
            <li key={document.id}>
              <p>{document.filename}</p>
              <p>Статус: {document.status}</p>
              <p>Размер: {document.size ?? "Не указан"}</p>
              <p>
                Дата создания: {document.created_at
                  ? new Date(document.created_at).toLocaleString("ru-RU")
                  : "Не указана"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default DocumentsList;
