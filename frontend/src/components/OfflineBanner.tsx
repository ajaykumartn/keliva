/**
 * OfflineBanner Component
 * Displays a banner when the user is offline
 */

import { useOnlineStatus } from '../hooks/useOnlineStatus';
import './OfflineBanner.css';

export function OfflineBanner() {
  const isOnline = useOnlineStatus();

  if (isOnline) {
    return null;
  }

  return (
    <div className="offline-banner" role="alert">
      <span className="offline-icon">📡</span>
      <span className="offline-message">
        You're offline. Some features may not be available.
      </span>
    </div>
  );
}
