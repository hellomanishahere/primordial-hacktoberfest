import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Database,
  MessageSquare,
  Lightbulb,
  ShieldCheck,
  FileText,
  ArrowRight,
} from 'lucide-react';
import type { OverviewMetrics } from '../types';
import { fetchOverview } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function Overview() {
  const [data, setData] = useState<OverviewMetrics | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError('');
    fetchOverview()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <LoadingSpinner label="Loading dashboard…" />;
  if (error) return <ErrorMessage message={error} onRetry={load} />;
  if (!data) return null;

  const stats = [
    { label: 'Repositories', value: data.repositories_analyzed, icon: Database, color: 'text-blue-400' },
    { label: 'Discussions', value: data.discussions_processed, icon: MessageSquare, color: 'text-purple-400' },
    { label: 'Decisions', value: data.decisions_detected, icon: Lightbulb, color: 'text-yellow-400' },
    { label: 'Verified', value: data.verified_decisions, icon: ShieldCheck, color: 'text-green-400' },
    { label: 'ADRs', value: data.adrs_generated, icon: FileText, color: 'text-cyan-400' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-400">
          Knowledge recovered from open-source engineering discussions.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`rounded-lg bg-charcoal-800 p-2.5 ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-xs text-gray-400">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          to="/analyze"
          className="card group flex items-center justify-between hover:border-accent/40 transition-colors"
        >
          <div>
            <h3 className="font-semibold text-white">Analyze a Discussion</h3>
            <p className="mt-1 text-sm text-gray-400">
              Extract decisions from a GitHub Issue or PR.
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-500 group-hover:text-accent transition-colors" />
        </Link>
        <Link
          to="/radar"
          className="card group flex items-center justify-between hover:border-accent/40 transition-colors"
        >
          <div>
            <h3 className="font-semibold text-white">PR Radar</h3>
            <p className="mt-1 text-sm text-gray-400">
              Check a Pull Request against historical decisions.
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-500 group-hover:text-accent transition-colors" />
        </Link>
      </div>

      {/* Recent Activity */}
      {data.recent_activity.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-white">Recent Activity</h2>
          <div className="space-y-2">
            {data.recent_activity.map((item) => (
              <Link
                key={item.decision_id}
                to={`/decisions/${encodeURIComponent(item.decision_id)}`}
                className="card flex items-center justify-between py-4 hover:border-charcoal-500 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-gray-200">
                    {item.decision_summary}
                  </p>
                  <p className="mt-0.5 text-xs text-gray-500">
                    {item.repository} #{item.entity_number}
                  </p>
                </div>
                <div className="ml-4 flex items-center gap-3">
                  <StatusBadge status={item.status} />
                  {item.adr_id && (
                    <span className="text-xs text-cyan-400">ADR</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

