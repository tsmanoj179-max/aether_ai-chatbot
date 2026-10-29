import React from 'react';
import { ToastMessage } from '../../store/useAppStore';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

interface ToastProps {
  toasts: ToastMessage[];
  onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onRemove }) => {
  if (!toasts.length) return null;

  return (
    <div
      role="region"
      aria-label="Notifications"
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-[calc(100vw-40px)] pointer-events-none"
    >
      {toasts.map(toast => {
        let Icon = Info;
        let iconClass = 'text-blue-600 dark:text-blue-400';
        let styleClass =
          'border-blue-500/30 bg-card/95 text-blue-950 dark:text-blue-100 dark:bg-blue-950/40 shadow-blue-500/5';

        if (toast.type === 'success') {
          Icon = CheckCircle2;
          iconClass = 'text-emerald-600 dark:text-emerald-400';
          styleClass =
            'border-emerald-500/30 bg-card/95 text-emerald-950 dark:text-emerald-100 dark:bg-emerald-950/40 shadow-emerald-500/5';
        } else if (toast.type === 'warning') {
          Icon = AlertTriangle;
          iconClass = 'text-amber-600 dark:text-amber-400';
          styleClass =
            'border-amber-500/30 bg-card/95 text-amber-950 dark:text-amber-100 dark:bg-amber-950/40 shadow-amber-500/5';
        } else if (toast.type === 'error') {
          Icon = AlertCircle;
          iconClass = 'text-rose-600 dark:text-rose-400';
          styleClass =
            'border-rose-500/30 bg-card/95 text-rose-950 dark:text-rose-100 dark:bg-rose-950/40 shadow-rose-500/5';
        }

        return (
          <div
            key={toast.id}
            role="status"
            aria-live="polite"
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border backdrop-blur-md shadow-xl transition-all animate-in fade-in slide-in-from-bottom-2 ${styleClass}`}
          >
            <Icon className={`w-4 h-4 shrink-0 mt-0.5 ${iconClass}`} />
            <div className="flex-1 text-xs leading-relaxed font-medium break-words">{toast.text}</div>
            <button
              onClick={() => onRemove(toast.id)}
              aria-label="Dismiss notification"
              className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
