import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { DecisionSummary } from '../types';
import { fetchDecisions } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';

const STATUS_OPTIONS = ['', 'accepted', 'proposed', 'rejected', 'deferred', 'unclear'];

export default function Decisions() {
  const [decisions, setDecisions] = useState<DecisionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [repoFilter, setRepoFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    fetchDecisions({
      status: statusFilter || undefined,
      repository: repoFilter || undefined,
      limit: 50,
    })
      .then((res) => {
        if ('decisions' in res) {
          setDecisions(res.decisions as DecisionSummary[]);
          setTotal(res.total);
        }
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [statusFilter, repoFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Decisions</h1>
        <p className="mt-1 text-sm text-gray-400">
          All engineering decisions recovered from GitHub discussions.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.filter(Boolean).map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Filter by repository…"
          className="input-field w-auto min-w-[200px]"
          value={repoFilter}
          onChange={(e) => setRepoFilter(e.target.value)}
        />
        <span className="text-xs text-gray-500">{total} decision{total !== 1 ? 's' : ''}</span>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} onRetry={load} />}

      {!loading && !error && decisions.length === 0 && (
        <EmptyState
          title="No decisions found"
          message="Analyze a GitHub discussion to detect and store engineering decisions."
        />
      )}

      {!loading && decisions.length > 0 && (
        <div className="space-y-2">
          {decisions.map((d) => (
            <Link
              key={d.decision_id}
              to={`/decisions/${encodeURIComponent(d.decision_id)}`}
              className="card flex items-center justify-between py-4 hover:border-charcoal-500 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-gray-200">
                  {d.decision_summary}
                </p>
                <p className="mt-0.5 text-xs text-gray-500">
                  {d.repository} #{d.entity_number} ·{' '}
                  {new Date(d.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="ml-4 flex items-center gap-3">
                <StatusBadge status={d.status} />
                {d.adr_id && <span className="text-xs text-cyan-400">ADR</span>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

