/**
 * useChatMessage Hook
 * Custom hook for sending chat messages to the API
 */

import { useCallback } from 'react';
import { useApi } from './useApi';
import { useConversation } from '../contexts/ConversationContext';

export interface ChatMessageRequest {
  message: string;
  session_id: string;
  user_name?: string;
  language?: string;
}

export interface ChatMessageResponse {
  response: string;
  language: string;
  conversation_id: string;
  facts_extracted?: number;
  context_used?: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function sendChatMessageApi(request: ChatMessageRequest): Promise<ChatMessageResponse> {
  const response = await fetch(`${API_URL}/api/chat/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to send message' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export function useChatMessage() {
  const { addMessage } = useConversation();
  const apiHook = useApi<ChatMessageResponse, [ChatMessageRequest]>(sendChatMessageApi, {
    onSuccess: (data) => {
      // Add assistant's response to conversation
      addMessage({
        conversationId: data.conversation_id,
        role: 'assistant',
        content: data.response,
        language: data.language,
        messageType: 'text',
        metadata: {
          interface: 'web',
        },
      });
    },
  });

  const sendMessage = useCallback(
    async (message: string, sessionId: string, userName?: string, language?: string) => {
      if (!message.trim()) {
        throw new Error('Message cannot be empty');
      }

      // Add user's message to conversation
      addMessage({
        conversationId: 'pending',
        role: 'user',
        content: message,
        language: language,
        messageType: 'text',
        metadata: {
          interface: 'web',
        },
      });

      return apiHook.execute({
        message: message.trim(),
        session_id: sessionId,
        user_name: userName,
        language: language,
      });
    },
    [apiHook.execute, addMessage]
  );

  return {
    ...apiHook,
    sendMessage,
  };
}
