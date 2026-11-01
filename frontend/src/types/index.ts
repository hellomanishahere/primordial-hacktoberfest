/* ── TypeScript interfaces matching the backend API response schemas ── */

/* GET /api/v1/overview */
export interface RecentActivity {
  decision_id: string;
  decision_summary: string;
  status: string;
  created_at: string;
  repository: string;
  entity_number: number;
  adr_id: string | null;
}

export interface OverviewMetrics {
  repositories_analyzed: number;
  discussions_processed: number;
  decisions_detected: number;
  verified_decisions: number;
  adrs_generated: number;
  recent_activity: RecentActivity[];
}

/* POST /api/v1/extract */
export interface ExtractRequest {
  url: string;
  model?: string;
  max_tokens?: number;
}

export interface ExtractResponse {
  status: string;
  repository: string;
  entity_number: number;
  resource_type: string;
  source_url: string;
  model_name: string;
  detection: Record<string, unknown>;
  rationale: Record<string, unknown>;
  verification: Record<string, unknown>;
  adrs: Record<string, unknown>;
  persisted: Record<string, unknown>;
}

/* GET /api/v1/decisions */
export interface DecisionSummary {
  decision_id: string;
  decision_summary: string;
  status: string;
  repository: string;
  entity_number: number;
  created_at: string;
  adr_id: string | null;
  source_url?: string;
}

export interface DecisionListResponse {
  total: number;
  decisions: DecisionSummary[];
}

/* GET /api/v1/decisions/:id */
export interface DecisionDetail {
  decision_id: string;
  decision_summary: string;
  status: string;
  repository: string;
  entity_number: number;
  discussion_url: string;
  rationale: string;
  supporting_arguments: Argument[];
  opposing_arguments: Argument[];
  rejected_alternatives: Alternative[];
  trade_offs: string[];
  consequences: string[];
  verification: VerificationInfo | null;
  adr: ADRInfo | null;
  created_at: string;
}

export interface Argument {
  claim: string;
  author: string;
  comment_id: string;
  permalink: string;
}

export interface Alternative {
  alternative_summary: string;
  rejection_reason: string;
  comment_ids: string[];
}

export interface VerificationInfo {
  verification_id: string;
  status: string;
  verified_claims: number;
  total_claims: number;
  contradiction_count: number;
}

export interface ADRInfo {
  adr_id: string;
  title: string;
  markdown?: string;
  markdown_content?: string;
  status: string;
}

export interface ADRRecord {
  adr_id: string;
  decision_id: string;
  discussion_id: string;
  title: string;
  status: string;
  date?: string;
  context?: string;
  problem_statement?: string;
  decision: string;
  file_slug: string;
  markdown_content: string;
  json_content?: string;
  markdown?: string;
  created_at?: string;
}

/* Search (GET /api/v1/decisions?query=...) */
export interface SearchHit {
  decision_id: string;
  title: string;
  summary: string;
  repository: string;
  entity_number: number;
  status: string;
  adr_id: string | null;
  verification_status: string;
  source_url: string;
  match_snippet: string | null;
  confidence: number;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  hits: SearchHit[];
  applied_filters: Record<string, unknown>;
}

/* POST /api/v1/radar/analyze */
export interface RadarRequest {
  url: string;
  threshold?: number;
}

export interface ChangedFile {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  patch: string | null;
}

export interface HistoricalMatch {
  decision_id: string;
  adr_id: string | null;
  decision_summary: string;
  discussion_url: string;
  category: string;
  relevance_explanation: string;
  related_changed_files: string[];
  evidence_references: string[];
  confidence: number;
}

export interface RadarReport {
  pr_info: {
    repository: string;
    pr_number: number;
    title: string;
    url: string;
    author: string;
    description: string;
    changed_files: ChangedFile[];
  };
  historical_matches: HistoricalMatch[];
  potential_conflicts_count: number;
  previously_rejected_count: number;
  recommendations: string[];
  has_relevant_decisions: boolean;
}

/* Health */
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

