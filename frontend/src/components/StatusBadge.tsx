interface StatusBadgeProps {
  status: string;
  className?: string;
}

const colorMap: Record<string, string> = {
  accepted: 'bg-green-500/15 text-green-400 border-green-500/30',
  verified: 'bg-green-500/15 text-green-400 border-green-500/30',
  proposed: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  rejected: 'bg-red-500/15 text-red-400 border-red-500/30',
  contradicted: 'bg-red-500/15 text-red-400 border-red-500/30',
  deferred: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  partially_supported: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  unclear: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  unsupported: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  insufficient_evidence: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  potential_conflict: 'bg-red-500/15 text-red-400 border-red-500/30',
  related_decision: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  previously_rejected_approach: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  potentially_repeated_decision: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  no_relevant_decision: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
};

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const colors = colorMap[status] ?? 'bg-gray-500/15 text-gray-400 border-gray-500/30';
  const label = status.replace(/_/g, ' ');

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${colors} ${className}`}
    >
      {label}
    </span>
  );
}

