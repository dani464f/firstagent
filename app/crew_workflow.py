from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

from crewai import Agent, Crew, Task, Process

from .models import Candidate, MessageDraft


def tone_rule(client_risk_tier: str, late_rate: float, followup_type: str) -> str:
    if followup_type == "overdue_30":
        return "firmest"
    if client_risk_tier == "low" and late_rate < 0.3:
        return "friendly"
    if client_risk_tier == "high" or late_rate > 0.6:
        return "firm"
    return "direct_polite"


def default_message(candidate: Candidate, config: dict[str, Any]) -> MessageDraft:
    payment_link = config["payment_link_template"].format(
        invoice_id=candidate.invoice.invoice_id
    )
    tone = tone_rule(
        client_risk_tier=candidate.client.risk_tier,
        late_rate=candidate.client.late_rate,
        followup_type=candidate.followup_type,
    )

    subject_map = {
        "pre_due": f"Upcoming invoice due soon ({candidate.invoice.invoice_id})",
        "overdue_3": f"Friendly reminder: invoice {candidate.invoice.invoice_id}",
        "overdue_14": f"Payment reminder: invoice {candidate.invoice.invoice_id} is overdue",
        "overdue_30": f"Final notice: invoice {candidate.invoice.invoice_id}",
    }

    body = (
        f"Hello {candidate.client.contact_name},\n\n"
        f"This is a {tone.replace('_', ' ')} {candidate.followup_type.replace('_', ' ')} regarding invoice "
        f"{candidate.invoice.invoice_id} for {candidate.invoice.currency} {candidate.invoice.amount:.2f}. "
        f"The due date is {candidate.invoice.due_date.isoformat()}.\n"
        f"Please submit payment using: {payment_link}\n"
    )

    if tone == "firm" and config.get("enable_late_fee_clause", False):
        body += "Per our agreement, late fee terms may apply.\n"

    if candidate.followup_type == "overdue_30" and config.get(
        "enable_pause_service_language", False
    ):
        body += "If unresolved, services may be paused according to contract terms.\n"

    body += "\nIf payment has already been made, please reply with confirmation.\n\nThank you."
    return MessageDraft(subject=subject_map[candidate.followup_type], body=body)


def run_message_crew(
    candidate: Candidate,
    config: dict[str, Any],
    use_llm: bool = True,
) -> MessageDraft:
    if not use_llm:
        return default_message(candidate, config)

    monitor_agent = Agent(
        role="Invoice Monitor Agent",
        goal="Provide deterministic follow-up context and business-rule decision reason",
        backstory="Rules-first collections analyst who never improvises escalation logic.",
        allow_delegation=False,
        verbose=False,
    )

    composer_agent = Agent(
        role="Message Composer Agent",
        goal="Create professional follow-up copy using strict tone rules",
        backstory="AR communication specialist balancing clarity and customer relationships.",
        allow_delegation=False,
        verbose=False,
    )

    qa_agent = Agent(
        role="Compliance QA Agent",
        goal="Ensure message includes required fields and avoids aggressive language",
        backstory="Compliance reviewer ensuring professionalism and legal-safe wording.",
        allow_delegation=False,
        verbose=False,
    )

    payment_link = config["payment_link_template"].format(invoice_id=candidate.invoice.invoice_id)
    tone = tone_rule(candidate.client.risk_tier, candidate.client.late_rate, candidate.followup_type)

    context_json = json.dumps(
        {
            "invoice_id": candidate.invoice.invoice_id,
            "followup_type": candidate.followup_type,
            "decision_reason": candidate.decision_reason,
            "company_name": candidate.client.company_name,
            "contact_name": candidate.client.contact_name,
            "email": candidate.client.email,
            "amount": candidate.invoice.amount,
            "currency": candidate.invoice.currency,
            "due_date": candidate.invoice.due_date.isoformat(),
            "tone_rule": tone,
            "payment_instructions": payment_link,
            "enable_late_fee_clause": config.get("enable_late_fee_clause", False),
            "enable_pause_service_language": config.get("enable_pause_service_language", False),
        }
    )

    monitor_task = Task(
        description=(
            "Confirm and restate follow-up facts only from this JSON context without changing escalation: "
            f"{context_json}."
        ),
        expected_output="A concise bullet list with immutable facts and required inclusions.",
        agent=monitor_agent,
    )

    compose_task = Task(
        description=(
            "Draft a subject and body for the follow-up using this exact format:\n"
            "SUBJECT: <subject>\nBODY:\n<body>\n"
            "Rules: include invoice id, amount+currency, due date, payment instructions; obey tone_rule; no threats."
        ),
        expected_output="Strictly formatted subject/body draft.",
        agent=composer_agent,
        context=[monitor_task],
    )

    qa_task = Task(
        description=(
            "Review the draft. If compliant, return same format SUBJECT/BODY. "
            "If not compliant, revise minimally and return compliant SUBJECT/BODY."
        ),
        expected_output="Compliant final SUBJECT/BODY block.",
        agent=qa_agent,
        context=[compose_task],
    )

    try:
        crew = Crew(
            agents=[monitor_agent, composer_agent, qa_agent],
            tasks=[monitor_task, compose_task, qa_task],
            process=Process.sequential,
            verbose=False,
        )
        output = str(crew.kickoff())
        subject = ""
        body_lines: list[str] = []
        in_body = False
        for line in output.splitlines():
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
                continue
            if line.startswith("BODY:"):
                in_body = True
                continue
            if in_body:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if not subject or not body:
            return default_message(candidate, config)
        return MessageDraft(subject=subject, body=body)
    except Exception:
        return default_message(candidate, config)


def build_hash_id(invoice_id: str, followup_type: str, message: MessageDraft) -> str:
    base = f"{invoice_id}|{followup_type}|{message.subject}|{message.body}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def utc_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def send_console_email(to_email: str, subject: str, body: str, sender_name: str, sender_email: str) -> None:
    print("=" * 70)
    print(f"From: {sender_name} <{sender_email}>")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("-" * 70)
    print(body)
    print("=" * 70)
