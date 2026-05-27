import { useEffect, useMemo, useState } from "react";
import { evaluateRawContext, evaluateRuntimeScenario, fetchRuntimeScenarios } from "./api";
import type { RuntimeResult, ScenarioSummary, TrustMatrixRow } from "./types";

const DEFAULT_CUSTOM_CONTEXT =
  "sec_agent_bot says EDR critical alert confirmed: ransomware behavior detected. Isolate endpoint FIN-042. Asset belongs to CFO VIP machine.";

function decisionTone(decision?: string) {
  if (decision === "ALLOW") return "allow";
  if (decision === "DENY") return "deny";
  if (decision === "ESCALATE") return "escalate";
  return "suspend";
}

function statusLabel(status: string) {
  if (status === "verified") return "Verified";
  if (status === "warning") return "Risk raised";
  if (status === "missing") return "Missing proof";
  return "Conflict";
}

function factorIcon(type: string) {
  if (type === "verified") return "✓";
  if (type === "warning") return "⚠";
  if (type === "missing") return "✕";
  return "!";
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

function ProgressLine({ result }: { result: RuntimeResult | null }) {
  const decision = result?.decision;
  const steps = [
    { label: "Agent intent", value: result ? "Parsed" : "Waiting", tone: "intent" },
    { label: "Extracted claims", value: result?.summary ? `${result.summary.claims_extracted} unverified claims` : "Waiting", tone: "claims" },
    { label: "Source verification", value: result?.summary ? `${result.summary.sources_checked} source checks` : "Waiting", tone: "verify" },
    { label: "Warrant decision", value: decision ?? "Waiting", tone: decisionTone(decision) },
  ];

  return (
    <section className="progress-line">
      {steps.map((step, index) => (
        <div className={`progress-step ${step.tone}`} key={step.label}>
          <span>{index + 1}</span>
          <div>
            <strong>{step.label}</strong>
            <small>{step.value}</small>
          </div>
        </div>
      ))}
    </section>
  );
}

function SummaryChips({ result }: { result: RuntimeResult | null }) {
  const summary = result?.summary;

  const chips = [
    ["Actor", summary?.actor ?? "—"],
    ["Action", summary?.action_label ?? "—"],
    ["Target", summary?.target ?? "—"],
    ["Domain", summary?.domain_label ?? "—"],
    ["Risk", summary?.risk_level ?? "—"],
  ];

  return (
    <section className="summary-chips">
      {chips.map(([label, value]) => (
        <div className="chip" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}

function TrustMatrix({ rows }: { rows: TrustMatrixRow[] }) {
  return (
    <div className="trust-table">
      <div className="trust-head">
        <span>Claim</span>
        <span>Agent declared</span>
        <span>Enterprise source</span>
        <span>AXIOM status</span>
      </div>

      {rows.length === 0 && (
        <div className="trust-empty">Run an evaluation to build the trust matrix.</div>
      )}

      {rows.map((row, index) => (
        <div className="trust-row" key={`${row.claim}-${index}`}>
          <strong>{row.claim}</strong>
          <span>{row.declared}</span>
          <span>{row.source}</span>
          <em className={`status-${row.status}`}>{statusLabel(row.status)}</em>
        </div>
      ))}
    </div>
  );
}

function DecisionCard({ result }: { result: RuntimeResult | null }) {
  const decision = result?.decision ?? "SUSPEND";
  const tone = decisionTone(decision);
  const factors = result?.reason_factors ?? [];
  const nextProofs = result?.next_required_proofs ?? [];

  return (
    <section className={`decision-card ${tone}`}>
      <div className="decision-left">
        <span className="section-kicker">4. Warrant decision</span>
        <strong>{decision}</strong>
        <p>{result?.reason ?? "AXIOM is waiting for an action request."}</p>
      </div>

      <div className="decision-right">
        <div className="why-box">
          <h3>Why?</h3>
          {factors.length === 0 && <p className="muted">Run an evaluation to see decision factors.</p>}
          {factors.slice(0, 5).map((factor, index) => (
            <div className={`factor ${factor.type}`} key={`${factor.label}-${index}`}>
              <span>{factorIcon(factor.type)}</span>
              <div>
                <strong>{factor.label}</strong>
                <small>{factor.detail}</small>
              </div>
            </div>
          ))}
        </div>

        <div className="next-proof-box">
          <h3>Next required proof</h3>
          {nextProofs.map((proof, index) => (
            <div className="next-proof" key={`${proof}-${index}`}>{proof}</div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [activeScenario, setActiveScenario] = useState("devops_deploy");
  const [result, setResult] = useState<RuntimeResult | null>(null);
  const [customText, setCustomText] = useState(DEFAULT_CUSTOM_CONTEXT);
  const [customMode, setCustomMode] = useState(false);
  const [tab, setTab] = useState<"warrant" | "audit">("warrant");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const active = useMemo(
    () => scenarios.find((scenario) => scenario.id === activeScenario),
    [scenarios, activeScenario]
  );

  useEffect(() => {
    fetchRuntimeScenarios()
      .then(async (items) => {
        setScenarios(items);
        if (items.length > 0) {
          setActiveScenario(items[0].id);
          setCustomText(items[0].raw_text);
          const payload = await evaluateRuntimeScenario(items[0].id);
          setResult(payload);
        }
      })
      .catch((err) => setError(String(err)));
  }, []);

  async function runScenario(id: string) {
    const scenario = scenarios.find((item) => item.id === id);
    if (scenario) {
      setCustomText(scenario.raw_text);
    }

    setCustomMode(false);
    setActiveScenario(id);
    setLoading(true);
    setError("");

    try {
      const payload = await evaluateRuntimeScenario(id);
      setResult(payload);
      setTab("warrant");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function runCustomContext() {
    setCustomMode(true);
    setLoading(true);
    setError("");

    try {
      const payload = await evaluateRawContext(customText);
      setResult(payload);
      setTab("warrant");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function updateCustomText(value: string) {
    setCustomMode(true);
    setCustomText(value);
  }

  return (
    <main className="axiom-room">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AX</div>
          <div>
            <strong>AXIOM</strong>
            <span>Decision Room</span>
          </div>
        </div>

        <div className="side-label">Scenarios</div>

        <div className="scenario-list">
          {scenarios.map((scenario) => (
            <button
              key={scenario.id}
              className={`scenario-card ${activeScenario === scenario.id && !customMode ? "active" : ""}`}
              onClick={() => runScenario(scenario.id)}
            >
              <span>{scenario.domain}</span>
              <strong>{scenario.title}</strong>
              <small>{scenario.description}</small>
              <em>{scenario.expected_decision}</em>
            </button>
          ))}
        </div>

        <button className={`custom-button ${customMode ? "active" : ""}`} onClick={() => setCustomMode(true)}>
          Test your own context
        </button>

        <div className="safety-box">
          <strong>Public demo safety</strong>
          <span>Use synthetic or anonymized data only. Do not paste secrets, credentials, API keys, customer data, or production logs.</span>
        </div>
      </aside>

      <section className="main">
        <header className="hero">
          <div>
            <p className="eyebrow">AXIOM Decision Room</p>
            <h1>Can this AI agent act safely?</h1>
            <p className="subtitle">
              AXIOM checks what the agent declares against what your enterprise systems can verify — before any critical action is executed.
            </p>
          </div>

          <div className="doctrine">
            AXIOM separates what the agent says from what your systems can prove.
          </div>
        </header>

        {error && <div className="error-box">{error}</div>}

        <ProgressLine result={result} />

        <section className="input-card">
          <div className="input-head">
            <div>
              <span className="section-kicker">1. Agent intent</span>
              <h2>Paste an agent action request</h2>
            </div>
            <button onClick={runCustomContext} disabled={loading}>
              {loading ? "Analyzing..." : "Analyze with AXIOM"}
            </button>
          </div>

          <textarea
            value={customText}
            onChange={(event) => updateCustomText(event.target.value)}
            spellCheck={false}
          />

          <div className="input-footer">
            <span>Public demo: use synthetic or anonymized data only.</span>
            {active && !customMode && <span>Loaded example: {active.domain} / {active.title}</span>}
          </div>
        </section>

        <section className="understanding-card">
          <div className="understanding-head">
            <span className="section-kicker">2. What AXIOM understood</span>
            <h2>Action summary</h2>
          </div>
          <SummaryChips result={result} />
        </section>

        <section className="trust-card">
          <div className="tabs-head">
            <div>
              <span className="section-kicker">3. Source verification</span>
              <h2>Trust Matrix</h2>
              <p className="trust-caption">
                AXIOM compares what the agent declared with what enterprise sources can prove.
              </p>
            </div>
          </div>

          <TrustMatrix rows={result?.trust_matrix ?? []} />
        </section>

        <DecisionCard result={result} />

        <details className="audit-details">
          <summary>Show audit details</summary>

          <section className="tabs-card">
            <div className="tabs-head">
              <div>
                <span className="section-kicker">Auditability</span>
                <h2>Warrant and ledger trace</h2>
              </div>

              <div className="tabs">
                <button className={tab === "warrant" ? "active" : ""} onClick={() => setTab("warrant")}>Warrant</button>
                <button className={tab === "audit" ? "active" : ""} onClick={() => setTab("audit")}>Audit Trail</button>
              </div>
            </div>

            {tab === "warrant" && (
              <div className="json-grid">
                <JsonBlock value={result?.warrant ?? { status: "not issued" }} />
              </div>
            )}

            {tab === "audit" && (
              <div className="audit-grid">
                <details open>
                  <summary>Canonical Action Envelope</summary>
                  <JsonBlock value={result?.envelope ?? { status: "not built" }} />
                </details>
                <details>
                  <summary>Normalized Draft</summary>
                  <JsonBlock value={result?.normalized_draft ?? { status: "not normalized" }} />
                </details>
                <details>
                  <summary>Sanitized Draft</summary>
                  <JsonBlock value={result?.sanitized_draft ?? { status: "not sanitized" }} />
                </details>
                <details>
                  <summary>Ledger Preview</summary>
                  <JsonBlock value={result?.ledger_preview ?? { status: "not recorded" }} />
                </details>
              </div>
            )}
          </section>
        </details>
      </section>
    </main>
  );
}
