import { useEffect, useState } from 'react';
import { Server, Activity } from 'lucide-react';
import { fetchHealth } from '../api/client';
import type { HealthResponse } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e: Error) => setHealthError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-400">Application configuration and backend status.</p>
      </div>

      {/* Backend Health */}
      <div className="card space-y-4">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <Server className="h-5 w-5 text-accent" />
          Backend Status
        </h2>

        {loading && <LoadingSpinner label="Checking backend…" />}

        {health && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <InfoRow label="Service" value={health.service} />
            <InfoRow label="Version" value={health.version} />
            <InfoRow
              label="Status"
              value={health.status}
              valueClass={health.status === 'healthy' ? 'text-green-400' : 'text-red-400'}
            />
          </div>
        )}

        {healthError && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3">
            <p className="text-sm text-red-300">
              Backend unreachable: {healthError}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Start the backend with: <code className="text-gray-400">uvicorn app.main:app --reload</code>
            </p>
          </div>
        )}
      </div>

      {/* Frontend Info */}
      <div className="card space-y-4">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <Activity className="h-5 w-5 text-accent" />
          Application Info
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <InfoRow label="Frontend" value="React 18 + Vite + Tailwind CSS" />
          <InfoRow label="Backend" value="FastAPI + SQLite" />
          <InfoRow label="AI Engine" value="Ollama (Qwen 2.5 7B)" />
        </div>
      </div>

      {/* API Endpoints Reference */}
      <div className="card space-y-4">
        <h2 className="text-lg font-semibold text-white">API Endpoints</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-charcoal-700 text-gray-400">
                <th className="pb-2 pr-4 font-medium">Method</th>
                <th className="pb-2 pr-4 font-medium">Path</th>
                <th className="pb-2 font-medium">Description</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              {[
                ['GET', '/api/v1/health', 'Health check'],
                ['GET', '/api/v1/overview', 'Dashboard metrics'],
                ['POST', '/api/v1/extract', 'Run full pipeline'],
                ['GET', '/api/v1/decisions', 'List/search decisions'],
                ['GET', '/api/v1/decisions/:id', 'Decision details'],
                ['GET', '/api/v1/decisions/:id/adr', 'Get ADR for decision'],
                ['POST', '/api/v1/radar/analyze', 'PR Radar analysis'],
              ].map(([method, path, desc]) => (
                <tr key={path} className="border-b border-charcoal-800">
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs font-mono ${
                        method === 'GET' ? 'bg-green-500/15 text-green-400' : 'bg-blue-500/15 text-blue-400'
                      }`}
                    >
                      {method}
                    </span>
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-400">{path}</td>
                  <td className="py-2 text-gray-400">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  valueClass = 'text-gray-200',
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg bg-charcoal-950 px-4 py-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-0.5 text-sm font-medium ${valueClass}`}>{value}</p>
    </div>
  );
}
