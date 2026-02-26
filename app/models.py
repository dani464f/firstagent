from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Invoice:
    invoice_id: str
    client_id: str
    invoice_date: date
    due_date: date
    amount: float
    currency: str
    status: str
    last_payment_date: Optional[date]
    last_followup_date: Optional[date]


@dataclass
class Client:
    client_id: str
    company_name: str
    contact_name: str
    email: str
    typical_payment_days: int
    late_rate: float
    risk_tier: str
    notes: str = ""


@dataclass
class Candidate:
    invoice: Invoice
    client: Client
    followup_type: str
    decision_reason: str


@dataclass
class MessageDraft:
    subject: str
    body: str


@dataclass
class DecisionSummary:
    scanned: int = 0
    candidates: int = 0
    sent: int = 0
    skipped: int = 0
