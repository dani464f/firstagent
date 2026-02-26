from __future__ import annotations

import csv
from pathlib import Path


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    data_dir = Path.cwd() / "data"

    write_csv(
        data_dir / "clients.csv",
        fieldnames=[
            "client_id",
            "company_name",
            "contact_name",
            "email",
            "typical_payment_days",
            "late_rate",
            "risk_tier",
            "notes",
        ],
        rows=[
            {
                "client_id": "C001",
                "company_name": "Northwind Studio",
                "contact_name": "Alice Kim",
                "email": "alice@northwind.example",
                "typical_payment_days": "5",
                "late_rate": "0.1",
                "risk_tier": "low",
                "notes": "Long-term client",
            },
            {
                "client_id": "C002",
                "company_name": "Vertex IT",
                "contact_name": "Bruno Diaz",
                "email": "bruno@vertex.example",
                "typical_payment_days": "15",
                "late_rate": "0.55",
                "risk_tier": "med",
                "notes": "Occasional delays",
            },
            {
                "client_id": "C003",
                "company_name": "Redline Ops",
                "contact_name": "Chloe Patel",
                "email": "chloe@redline.example",
                "typical_payment_days": "22",
                "late_rate": "0.75",
                "risk_tier": "high",
                "notes": "Late fee clause in MSA",
            },
        ],
    )

    write_csv(
        data_dir / "invoices.csv",
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
        rows=[
            {
                "invoice_id": "INV-1001",
                "client_id": "C001",
                "invoice_date": "2026-01-15",
                "due_date": "2026-02-20",
                "amount": "1200.00",
                "currency": "USD",
                "status": "open",
                "last_payment_date": "",
                "last_followup_date": "",
            },
            {
                "invoice_id": "INV-1002",
                "client_id": "C002",
                "invoice_date": "2026-01-10",
                "due_date": "2026-02-12",
                "amount": "2400.00",
                "currency": "USD",
                "status": "open",
                "last_payment_date": "",
                "last_followup_date": "2026-02-24",
            },
            {
                "invoice_id": "INV-1003",
                "client_id": "C003",
                "invoice_date": "2025-12-01",
                "due_date": "2026-01-20",
                "amount": "5100.00",
                "currency": "USD",
                "status": "open",
                "last_payment_date": "",
                "last_followup_date": "",
            },
            {
                "invoice_id": "INV-1004",
                "client_id": "C003",
                "invoice_date": "2026-02-10",
                "due_date": "2026-02-28",
                "amount": "800.00",
                "currency": "USD",
                "status": "open",
                "last_payment_date": "",
                "last_followup_date": "",
            },
            {
                "invoice_id": "INV-1005",
                "client_id": "C001",
                "invoice_date": "2026-01-05",
                "due_date": "2026-02-01",
                "amount": "300.00",
                "currency": "USD",
                "status": "paid",
                "last_payment_date": "2026-02-02",
                "last_followup_date": "",
            },
        ],
    )

    write_csv(
        data_dir / "followups_log.csv",
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
        rows=[],
    )

    print(f"Seeded data files in {data_dir}")


if __name__ == "__main__":
    main()
