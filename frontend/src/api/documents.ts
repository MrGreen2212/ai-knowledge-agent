import apiClient from "./client";

export interface Document {
  id: string;
  filename: string;
  object_name: string;
  content_type: string | null;
  size: number | null;
  status: string;
  created_at: string | null;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  object_name: string;
  status: string;
  size: number | null;
}

export async function uploadDocument(
  file: File
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<DocumentUploadResponse>(
    "/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

export async function getDocuments(): Promise<Document[]> {
  const response = await apiClient.get<Document[]>("/documents");

  return response.data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/documents/${documentId}`);

  return response.data;
}
