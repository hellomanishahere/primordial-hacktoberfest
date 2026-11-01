import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  className?: string;
}

export default function LoadingSpinner({
  label = 'Loading…',
  className = '',
}: LoadingSpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-16 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-accent" />
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  );
}

