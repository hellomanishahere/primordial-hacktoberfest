import { useState } from 'react';
import { Radar, AlertTriangle, CheckCircle2, ExternalLink } from 'lucide-react';
import type { RadarReport } from '../types';
import { analyzeRadar } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function PRRadar() {
  const [url, setUrl] = useState('');
  const [threshold, setThreshold] = useState(0.5);
  const [report, setReport] = useState<RadarReport | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setReport(null);
    analyzeRadar({ url: url.trim(), threshold })
      .then(setReport)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">PR Radar</h1>
        <p className="mt-1 text-sm text-gray-400">
          Analyze a Pull Request against historical engineering decisions to detect conflicts and repeated patterns.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div>
          <label htmlFor="pr-url" className="mb-1.5 block text-sm font-medium text-gray-300">
            Pull Request URL
          </label>
          <input
            id="pr-url"
            type="url"
            required
            placeholder="https://github.com/owner/repo/pull/456"
            className="input-field"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        <div className="max-w-xs">
          <label htmlFor="threshold" className="mb-1.5 block text-sm font-medium text-gray-300">
            Relevance Threshold: {threshold.toFixed(2)}
          </label>
          <input
            id="threshold"
            type="range"
            min="0"
            max="1"
            step="0.05"
            className="w-full accent-accent"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>0 (loose)</span>
            <span>1 (strict)</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="btn-primary flex items-center gap-2"
        >
          <Radar className="h-4 w-4" />
          {loading ? 'Scanning…' : 'Scan PR'}
        </button>
      </form>

      {loading && <LoadingSpinner label="Scanning against historical decisions…" />}
      {error && <ErrorMessage message={error} />}

      {report && (
        <div className="space-y-6">
          {/* PR Info */}
          <div className="card space-y-2">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-white">
                  {report.pr_info.title}
                </h2>
                <p className="text-sm text-gray-400">
                  {report.pr_info.repository} #{report.pr_info.pr_number} by @{report.pr_info.author}
                </p>
              </div>
              <a
                href={report.pr_info.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary flex items-center gap-1 text-xs"
              >
                GitHub <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <p className="text-sm text-gray-400">
              {report.pr_info.changed_files.length} file{report.pr_info.changed_files.length !== 1 ? 's' : ''} changed
            </p>
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard
              label="Historical Matches"
              value={report.historical_matches.length}
              highlight={report.has_relevant_decisions}
            />
            <StatCard
              label="Potential Conflicts"
              value={report.potential_conflicts_count}
              danger={report.potential_conflicts_count > 0}
            />
            <StatCard
              label="Previously Rejected"
              value={report.previously_rejected_count}
              danger={report.previously_rejected_count > 0}
            />
            <StatCard
              label="Relevant Decisions"
              value={report.has_relevant_decisions ? 'Yes' : 'No'}
              highlight={report.has_relevant_decisions}
            />
          </div>

          {/* Recommendations */}
          {report.recommendations.length > 0 && (
            <div className="card space-y-3">
              <h3 className="flex items-center gap-2 font-semibold text-white">
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
                Recommendations
              </h3>
              <ul className="space-y-2">
                {report.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-400" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Matches */}
          {report.historical_matches.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-white">Historical Matches</h3>
              {report.historical_matches.map((m, i) => (
                <div key={i} className="card space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-gray-200">{m.decision_summary}</p>
                    <StatusBadge status={m.category} />
                  </div>
                  <p className="text-sm text-gray-400">{m.relevance_explanation}</p>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                    <span>Confidence: {(m.confidence * 100).toFixed(0)}%</span>
                    <a
                      href={m.discussion_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent-light"
                    >
                      Original Discussion ↗
                    </a>
                    {m.related_changed_files.length > 0 && (
                      <span>Files: {m.related_changed_files.join(', ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!report.has_relevant_decisions && (
            <div className="card flex items-center gap-3 border-green-500/30">
              <CheckCircle2 className="h-5 w-5 text-green-400" />
              <p className="text-sm text-green-300">
                No historical conflicts or previously rejected approaches detected.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight = false,
  danger = false,
}: {
  label: string;
  value: number | string;
  highlight?: boolean;
  danger?: boolean;
}) {
  return (
    <div className="card">
      <p className="text-xs text-gray-400">{label}</p>
      <p
        className={`mt-1 text-2xl font-bold ${
          danger ? 'text-red-400' : highlight ? 'text-accent' : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
