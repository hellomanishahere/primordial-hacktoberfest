import { AlertTriangle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({
  message,
  onRetry,
  className = '',
}: ErrorMessageProps) {
  return (
    <div className={`card flex items-start gap-4 border-red-500/30 ${className}`}>
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
      <div className="flex-1">
        <p className="text-sm text-red-300">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 text-sm font-medium text-accent hover:text-accent-light transition-colors"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

