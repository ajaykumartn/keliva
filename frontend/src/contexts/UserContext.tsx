/**
 * UserContext
 * Manages user state and session information across the application
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  sessionId: string;
  name?: string;
  preferredLanguage?: string;
  createdAt?: string;
  lastActive?: string;
}

interface UserContextType {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  updateUser: (updates: Partial<User>) => void;
  clearUser: () => void;
  refreshUser: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Get or create a session ID for the current user
function getOrCreateSessionId(): string {
  let sessionId = localStorage.getItem('keliva_session_id');
  if (!sessionId) {
    sessionId = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('keliva_session_id', sessionId);
  }
  return sessionId;
}

interface UserProviderProps {
  children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize user on mount
  useEffect(() => {
    initializeUser();
  }, []);

  const initializeUser = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const sessionId = getOrCreateSessionId();
      
      // Create initial user object
      const initialUser: User = {
        id: sessionId,
        sessionId: sessionId,
        name: localStorage.getItem('keliva_user_name') || undefined,
        preferredLanguage: localStorage.getItem('keliva_preferred_language') || 'en-US',
        lastActive: new Date().toISOString(),
      };

      setUser(initialUser);
    } catch (err) {
      console.error('Error initializing user:', err);
      setError(err instanceof Error ? err.message : 'Failed to initialize user');
    } finally {
      setIsLoading(false);
    }
  };

  const updateUser = (updates: Partial<User>) => {
    setUser(prev => {
      if (!prev) return null;
      
      const updated = { ...prev, ...updates };
      
      // Persist certain fields to localStorage
      if (updates.name !== undefined) {
        localStorage.setItem('keliva_user_name', updates.name);
      }
      if (updates.preferredLanguage !== undefined) {
        localStorage.setItem('keliva_preferred_language', updates.preferredLanguage);
      }
      
      return updated;
    });
  };

  const clearUser = () => {
    localStorage.removeItem('keliva_session_id');
    localStorage.removeItem('keliva_user_name');
    localStorage.removeItem('keliva_preferred_language');
    setUser(null);
    initializeUser();
  };

  const refreshUser = async () => {
    await initializeUser();
  };

  const value: UserContextType = {
    user,
    isLoading,
    error,
    updateUser,
    clearUser,
    refreshUser,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
