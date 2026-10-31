import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  className?: string;
}

export default function EmptyState({
  title = 'Nothing here yet',
  message = 'Start by analyzing a GitHub discussion.',
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-16 ${className}`}>
      <Inbox className="h-12 w-12 text-charcoal-500" />
      <h3 className="text-lg font-semibold text-gray-300">{title}</h3>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}

