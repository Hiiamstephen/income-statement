# Five-minute walkthrough outline

Record a screen share while running `python3 app.py`. Keep it under five minutes and share the resulting video link with the submission.

1. **Demo (about one minute):** Open <http://127.0.0.1:8000/>, show Q1 net income of (USD 44,480.14), then change the range to 2026-03-20 through 2026-03-20. The software expense should show (USD 100.00) and net income USD 100.00. Show a date with no activity, where all rows remain at zero.
2. **Code path (about two minutes):** Point to `index.html` for the date request and rendering, `app.py` for route validation and JSON response, and `statement.py` for inclusive posted-entry filtering, signed account amounts, and subtotals. Show `ledger.json` loaded and validated at startup.
3. **How you work (about one minute):** Show the editor and terminal, run `python3 -m unittest -v`, and explain one independently checked target. Mention how AI helped draft code and tests, and the browser field lookup that you caught and corrected.
4. **Tradeoffs (remaining time):** Explain the integer-cent representation, why January rent stays in January, why inactive marketing remains, and where you would add journal-line drill-down.
