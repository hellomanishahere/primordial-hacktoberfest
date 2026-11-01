import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Calendar, GitCommit } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ADRRecord, DecisionDetail } from '../types';
import { fetchDecisionADR, fetchDecision } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';

export default function ADRViewPage() {
  const { id } = useParams<{ id: string }>();
  const [adr, setAdr] = useState<ADRRecord | null>(null);
  const [decision, setDecision] = useState<DecisionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    if (!id) return;
    setLoading(true);
    setError('');

    Promise.all([
      fetchDecisionADR(id),
      fetchDecision(id).catch(() => null),
    ])
      .then(([adrData, decData]) => {
        setAdr(adrData);
        setDecision(decData);
      })
      .catch((e: Error) => {
        setError(e.message);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  if (loading) return <LoadingSpinner label="Loading architectural decision record…" />;
  if (error) return <ErrorMessage message={error} onRetry={load} />;
  if (!adr) {
    return (
      <div className="space-y-6">
        <Link
          to={id ? `/decisions/${encodeURIComponent(id)}` : '/decisions'}
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-accent transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Decision
        </Link>
        <EmptyState
          title="No ADR found"
          message="An Architectural Decision Record has not been generated for this decision yet."
        />
      </div>
    );
  }

  const markdownText = adr.markdown_content || adr.markdown || '';

  return (
    <div className="space-y-6">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={`/decisions/${encodeURIComponent(id!)}`}
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-accent transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Decision Detail
        </Link>
        <Link
          to="/adrs"
          className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          Browse ADR Library →
        </Link>
      </div>

      {/* ADR Header Card */}
      <div className="card space-y-4 border-cyan-500/30">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider">
                {adr.adr_id}
              </span>
              {adr.file_slug && (
                <span className="text-xs text-gray-500 font-mono">
                  · {adr.file_slug}.md
                </span>
              )}
            </div>
            <h1 className="mt-1 text-2xl font-bold text-white">
              {adr.title}
            </h1>
          </div>
          <StatusBadge status={adr.status} />
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400 border-t border-charcoal-800 pt-3">
          {adr.date && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-gray-500" />
              {adr.date}
            </span>
          )}
          {decision && (
            <>
              <span className="inline-flex items-center gap-1">
                <GitCommit className="h-3.5 w-3.5 text-gray-500" />
                {decision.repository} #{decision.entity_number}
              </span>
              {decision.discussion_url && (
                <a
                  href={decision.discussion_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-accent hover:text-accent-light"
                >
                  Source Discussion <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </>
          )}
        </div>
      </div>

      {/* Markdown Document Container */}
      <div className="card">
        {markdownText ? (
          <article className="prose prose-invert max-w-none space-y-4 text-gray-300">
            <ReactMarkdown
              components={{
                h1: ({ ...props }) => (
                  <h1 className="text-xl font-bold text-white border-b border-charcoal-700 pb-2 mb-4" {...props} />
                ),
                h2: ({ ...props }) => (
                  <h2 className="text-lg font-semibold text-white mt-6 mb-3 flex items-center gap-2" {...props} />
                ),
                h3: ({ ...props }) => (
                  <h3 className="text-base font-medium text-gray-200 mt-4 mb-2" {...props} />
                ),
                p: ({ ...props }) => (
                  <p className="text-sm leading-relaxed text-gray-300 mb-3" {...props} />
                ),
                ul: ({ ...props }) => (
                  <ul className="list-disc pl-5 space-y-1.5 text-sm text-gray-300 mb-4" {...props} />
                ),
                ol: ({ ...props }) => (
                  <ol className="list-decimal pl-5 space-y-1.5 text-sm text-gray-300 mb-4" {...props} />
                ),
                li: ({ ...props }) => (
                  <li className="leading-relaxed" {...props} />
                ),
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  return isInline ? (
                    <code className="rounded bg-charcoal-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300" {...props}>
                      {children}
                    </code>
                  ) : (
                    <pre className="overflow-x-auto rounded-lg bg-charcoal-950 p-4 font-mono text-xs text-gray-300">
                      <code {...props}>{children}</code>
                    </pre>
                  );
                },
                blockquote: ({ ...props }) => (
                  <blockquote className="border-l-4 border-cyan-500/50 pl-4 py-1 italic text-gray-400 bg-charcoal-950/50 rounded-r" {...props} />
                ),
                a: ({ ...props }) => (
                  <a className="text-accent hover:text-accent-light underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />
                ),
                hr: () => <hr className="border-charcoal-800 my-6" />,
              }}
            >
              {markdownText}
            </ReactMarkdown>
          </article>
        ) : (
          <EmptyState
            title="Markdown content empty"
            message="This ADR record does not contain markdown text."
          />
        )}
      </div>
    </div>
  );
}

