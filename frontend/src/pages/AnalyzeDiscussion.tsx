import { useState } from 'react';
import { FlaskConical, ExternalLink, CheckCircle2 } from 'lucide-react';
import type { ExtractResponse } from '../types';
import { extractDiscussion } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function AnalyzeDiscussion() {
  const [url, setUrl] = useState('');
  const [model, setModel] = useState('');
  const [maxTokens, setMaxTokens] = useState(12000);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    extractDiscussion({
      url: url.trim(),
      model: model.trim() || undefined,
      max_tokens: maxTokens,
    })
      .then(setResult)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Analyze Discussion</h1>
        <p className="mt-1 text-sm text-gray-400">
          Paste a GitHub Issue or Pull Request URL to run the full decision intelligence pipeline.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div>
          <label htmlFor="gh-url" className="mb-1.5 block text-sm font-medium text-gray-300">
            GitHub URL
          </label>
          <input
            id="gh-url"
            type="url"
            required
            placeholder="https://github.com/owner/repo/pull/123"
            className="input-field"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="model" className="mb-1.5 block text-sm font-medium text-gray-300">
              AI Model
              <span className="ml-1 text-xs text-gray-500">(optional)</span>
            </label>
            <input
              id="model"
              type="text"
              placeholder="qwen2.5:7b"
              className="input-field"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="max-tokens" className="mb-1.5 block text-sm font-medium text-gray-300">
              Max Tokens
            </label>
            <input
              id="max-tokens"
              type="number"
              min={1000}
              max={32000}
              className="input-field"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="btn-primary flex items-center gap-2"
        >
          <FlaskConical className="h-4 w-4" />
          {loading ? 'Analyzing…' : 'Run Pipeline'}
        </button>
      </form>

      {loading && (
        <LoadingSpinner label="Running decision intelligence pipeline — this may take a few minutes…" />
      )}

      {error && <ErrorMessage message={error} />}

      {result && (
        <div className="space-y-6">
          {/* Success banner */}
          <div className="card flex items-start gap-3 border-green-500/30">
            <CheckCircle2 className="mt-0.5 h-5 w-5 text-green-400" />
            <div>
              <p className="font-semibold text-green-300">Pipeline completed successfully</p>
              <p className="mt-1 text-sm text-gray-400">
                {result.repository} #{result.entity_number} · {result.resource_type}
              </p>
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <InfoCard label="Model" value={result.model_name} />
            <InfoCard label="Status" value={result.status} />
            <InfoCard label="Source" value={result.resource_type} />
            <div className="card flex flex-col gap-1">
              <span className="text-xs text-gray-400">Source URL</span>
              <a
                href={result.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 truncate text-sm font-medium text-accent hover:text-accent-light"
              >
                View on GitHub <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          {/* Detection summary */}
          <CollapsibleSection title="Detection Result" data={result.detection} />
          <CollapsibleSection title="Rationale Extraction" data={result.rationale} />
          <CollapsibleSection title="Evidence Verification" data={result.verification} />
          <CollapsibleSection title="ADR Generation" data={result.adrs} />
          <CollapsibleSection title="Persistence" data={result.persisted} />
        </div>
      )}
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card flex flex-col gap-1">
      <span className="text-xs text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-200">{value}</span>
    </div>
  );
}

function CollapsibleSection({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown>;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="font-semibold text-gray-200">{title}</span>
        <span className="text-xs text-gray-500">{open ? '▲ Collapse' : '▼ Expand'}</span>
      </button>
      {open && (
        <pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-charcoal-950 p-4 text-xs text-gray-300">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

