/**
 * ToastContext
 * Global context for managing toast notifications
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ToastContainer } from '../components/ToastContainer';
import { ToastProps, ToastType } from '../components/Toast';

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = 'info', duration = 5000) => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      const newToast: ToastProps = {
        id,
        type,
        message,
        duration,
        onClose: removeToast,
      };

      setToasts((prev) => [...prev, newToast]);
    },
    [removeToast]
  );

  const showError = useCallback(
    (message: string, duration = 5000) => {
      showToast(message, 'error', duration);
    },
    [showToast]
  );

  const showSuccess = useCallback(
    (message: string, duration = 5000) => {
      showToast(message, 'success', duration);
    },
    [showToast]
  );

  const showInfo = useCallback(
    (message: string, duration = 5000) => {
      showToast(message, 'info', duration);
    },
    [showToast]
  );

  const showWarning = useCallback(
    (message: string, duration = 5000) => {
      showToast(message, 'warning', duration);
    },
    [showToast]
  );

  return (
    <ToastContext.Provider
      value={{
        showToast,
        showError,
        showSuccess,
        showInfo,
        showWarning,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
