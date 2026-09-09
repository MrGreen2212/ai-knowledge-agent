import apiClient from "./client";
import type { Conversation, Message } from "../types/chat";

export interface ConversationDetails extends Conversation {
  messages: Message[];
}

export async function getConversations(): Promise<Conversation[]> {
  const response = await apiClient.get<Conversation[]>("/conversations");

  return response.data;
}

export async function getConversation(
  conversationId: string
): Promise<ConversationDetails> {
  const response = await apiClient.get<ConversationDetails>(
    `/conversations/${conversationId}`
  );

  return response.data;
}

export async function deleteConversation(
  conversationId: string
): Promise<void> {
  await apiClient.delete(`/conversations/${conversationId}`);
}