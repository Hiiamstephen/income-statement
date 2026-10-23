# Implementation notes

For **2026-01-01 through 2026-03-31**, the app reports **net income of (USD 44,480.14)**. Revenue is 37,850.50; cost of goods sold is 14,272.75; gross profit is 23,577.75; operating expenses are 68,100.07; operating income is (44,522.32); and other income is 42.18.

The range includes both dates. Only posted entries count. I kept all eligible account rows, including zero balances, sorted by account number. An inactive account remains in historical reports. Revenue is credits less debits; expenses are debits less credits. Contra revenue thus appears negative, as does an expense credit. Assets, liabilities, and equity are excluded. The annual subscription bill and receivable collection have no income-statement effect; only the three posted recognition entries contribute subscription revenue. I reported January rent in January as recorded, without allocating it across months. Dates are calendar dates, without timezone conversion. Every amount is parsed directly into integer cents and returned as a two-decimal string.

I checked Q1 account rows and totals against independently written targets from the supplied entries. Tests also cover void/draft exclusion, date endpoints, out-of-period entries, the inactive marketing account, returns and discounts, the software vendor credit, empty periods, invalid requests, corrupt ledger entries, and the complete HTTP path. A separate test checks that `ledger.json` exactly matches the JSON in the assignment. Monthly amounts reconcile to Q1 for each account and derived total.

I also opened the page in Chrome, confirmed the Q1 amounts and parentheses for losses, then changed the dates and saw the empty-period zero rows. The page script passed a syntax check.

AI helped draft the service, page, and tests. I did not trust its first browser form lookup (`form.start`, with no named input); I changed it to explicit input selectors. I also corrected an empty-period test assertion that tried to index an amount string as a row. These mistakes were caught during review and test execution, rather than taken as evidence that the accounting was right.

With more time, I would add comparative periods and traceable drill-down from each account row to the contributing journal lines. The core calculation is separate from HTTP to keep those extensions small.
