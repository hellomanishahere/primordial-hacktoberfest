import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ExternalLink, FileText } from 'lucide-react';
import type { DecisionDetail } from '../types';
import { fetchDecision } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function DecisionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<DecisionDetail | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!id) return;
    setLoading(true);
    setError('');
    fetchDecision(id)
      .then(setDetail)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  if (loading) return <LoadingSpinner label="Loading decision…" />;
  if (error) return <ErrorMessage message={error} onRetry={load} />;
  if (!detail) return null;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/decisions"
        className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-accent transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Decisions
      </Link>

      {/* Header */}
      <div className="card space-y-3">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-xl font-bold text-white">{detail.decision_summary}</h1>
          <StatusBadge status={detail.status} />
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
          <span>{detail.repository} #{detail.entity_number}</span>
          <a
            href={detail.discussion_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-accent hover:text-accent-light"
          >
            View Discussion <ExternalLink className="h-3 w-3" />
          </a>
          {detail.adr && (
            <Link
              to={`/decisions/${encodeURIComponent(detail.decision_id)}/adr`}
              className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
            >
              <FileText className="h-3 w-3" /> View ADR
            </Link>
          )}
        </div>
      </div>

      {/* Rationale */}
      {detail.rationale && (
        <Section title="Rationale">
          <p className="text-sm text-gray-300 leading-relaxed">{detail.rationale}</p>
        </Section>
      )}

      {/* Supporting Arguments */}
      {detail.supporting_arguments?.length > 0 && (
        <Section title="Supporting Arguments">
          <ArgumentList args={detail.supporting_arguments} />
        </Section>
      )}

      {/* Opposing Arguments */}
      {detail.opposing_arguments?.length > 0 && (
        <Section title="Opposing Arguments">
          <ArgumentList args={detail.opposing_arguments} />
        </Section>
      )}

      {/* Rejected Alternatives */}
      {detail.rejected_alternatives?.length > 0 && (
        <Section title="Rejected Alternatives">
          {detail.rejected_alternatives.map((alt, i) => (
            <div key={i} className="rounded-lg bg-charcoal-950 p-4">
              <p className="font-medium text-gray-200">{alt.alternative_summary}</p>
              <p className="mt-1 text-sm text-gray-400">
                Reason: {alt.rejection_reason}
              </p>
            </div>
          ))}
        </Section>
      )}

      {/* Trade-offs */}
      {detail.trade_offs?.length > 0 && (
        <Section title="Trade-offs">
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-300">
            {detail.trade_offs.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Consequences */}
      {detail.consequences?.length > 0 && (
        <Section title="Consequences">
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-300">
            {detail.consequences.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Verification */}
      {detail.verification && (
        <Section title="Evidence Verification">
          <div className="flex flex-wrap gap-4 text-sm">
            <StatPill label="Status" value={detail.verification.status} />
            <StatPill
              label="Verified"
              value={`${detail.verification.verified_claims}/${detail.verification.total_claims}`}
            />
            <StatPill
              label="Contradictions"
              value={String(detail.verification.contradiction_count)}
            />
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card space-y-3">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      {children}
    </div>
  );
}

function ArgumentList({ args }: { args: { claim: string; author: string; comment_id: string; permalink: string }[] }) {
  return (
    <div className="space-y-3">
      {args.map((a, i) => (
        <div key={i} className="rounded-lg bg-charcoal-950 p-4">
          <p className="text-sm text-gray-300">{a.claim}</p>
          <p className="mt-2 text-xs text-gray-500">
            — {a.author}{' '}
            <a
              href={a.permalink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:text-accent-light"
            >
              #{a.comment_id}
            </a>
          </p>
        </div>
      ))}
    </div>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-charcoal-950 px-4 py-2">
      <span className="text-xs text-gray-500">{label}</span>
      <p className="text-sm font-medium text-gray-200">{value}</p>
    </div>
  );
}

