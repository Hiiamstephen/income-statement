# Campfire Income Statement — Design and Testing Plan

## Status and scope

Implementation began after the user requested it. The selected stack is Python's standard library, with one HTTP process serving the API and page. The response schema is implemented in `statement.py`; `NOTES.md` records final decisions.

Reference: [Assignment repository](https://github.com/Campfire-eng/income-statement-take-home) and its [accounting primer](https://github.com/Campfire-eng/income-statement-take-home/blob/main/ACCOUNTING_PRIMER.md).

## Assignment context

Build a small full-stack application that produces an income statement (profit and loss report) for Northwind Coffee Roasters over a selected date range. The supplied ledger contains a chart of accounts and journal entries. Each journal entry records a transaction through debit and credit lines; total debits equal total credits.

Required deliverables:

- Backend: `GET /income-statement?start=YYYY-MM-DD&end=YYYY-MM-DD`.
- Frontend: start and end date inputs and a readable statement with account rows and section subtotals.
- Tests covering meaningful accounting behavior.
- `README.md` with run/test commands and language/tool versions.
- `NOTES.md`, at most one page: Q1 net income, assumptions, verification, AI use and a mistake or untrusted output, and next steps.
- Incremental commits and a walkthrough video of at most five minutes.

The assignment allows two hours of implementation; stop at that limit and document unfinished work. The video is outside that limit. A subsequent review and pairing session requires explaining and extending the code without AI. Prioritize exact results and understandable code over styling or extra infrastructure.

## Accounting rules

1. Include only `posted` entries whose accounting date falls within the requested range, including both endpoints.
2. Include only revenue and expense accounts in the statement. Exclude assets, liabilities, and equity.
3. Preserve historical activity on inactive accounts. Inactivity restricts new postings, not historical reporting.
4. Revenue amounts equal credits minus debits. Returns and discounts therefore reduce revenue.
5. Expense amounts equal debits minus credits. Vendor credits therefore reduce expenses.
6. Use account subtype to place rows in Revenue, Cost of goods sold, Operating expenses, or Other income.
7. Report entries as recorded. Do not infer accounting treatment from memo text, reclassify entries, or allocate expenses across periods.

Examples that matter:

- Annual subscription billing affects receivables and deferred revenue; only the recorded recognition entries contribute subscription revenue.
- Collecting a receivable does not create revenue again.
- The January rent entry remains entirely in January, even though its memo mentions three months.
- The legacy marketing account remains in historical results.

Formulas:

```text
Revenue = operating revenue + signed contra revenue
Gross profit = Revenue − Cost of goods sold
Operating income = Gross profit − Operating expenses
Net income = Operating income + Other income
```

## Dates and timestamps

Keep `date` / `accounting_date`, `start`, and `end` as calendar dates in `YYYY-MM-DD` format. The assignment explicitly gives dates without times or timezones. Do not convert them to UTC timestamps or through local timezones.

A future `created_at` field could use a UTC timestamp such as `2026-04-01T02:15:00Z` to record when the system stored an entry. It would serve a different purpose from the accounting date and would not determine report inclusion. The supplied ledger has no timestamps; do not invent them or add this feature to the initial scope.

## Service structure

Use one application with a pure calculation module and an in-memory ledger loaded at startup. A database is unnecessary for this assignment.

```text
Browser: date inputs and statement
                  |
HTTP layer: validate query and return response
                  |
Report function: filter → aggregate accounts → compute totals
                  |
Validated ledger loaded at startup
```

| Component | Responsibility |
| --- | --- |
| Ledger loader | Read JSON; validate amounts, account references, and balanced entries |
| Report function | Filter posted entries by date, aggregate eligible accounts, calculate subtotals and derived totals |
| HTTP endpoint | Validate query parameters; return report or clear errors |
| Frontend | Request the report and display account rows, subtotals, loading states, and errors |
| Tests | Verify accounting rules, reference totals, and the complete request path |

Keep the report function independent of HTTP and frontend concerns. The backend owns all accounting calculations; the frontend formats the returned values.

### Money

- Parse decimal strings directly into integer cents; do not parse through binary floating point.
- Calculate with integer cents and serialize monetary response values as decimal strings with two decimal places.
- If JavaScript/TypeScript is selected, choose an exact integer representation or explicitly enforce safe integer limits.
- Display the currency and format negative values in parentheses.

### API and display behavior

- Return company, currency, requested period, account rows grouped into sections, section subtotals, gross profit, operating income, and net income.
- The implemented JSON schema is documented by the `income_statement` return value in `statement.py` and exercised through the API tests.
- Sort account rows by account number.
- Retain the statement structure and show zero amounts for periods without activity; use a consistent policy of including eligible zero-balance accounts.
- Return `400` for missing dates, invalid calendar dates, or a start date after the end date.
- Fail clearly at startup for invalid source data rather than silently dropping it.
- Avoid authentication, deployment, Docker, additional services, and unrelated features within the initial scope.

### Language and framework

The implementation uses Python's standard library HTTP server and a small browser page. The calculation is a pure function independent of HTTP.

## Q1 2026 acceptance target

Range: `2026-01-01` through `2026-03-31`, inclusive. Currency: USD.

These are independently calculated targets from the supplied ledger, not output from an implemented application.

| Statement line | Amount (USD) |
| --- | ---: |
| Product revenue | 35,650.75 |
| Subscription revenue | 3,000.00 |
| Returns and discounts | (800.25) |
| **Revenue** | **37,850.50** |
| Cost of goods sold | 14,272.75 |
| **Gross profit** | **23,577.75** |
| Salaries | 55,500.00 |
| Rent | 9,000.00 |
| Software | 1,099.97 |
| Marketing (legacy) | 2,500.10 |
| **Operating expenses** | **68,100.07** |
| **Operating income** | **(44,522.32)** |
| Interest income / Other income | 42.18 |
| **Net income** | **(44,480.14)** |

## Testing plan

Establish expected values independently before implementing the report function. Do not generate expected results with the production calculation itself.

| Test | Error it should catch |
| --- | --- |
| Full Q1 account rows, subtotals, and totals | Incorrect aggregation or section assignment |
| Draft and void entries | Inclusion of unapproved or cancelled activity |
| Same-day range and entries on both boundaries | Incorrect inclusive date filtering |
| Entries before and after the range | Accumulating balances instead of period activity |
| Returns and discounts | Incorrect revenue signs, including multi-line sales entries |
| Software vendor credit | Ignoring credits that reduce expenses |
| Inactive marketing account | Excluding historical activity |
| Subscription billing and customer payments | Counting balance-sheet movements as revenue |
| January versus February rent | Inventing allocations absent from the ledger |
| Empty period | Missing structure or incorrect nonzero totals |
| Missing, malformed, impossible, or reversed dates | Incorrect request validation |
| Exact cent amounts | Floating-point drift or incorrect money parsing |
| Invalid account reference or unbalanced source entry | Silently accepting corrupt input |

Additional verification:

- For every account, section subtotal, and derived total, January + February + March must equal Q1.
- A small browser smoke test changes the date range and confirms the rendered statement updates, including negative formatting.
- Verify that timezone handling never shifts an accounting date or changes report membership.

Prioritize focused calculation tests, a small set of API tests, and one browser smoke test. Avoid a large test framework or infrastructure that consumes the implementation budget.

## Implementation

The user authorized implementation after this plan was written. See `statement.py`, `app.py`, `index.html`, `test_statement.py`, and `NOTES.md` for the completed flow and verification.

## Workspace instructions used

Prepared under the workspace `AGENTS.md` and `Tool Convention.md`. This file records the agreed design only; no application code has been created.
