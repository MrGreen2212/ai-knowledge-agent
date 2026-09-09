import apiClient from "./client";

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
  top_k?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
}

export async function sendMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    "/conversations/chat",
    request
  );

  return response.data;
}