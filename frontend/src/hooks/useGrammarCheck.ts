/**
 * useGrammarCheck Hook
 * Custom hook for grammar checking API calls
 */

import { useCallback } from 'react';
import { useApi } from './useApi';

export interface GrammarError {
  start_pos: number;
  end_pos: number;
  error_type: string;
  original_text: string;
  corrected_text: string;
  explanation: string;
  severity: string;
}

export interface GrammarCheckResponse {
  original_text: string;
  corrected_text: string;
  errors: GrammarError[];
  overall_score: number;
  has_errors: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function checkGrammarApi(text: string): Promise<GrammarCheckResponse> {
  const response = await fetch(`${API_URL}/api/grammar/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: text.trim() }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Grammar check failed' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export function useGrammarCheck() {
  const apiHook = useApi<GrammarCheckResponse, [string]>(checkGrammarApi);

  const checkGrammar = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        throw new Error('Text cannot be empty');
      }
      return apiHook.execute(text);
    },
    [apiHook.execute]
  );

  return {
    ...apiHook,
    checkGrammar,
  };
}
