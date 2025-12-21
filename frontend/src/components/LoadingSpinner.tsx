/**
 * LoadingSpinner Component
 * Reusable loading spinner for async operations
 */

import './LoadingSpinner.css';

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  fullScreen?: boolean;
}

export function LoadingSpinner({ 
  size = 'medium', 
  message, 
  fullScreen = false 
}: LoadingSpinnerProps) {
  const spinner = (
    <div className={`loading-spinner-wrapper ${fullScreen ? 'fullscreen' : ''}`}>
      <div className={`loading-spinner ${size}`}>
        <div className="spinner-circle"></div>
      </div>
      {message && <p className="loading-message">{message}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="loading-overlay">
        {spinner}
      </div>
    );
  }

  return spinner;
}
