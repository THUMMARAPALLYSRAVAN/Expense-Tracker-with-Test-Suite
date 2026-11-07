# Bug Report and Fix Log

| ID | Defect / risk | Fix | Regression coverage |
|---|---|---|---|
| BUG-01 | Decimal values could fail with unclear exceptions or accept non-finite values. | Strict Decimal validation and half-up rounding to paise. | Money validation tests. |
| BUG-02 | Monthly summary used naive month boundaries without an explicit timezone policy. | Normalize offset-aware timestamps to Asia/Kolkata wall time and use half-open month intervals. | Timezone and month-boundary tests. |
| BUG-03 | CSV importer accepted only ISO dates and stopped at the first invalid row. | Mixed-format parsing, row-level validation, valid-row commit, and an import report. | Dirty CSV integration tests. |
| BUG-04 | Duplicate detection did not compare amount and category. | Compare all normalized transaction fields. | Duplicate and round-trip tests. |
| BUG-05 | Recurring schedules could be displayed but not actually processed into transactions. | Added explicit, atomic due-expense processing and next-due advancement. | Recurring processing tests. |

## Debugging approach
For each defect, write a failing regression test first, reproduce with a small fixture, inspect values at the service boundary, apply the fix, and rerun the focused test followed by the full suite.
