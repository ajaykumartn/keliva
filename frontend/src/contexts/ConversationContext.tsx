/**
 * ConversationContext
 * Manages conversation state and message history across the application
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  language?: string;
  messageType: 'text' | 'voice' | 'grammar_check';
  timestamp: string;
  metadata?: {
    interface?: 'web' | 'telegram' | 'whatsapp';
    confidence?: number;
    grammarErrors?: any[];
  };
}

export interface Conversation {
  id: string;
  userId: string;
  startedAt: string;
  endedAt?: string;
  interface: 'web' | 'telegram' | 'whatsapp';
  messages: Message[];
}

interface ConversationContextType {
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  startConversation: (userId: string, interfaceType: 'web' | 'telegram' | 'whatsapp') => void;
  endConversation: () => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  loadConversationHistory: (userId: string) => Promise<void>;
  setError: (error: string | null) => void;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

interface ConversationProviderProps {
  children: ReactNode;
}

export function ConversationProvider({ children }: ConversationProviderProps) {
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startConversation = useCallback((userId: string, interfaceType: 'web' | 'telegram' | 'whatsapp') => {
    const conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const newConversation: Conversation = {
      id: conversationId,
      userId,
      startedAt: new Date().toISOString(),
      interface: interfaceType,
      messages: [],
    };

    setCurrentConversation(newConversation);
    setMessages([]);
    setError(null);
  }, []);

  const endConversation = useCallback(() => {
    if (currentConversation) {
      setCurrentConversation({
        ...currentConversation,
        endedAt: new Date().toISOString(),
      });
    }
  }, [currentConversation]);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, newMessage]);

    // Update current conversation
    if (currentConversation) {
      setCurrentConversation(prev => {
        if (!prev) return null;
        return {
          ...prev,
          messages: [...prev.messages, newMessage],
        };
      });
    }
  }, [currentConversation]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    if (currentConversation) {
      setCurrentConversation({
        ...currentConversation,
        messages: [],
      });
    }
  }, [currentConversation]);

  const loadConversationHistory = useCallback(async (userId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${apiUrl}/api/chat/history?session_id=${userId}&include_all_interfaces=true`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          // User not found - this is okay for first-time users
          setMessages([]);
          return;
        }
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Transform API response to our Message format
      const loadedMessages: Message[] = data.messages.map((msg: any) => ({
        id: msg.id,
        conversationId: data.conversation_id || 'unknown',
        role: msg.role,
        content: msg.content,
        language: msg.language,
        messageType: msg.message_type,
        timestamp: msg.timestamp,
        metadata: msg.metadata,
      }));

      setMessages(loadedMessages);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversation history';
      setError(errorMessage);
      console.error('Error loading conversation history:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const value: ConversationContextType = {
    currentConversation,
    messages,
    isLoading,
    error,
    startConversation,
    endConversation,
    addMessage,
    clearMessages,
    loadConversationHistory,
    setError,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversation() {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return context;
}
