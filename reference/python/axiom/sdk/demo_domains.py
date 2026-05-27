from __future__ import annotations

from typing import Literal

from .models import AxiomStrictModel, RawEnterpriseContext


class DemoDomainScenario(AxiomStrictModel):
    id: str
    domain: str
    title: str
    severity: Literal["success", "warning", "danger"]
    expected_decision: str
    description: str
    raw_text: str
    safety_warning: str = "Public demo environment: do not paste secrets, credentials, API keys, customer data, or confidential production logs."


DEMO_DOMAIN_SCENARIOS: dict[str, DemoDomainScenario] = {
    "devops_deploy": DemoDomainScenario(
        id="devops_deploy",
        domain="DevOps",
        title="Deploy payment-api to production",
        severity="success",
        expected_decision="ALLOW",
        description="All operational proofs are declared and source-verified.",
        raw_text=(
            "agent_ops_01 says CHG-1001 is approved. "
            "PR #42 has required review. CI passed. "
            "Security scan is clean. Rollback plan is available. "
            "Deploy payment-api to production."
        ),
    ),
    "finance_wire_transfer": DemoDomainScenario(
        id="finance_wire_transfer",
        domain="Finance",
        title="Execute €48,000 wire transfer",
        severity="warning",
        expected_decision="SUSPEND",
        description="The agent declares payment readiness, but risk evidence triggers suspension.",
        raw_text=(
            "agent_finance_01 says invoice INV-2042 is approved. "
            "Beneficiary ACME is verified. Fraud score is clean. "
            "Execute €48,000 wire transfer now."
        ),
    ),
    "cyber_isolate_endpoint": DemoDomainScenario(
        id="cyber_isolate_endpoint",
        domain="Cyber",
        title="Isolate endpoint FIN-042",
        severity="warning",
        expected_decision="ESCALATE",
        description="EDR alert is confirmed, but asset criticality and missing fallback require escalation.",
        raw_text=(
            "sec_agent_bot says EDR critical alert confirmed: ransomware behavior detected. "
            "Isolate endpoint FIN-042. Asset belongs to CFO VIP machine."
        ),
    ),
    "support_refund": DemoDomainScenario(
        id="support_refund",
        domain="Support",
        title="Approve €850 customer refund",
        severity="danger",
        expected_decision="DENY",
        description="Refund exceeds autonomous threshold and requires manager approval.",
        raw_text=(
            "support_agent_ai says customer refund requested for €850. "
            "Customer is eligible. Approve refund now."
        ),
    ),
}


def list_domain_scenarios() -> list[dict]:
    return [scenario.model_dump(mode="json") for scenario in DEMO_DOMAIN_SCENARIOS.values()]


def get_domain_context(scenario_id: str) -> RawEnterpriseContext:
    scenario = DEMO_DOMAIN_SCENARIOS[scenario_id]
    return RawEnterpriseContext(
        input_mode="paste_context",
        raw_text=scenario.raw_text,
        metadata={
            "scenario_id": scenario.id,
            "domain": scenario.domain,
            "title": scenario.title,
        },
    )
