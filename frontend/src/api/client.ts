/* ── Centralized API client for all Primordial backend endpoints ── */

import type {
  DecisionDetail,
  DecisionListResponse,
  ExtractRequest,
  ExtractResponse,
  HealthResponse,
  OverviewMetrics,
  RadarReport,
  RadarRequest,
  SearchResponse,
} from '../types';

const BASE = import.meta.env.VITE_API_BASE_URL ?? '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/* ── Health ── */
export const fetchHealth = () => request<HealthResponse>('/api/v1/health');

/* ── Overview Dashboard ── */
export const fetchOverview = () => request<OverviewMetrics>('/api/v1/overview');

/* ── Pipeline Extraction ── */
export const extractDiscussion = (payload: ExtractRequest) =>
  request<ExtractResponse>('/api/v1/extract', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/* ── Decisions ── */
export const fetchDecisions = (params?: {
  query?: string;
  repository?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) => {
  const searchParams = new URLSearchParams();
  if (params?.query) searchParams.set('query', params.query);
  if (params?.repository) searchParams.set('repository', params.repository);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  const qs = searchParams.toString();
  return request<DecisionListResponse | SearchResponse>(
    `/api/v1/decisions${qs ? `?${qs}` : ''}`,
  );
};

export const fetchDecision = (id: string) =>
  request<DecisionDetail>(`/api/v1/decisions/${encodeURIComponent(id)}`);

export const fetchDecisionADR = (id: string) =>
  request<{ adr_id: string; title: string; markdown: string; status: string }>(
    `/api/v1/decisions/${encodeURIComponent(id)}/adr`,
  );

/* ── PR Radar ── */
export const analyzeRadar = (payload: RadarRequest) =>
  request<RadarReport>('/api/v1/radar/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

