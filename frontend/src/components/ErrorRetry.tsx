/**
 * ErrorRetry Component
 * Displays error message with retry button
 */

import './ErrorRetry.css';

export interface ErrorRetryProps {
  message: string;
  onRetry: () => void;
  isRetrying?: boolean;
}

export function ErrorRetry({ message, onRetry, isRetrying = false }: ErrorRetryProps) {
  return (
    <div className="error-retry">
      <div className="error-retry-content">
        <span className="error-retry-icon">⚠️</span>
        <p className="error-retry-message">{message}</p>
        <button
          className="error-retry-button"
          onClick={onRetry}
          disabled={isRetrying}
        >
          {isRetrying ? 'Retrying...' : 'Try Again'}
        </button>
      </div>
    </div>
  );
}
