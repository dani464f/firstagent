from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Optional

from .models import Client, Invoice

DATE_FMT = "%Y-%m-%d"


class CsvStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.invoices_path = data_dir / "invoices.csv"
        self.clients_path = data_dir / "clients.csv"
        self.followups_log_path = data_dir / "followups_log.csv"

    @staticmethod
    def _parse_date(value: str) -> Optional[date]:
        if not value:
            return None
        return datetime.strptime(value, DATE_FMT).date()

    @staticmethod
    def _date_to_str(value: Optional[date]) -> str:
        return value.strftime(DATE_FMT) if value else ""

    def read_invoices(self) -> list[Invoice]:
        invoices: list[Invoice] = []
        with self.invoices_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                invoices.append(
                    Invoice(
                        invoice_id=row["invoice_id"],
                        client_id=row["client_id"],
                        invoice_date=datetime.strptime(row["invoice_date"], DATE_FMT).date(),
                        due_date=datetime.strptime(row["due_date"], DATE_FMT).date(),
                        amount=float(row["amount"]),
                        currency=row["currency"],
                        status=row["status"].strip().lower(),
                        last_payment_date=self._parse_date(row.get("last_payment_date", "")),
                        last_followup_date=self._parse_date(row.get("last_followup_date", "")),
                    )
                )
        return invoices

    def read_clients(self) -> dict[str, Client]:
        clients: dict[str, Client] = {}
        with self.clients_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                client = Client(
                    client_id=row["client_id"],
                    company_name=row["company_name"],
                    contact_name=row["contact_name"],
                    email=row["email"],
                    typical_payment_days=int(row["typical_payment_days"]),
                    late_rate=float(row["late_rate"]),
                    risk_tier=row["risk_tier"].strip().lower(),
                    notes=row.get("notes", ""),
                )
                clients[client.client_id] = client
        return clients

    def read_followups_log(self) -> list[dict[str, str]]:
        if not self.followups_log_path.exists():
            return []
        with self.followups_log_path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def append_followup_log(self, row: dict[str, str]) -> None:
        file_exists = self.followups_log_path.exists()
        with self.followups_log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "invoice_id",
                    "client_id",
                    "followup_type",
                    "channel",
                    "subject",
                    "body",
                    "decision_reason",
                    "hash_id",
                ],
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def update_invoices_last_followup(
        self, updated_rows: Iterable[tuple[str, date]]
    ) -> None:
        updates = {invoice_id: followup_date for invoice_id, followup_date in updated_rows}
        invoices = self.read_invoices()
        for invoice in invoices:
            if invoice.invoice_id in updates:
                invoice.last_followup_date = updates[invoice.invoice_id]

        with self.invoices_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "invoice_id",
                    "client_id",
                    "invoice_date",
                    "due_date",
                    "amount",
                    "currency",
                    "status",
                    "last_payment_date",
                    "last_followup_date",
                ],
            )
            writer.writeheader()
            for inv in invoices:
                writer.writerow(
                    {
                        "invoice_id": inv.invoice_id,
                        "client_id": inv.client_id,
                        "invoice_date": inv.invoice_date.strftime(DATE_FMT),
                        "due_date": inv.due_date.strftime(DATE_FMT),
                        "amount": f"{inv.amount:.2f}",
                        "currency": inv.currency,
                        "status": inv.status,
                        "last_payment_date": self._date_to_str(inv.last_payment_date),
                        "last_followup_date": self._date_to_str(inv.last_followup_date),
                    }
                )
