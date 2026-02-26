from __future__ import annotations

from datetime import date

from .models import Candidate, Client, Invoice


def determine_followup_type(
    invoice: Invoice,
    client: Client,
    today: date,
    pre_due_window_days: int,
) -> tuple[str | None, str]:
    if invoice.status == "paid":
        return None, "Invoice already paid"

    days_overdue = (today - invoice.due_date).days
    days_to_due = (invoice.due_date - today).days

    if days_overdue >= 30:
        return "overdue_30", f"Invoice overdue by {days_overdue} days"
    if 14 <= days_overdue < 30:
        return "overdue_14", f"Invoice overdue by {days_overdue} days"
    if 3 <= days_overdue < 14:
        return "overdue_3", f"Invoice overdue by {days_overdue} days"

    consistently_late = client.late_rate >= 0.6 or client.typical_payment_days > 10
    if 0 <= days_to_due <= pre_due_window_days and consistently_late:
        return (
            "pre_due",
            f"Due in {days_to_due} days; client flagged consistently late",
        )

    return None, "No follow-up trigger today"


def cooldown_blocks(invoice: Invoice, today: date, cooldown_days: int) -> bool:
    if not invoice.last_followup_date:
        return False
    return (today - invoice.last_followup_date).days < cooldown_days


def already_sent_type(
    invoice_id: str, followup_type: str, logs: list[dict[str, str]]
) -> bool:
    return any(
        row["invoice_id"] == invoice_id and row["followup_type"] == followup_type for row in logs
    )


def build_candidates(
    invoices: list[Invoice],
    clients: dict[str, Client],
    logs: list[dict[str, str]],
    today: date,
    pre_due_window_days: int,
    cooldown_days: int,
) -> tuple[list[Candidate], list[str]]:
    candidates: list[Candidate] = []
    skipped_reasons: list[str] = []

    for invoice in invoices:
        client = clients.get(invoice.client_id)
        if not client:
            skipped_reasons.append(
                f"{invoice.invoice_id}: missing client {invoice.client_id}"
            )
            continue

        followup_type, reason = determine_followup_type(
            invoice=invoice,
            client=client,
            today=today,
            pre_due_window_days=pre_due_window_days,
        )

        if not followup_type:
            skipped_reasons.append(f"{invoice.invoice_id}: {reason}")
            continue

        if cooldown_blocks(invoice, today, cooldown_days):
            skipped_reasons.append(
                f"{invoice.invoice_id}: cooldown active (last_followup_date={invoice.last_followup_date})"
            )
            continue

        if already_sent_type(invoice.invoice_id, followup_type, logs):
            skipped_reasons.append(
                f"{invoice.invoice_id}: {followup_type} already sent previously"
            )
            continue

        candidates.append(
            Candidate(
                invoice=invoice,
                client=client,
                followup_type=followup_type,
                decision_reason=reason,
            )
        )

    return candidates, skipped_reasons
