export type Decision = "ALLOW" | "SUSPEND" | "DENY" | "ESCALATE";

export interface ScenarioSummary {
  id: string;
  domain: string;
  title: string;
  severity: "success" | "warning" | "danger";
  expected_decision: string;
  description: string;
  raw_text: string;
  safety_warning?: string;
}

export interface RuntimeSummary {
  action: string;
  action_label: string;
  target: string;
  domain: string;
  domain_label: string;
  actor: string;
  environment?: string | null;
  risk_level: string;
  claims_extracted: number;
  sources_checked: number;
  missing_proofs: number;
}

export interface TrustMatrixRow {
  claim: string;
  declared: string;
  source: string;
  status: "verified" | "warning" | "conflict" | "missing";
  source_hint?: string | null;
}

export interface ReasonFactor {
  type: "verified" | "warning" | "conflict" | "missing";
  label: string;
  source: string;
  detail: string;
}

export interface VerificationDetail {
  claim_id?: string | null;
  claim_type?: string | null;
  source_name: string;
  status: "PASSED" | "WARNING" | "FAILED" | "MISSING";
  message: string;
  payload_snapshot: Record<string, unknown>;
}

export interface RuntimeResult {
  scenario?: ScenarioSummary | null;
  doctrine?: string;
  summary?: RuntimeSummary;
  trust_matrix?: TrustMatrixRow[];
  reason_factors?: ReasonFactor[];
  next_required_proofs?: string[];
  decision: Decision;
  reason: string;
  raw_context: Record<string, unknown>;
  normalized_draft: Record<string, unknown>;
  sanitized_draft: Record<string, unknown>;
  envelope: Record<string, unknown>;
  declared_vs_verified: unknown[];
  verified_sources: VerificationDetail[];
  warrant: Record<string, unknown>;
  ledger_preview: Record<string, unknown>;
}
