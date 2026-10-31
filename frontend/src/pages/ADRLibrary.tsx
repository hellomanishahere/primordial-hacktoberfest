import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';
import type { DecisionSummary } from '../types';
import { fetchDecisions } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import StatusBadge from '../components/StatusBadge';

export default function ADRLibrary() {
  const [decisions, setDecisions] = useState<DecisionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    fetchDecisions({ limit: 100 })
      .then((res) => {
        if ('decisions' in res) {
          // Only show decisions that have an ADR
          setDecisions(
            (res.decisions as DecisionSummary[]).filter((d) => d.adr_id),
          );
        }
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">ADR Library</h1>
        <p className="mt-1 text-sm text-gray-400">
          Architectural Decision Records generated from real engineering discussions.
        </p>
      </div>

      {loading && <LoadingSpinner label="Loading ADR library…" />}
      {error && <ErrorMessage message={error} onRetry={load} />}

      {!loading && !error && decisions.length === 0 && (
        <EmptyState
          title="No ADRs yet"
          message="ADRs are generated when you analyze a GitHub discussion through the pipeline."
        />
      )}

      {!loading && decisions.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {decisions.map((d) => (
            <Link
              key={d.decision_id}
              to={`/decisions/${encodeURIComponent(d.decision_id)}`}
              className="card group space-y-3 hover:border-cyan-500/40 transition-colors"
            >
              <div className="flex items-center gap-2 text-cyan-400">
                <FileText className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wider">
                  {d.adr_id}
                </span>
              </div>
              <p className="line-clamp-2 font-medium text-gray-200 group-hover:text-white transition-colors">
                {d.decision_summary}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">{d.repository}</span>
                <StatusBadge status={d.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
