import { useRef, useState } from "react";
import { uploadDocument } from "../../api/documents";

interface DocumentUploadProps {
  onUploaded: () => void;
}

function DocumentUpload({ onUploaded }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file || loading) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await uploadDocument(file);
      onUploaded();
      setMessage("Документ успешно загружен");
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      console.error(err);
      setMessage("Не удалось загрузить документ");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        disabled={loading}
      />

      <button
        type="button"
        onClick={() => void handleUpload()}
        disabled={!file || loading}
      >
        {loading ? "Загрузка..." : "Загрузить"}
      </button>

      {message && <p role="status">{message}</p>}
    </div>
  );
}

export default DocumentUpload;
