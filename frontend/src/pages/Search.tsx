import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search as SearchIcon } from 'lucide-react';
import type { SearchHit, SearchResponse } from '../types';
import { fetchDecisions } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [repoFilter, setRepoFilter] = useState('');
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [totalHits, setTotalHits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    fetchDecisions({
      query: query.trim(),
      status: statusFilter || undefined,
      repository: repoFilter || undefined,
      limit: 50,
    })
      .then((res) => {
        if ('hits' in res) {
          const sr = res as SearchResponse;
          setResults(sr.hits);
          setTotalHits(sr.total_hits);
        } else {
          setResults([]);
          setTotalHits(0);
        }
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Search Decisions</h1>
        <p className="mt-1 text-sm text-gray-400">
          Full-text search across all recovered engineering decisions.
        </p>
      </div>

      <form onSubmit={handleSearch} className="card space-y-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search decisions, rationale, arguments…"
              className="input-field pl-10"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button type="submit" disabled={loading || !query.trim()} className="btn-primary">
            Search
          </button>
        </div>

        <div className="flex flex-wrap gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field w-auto"
          >
            <option value="">All statuses</option>
            <option value="accepted">Accepted</option>
            <option value="proposed">Proposed</option>
            <option value="rejected">Rejected</option>
            <option value="deferred">Deferred</option>
            <option value="unclear">Unclear</option>
          </select>
          <input
            type="text"
            placeholder="Repository filter…"
            className="input-field w-auto min-w-[200px]"
            value={repoFilter}
            onChange={(e) => setRepoFilter(e.target.value)}
          />
        </div>
      </form>

      {loading && <LoadingSpinner label="Searching…" />}
      {error && <ErrorMessage message={error} />}

      {results !== null && !loading && (
        <>
          <p className="text-sm text-gray-400">
            {totalHits} result{totalHits !== 1 ? 's' : ''} found
          </p>

          {results.length === 0 ? (
            <EmptyState title="No matches" message="Try different keywords or remove filters." />
          ) : (
            <div className="space-y-2">
              {results.map((hit) => (
                <Link
                  key={hit.decision_id}
                  to={`/decisions/${encodeURIComponent(hit.decision_id)}`}
                  className="card block space-y-2 py-4 hover:border-charcoal-500 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-gray-200">{hit.title || hit.summary}</p>
                    <div className="flex shrink-0 items-center gap-2">
                      <StatusBadge status={hit.status} />
                      <StatusBadge status={hit.verification_status} />
                    </div>
                  </div>
                  {hit.match_snippet && (
                    <p className="text-sm text-gray-400 line-clamp-2">{hit.match_snippet}</p>
                  )}
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>{hit.repository} #{hit.entity_number}</span>
                    <span>Confidence: {(hit.confidence * 100).toFixed(0)}%</span>
                    {hit.adr_id && <span className="text-cyan-400">ADR</span>}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
