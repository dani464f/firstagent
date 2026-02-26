from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .config_loader import load_config
from .crew_workflow import (
    build_hash_id,
    run_message_crew,
    send_console_email,
    utc_timestamp,
)
from .data_access import CsvStore
from .logic import build_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run invoice follow-up daily job")
    parser.add_argument("--today", required=False, help="Override date in YYYY-MM-DD")
    parser.add_argument("--data-dir", default="data", help="CSV data directory")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use deterministic template composer instead of CrewAI LLM generation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd()
    config_path = root / "config.yaml"
    config = load_config(config_path)

    today = (
        datetime.strptime(args.today, "%Y-%m-%d").date()
        if args.today
        else datetime.now().date()
    )

    store = CsvStore(root / args.data_dir)
    invoices = store.read_invoices()
    clients = store.read_clients()
    logs = store.read_followups_log()

    candidates, skipped = build_candidates(
        invoices=invoices,
        clients=clients,
        logs=logs,
        today=today,
        pre_due_window_days=config["pre_due_window_days"],
        cooldown_days=config["cooldown_days"],
    )

    sent_updates: list[tuple[str, date]] = []
    messages_sent = 0

    for candidate in candidates:
        message = run_message_crew(
            candidate=candidate,
            config=config,
            use_llm=not args.no_llm,
        )

        send_console_email(
            to_email=candidate.client.email,
            subject=message.subject,
            body=message.body,
            sender_name=config["sender_name"],
            sender_email=config["sender_email"],
        )

        store.append_followup_log(
            {
                "timestamp": utc_timestamp(),
                "invoice_id": candidate.invoice.invoice_id,
                "client_id": candidate.client.client_id,
                "followup_type": candidate.followup_type,
                "channel": "console",
                "subject": message.subject,
                "body": message.body,
                "decision_reason": candidate.decision_reason,
                "hash_id": build_hash_id(
                    candidate.invoice.invoice_id, candidate.followup_type, message
                ),
            }
        )
        sent_updates.append((candidate.invoice.invoice_id, today))
        messages_sent += 1

    if sent_updates:
        store.update_invoices_last_followup(sent_updates)

    print("\nDAILY SUMMARY")
    print(f"Today: {today.isoformat()}")
    print(f"Invoices scanned: {len(invoices)}")
    print(f"Candidates found: {len(candidates)}")
    print(f"Messages sent: {messages_sent}")
    print(f"Skipped: {len(skipped)}")
    if skipped:
        print("Skip details:")
        for item in skipped:
            print(f"- {item}")


if __name__ == "__main__":
    main()
