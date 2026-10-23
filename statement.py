"""Ledger validation and income statement calculations; no HTTP dependencies."""

import json
import re
from datetime import date
from pathlib import Path


MONEY = re.compile(r"\d+\.\d{2}\Z")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
SECTIONS = (
    ("revenue", "Revenue"),
    ("cogs", "Cost of goods sold"),
    ("operating_expenses", "Operating expenses"),
    ("other_income", "Other income"),
)
SUBTYPE_SECTION = {
    "operating_revenue": "revenue",
    "contra_revenue": "revenue",
    "cogs": "cogs",
    "operating_expense": "operating_expenses",
    "other_income": "other_income",
}
SUBTYPE_TYPE = {
    "operating_revenue": "revenue",
    "contra_revenue": "revenue",
    "cogs": "expense",
    "operating_expense": "expense",
    "other_income": "revenue",
}


def parse_date(value):
    if not isinstance(value, str) or not DATE.fullmatch(value):
        raise ValueError("Dates must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid calendar date") from exc


def parse_cents(value):
    if not isinstance(value, str) or not MONEY.fullmatch(value):
        raise ValueError(f"Invalid monetary amount: {value!r}")
    whole, fraction = value.split(".")
    return int(whole) * 100 + int(fraction)


def money(cents):
    sign = "-" if cents < 0 else ""
    magnitude = abs(cents)
    return f"{sign}{magnitude // 100}.{magnitude % 100:02d}"


def load_ledger(path):
    """Load and validate source data once; keep all journal amounts in cents."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw.get("company"), str) or not isinstance(raw.get("currency"), str):
        raise ValueError("Ledger needs a company and currency")
    accounts = {}
    for account in raw["accounts"]:
        number = account["number"]
        if not isinstance(number, str) or number in accounts:
            raise ValueError(f"Duplicate or invalid account number: {number!r}")
        subtype, account_type = account["subtype"], account["type"]
        if subtype == "balance_sheet":
            valid = account_type in {"asset", "liability", "equity"}
        else:
            valid = SUBTYPE_TYPE.get(subtype) == account_type
        if not valid or not isinstance(account["name"], str) or not isinstance(account["is_active"], bool):
            raise ValueError(f"Invalid account: {number}")
        accounts[number] = account

    entries = []
    entry_ids = set()
    for entry in raw["journal_entries"]:
        entry_id = entry["id"]
        if entry_id in entry_ids or entry["status"] not in {"posted", "draft", "void"}:
            raise ValueError(f"Duplicate entry ID or invalid status: {entry_id}")
        entry_ids.add(entry_id)
        entry_date = parse_date(entry["date"])
        lines = []
        if len(entry["lines"]) < 2:
            raise ValueError(f"Entry needs at least two lines: {entry_id}")
        debits = credits = 0
        for line in entry["lines"]:
            number = line["account"]
            if number not in accounts:
                raise ValueError(f"Unknown account {number} in {entry_id}")
            debit, credit = parse_cents(line["debit"]), parse_cents(line["credit"])
            if debit and credit:
                raise ValueError(f"Both debit and credit on a line in {entry_id}")
            debits += debit
            credits += credit
            lines.append((number, debit, credit))
        if debits != credits:
            raise ValueError(f"Unbalanced entry: {entry_id}")
        entries.append({"date": entry_date, "status": entry["status"], "lines": lines})
    return {"company": raw["company"], "currency": raw["currency"], "accounts": accounts, "entries": entries}


def income_statement(ledger, start, end):
    """Return period activity, including zero rows, with signed decimal strings."""
    first, last = parse_date(start), parse_date(end)
    if first > last:
        raise ValueError("Start date must be on or before end date")

    balances = {number: 0 for number, account in ledger["accounts"].items()
                if account["type"] in {"revenue", "expense"}}
    for entry in ledger["entries"]:
        if entry["status"] != "posted" or not first <= entry["date"] <= last:
            continue
        for number, debit, credit in entry["lines"]:
            if number in balances:
                account = ledger["accounts"][number]
                balances[number] += (credit - debit if account["type"] == "revenue" else debit - credit)

    sections = []
    totals = {}
    for key, label in SECTIONS:
        rows = [
            {"number": number, "name": account["name"], "amount": money(balances[number])}
            for number, account in sorted(ledger["accounts"].items())
            if account["subtype"] in SUBTYPE_SECTION and SUBTYPE_SECTION[account["subtype"]] == key
        ]
        subtotal = sum(balances[row["number"]] for row in rows)
        totals[key] = subtotal
        sections.append({"key": key, "label": label, "accounts": rows, "subtotal": money(subtotal)})

    gross_profit = totals["revenue"] - totals["cogs"]
    operating_income = gross_profit - totals["operating_expenses"]
    net_income = operating_income + totals["other_income"]
    return {
        "company": ledger["company"], "currency": ledger["currency"],
        "start": start, "end": end, "sections": sections,
        "gross_profit": money(gross_profit),
        "operating_income": money(operating_income),
        "net_income": money(net_income),
    }
