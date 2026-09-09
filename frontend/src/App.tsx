import { useState } from "react";
import ChatWindow from "./components/Chat/ChatWindow";
import DocumentUpload from "./components/Documents/DocumentUpload";
import DocumentsList from "./components/Documents/DocumentsList";

function App() {
  const [documentsRefreshKey, setDocumentsRefreshKey] = useState(0);

  return (
    <div>
      <ChatWindow />
      <section>
        <DocumentUpload
          onUploaded={() => setDocumentsRefreshKey((key) => key + 1)}
        />
        <DocumentsList refreshKey={documentsRefreshKey} />
      </section>
    </div>
  );
}

export default App;