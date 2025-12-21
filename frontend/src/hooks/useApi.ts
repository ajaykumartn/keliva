/**
 * useApi Hook
 * Generic hook for making API calls with loading, error states, and retry logic
 */

import { useState, useCallback } from 'react';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  retries?: number;
  retryDelay?: number;
}

interface UseApiReturn<T, P extends any[]> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  execute: (...args: P) => Promise<T | null>;
  retry: () => Promise<T | null>;
  reset: () => void;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useApi<T, P extends any[] = []>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T, P> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastArgs, setLastArgs] = useState<P | null>(null);

  const { retries = 2, retryDelay = 1000 } = options;

  const executeWithRetry = useCallback(
    async (...args: P): Promise<T | null> => {
      let lastError: Error | null = null;
      
      for (let attempt = 0; attempt <= retries; attempt++) {
        try {
          setIsLoading(true);
          setError(null);

          const result = await apiFunction(...args);
          setData(result);

          if (options.onSuccess) {
            options.onSuccess(result);
          }

          return result;
        } catch (err) {
          lastError = err instanceof Error ? err : new Error('An unknown error occurred');
          
          // Don't retry on the last attempt
          if (attempt < retries) {
            await sleep(retryDelay * (attempt + 1)); // Exponential backoff
          }
        }
      }

      // All retries failed
      if (lastError) {
        setError(lastError);

        if (options.onError) {
          options.onError(lastError);
        }
      }

      return null;
    },
    [apiFunction, options, retries, retryDelay]
  );

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      setLastArgs(args);
      return executeWithRetry(...args);
    },
    [executeWithRetry]
  );

  const retry = useCallback(async (): Promise<T | null> => {
    if (lastArgs === null) {
      throw new Error('No previous request to retry');
    }
    return executeWithRetry(...lastArgs);
  }, [lastArgs, executeWithRetry]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
    setLastArgs(null);
  }, []);

  // Set loading to false after all attempts
  const wrappedExecute = useCallback(
    async (...args: P): Promise<T | null> => {
      try {
        return await execute(...args);
      } finally {
        setIsLoading(false);
      }
    },
    [execute]
  );

  const wrappedRetry = useCallback(async (): Promise<T | null> => {
    try {
      return await retry();
    } finally {
      setIsLoading(false);
    }
  }, [retry]);

  return {
    data,
    isLoading,
    error,
    execute: wrappedExecute,
    retry: wrappedRetry,
    reset,
  };
}
