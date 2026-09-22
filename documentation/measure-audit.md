# Measure audit — 21 September 2026

Reviewed all seven original measures and added five complementary measures. All 12 measures passed 96 independent comparisons with the original CSV data across total, 2017, SP, bed_bath_table, delivered, canceled, combined date/state/category, and empty selections. Verified 112,650 unique order-item keys.

## Corrections

- Customers now counts persistent `customer_unique_id` values for the selected sales items. The previous order-specific ID counted 98,666; the corrected distinct customer count is 95,420.
- AOV and the added ratio measures explicitly return zero for empty selections. Repeat Customer Rate also returns zero when selected customers have no repeat orders.
- Monetary display formats use two decimal places; count formats use thousands separators. The existing dollar symbol is preserved; no currency conversion was performed.
- Month Name now sorts by Month Number.
- Every measure has a description documenting its meaning and filter scope.

## Measures and verified totals

| Measure | Total |
| --- | ---: |
| Revenue | 13,591,643.70 |
| Freight Revenue | 2,251,909.54 |
| Total Order Value | 15,843,553.24 |
| Orders | 98,666 |
| Units Sold | 112,650 |
| Customers | 95,420 |
| AOV | 137.75 |
| AOV Including Freight — added | 160.58 |
| Units per Order — added | 1.14 |
| Revenue per Customer — added | 142.44 |
| Repeat Customers — added | 2,913 |
| Repeat Customer Rate — added | 3.05% |

## Definitions and scope

Revenue and units retain the original all-status sales-item scope, including canceled orders unless filtered. Orders counts orders with items, not every row in the Orders table. AOV excludes freight; AOV Including Freight includes it. Product-filtered order value includes only selected products. Repeat customers means multiple orders within the current selection, not lifetime repeat status. Totals/counts retain BLANK for no rows; ratio measures return zero.

Checks validate calculations and existing filter propagation against current source files. No payment reconciliation, delivery KPI, profit, or time-intelligence measures were introduced. Those require separate definitions. Existing SalesValue and delivery-duration columns are stored as text; the audited measures do not aggregate those columns.

## Files

- `outputs/frjkt-before-measure-audit.pbix`: original report backup.
- `outputs/model-before.json` and `outputs/model-after.json`: model snapshots.
- `powerbi/measures.dax`: final formulas and definitions.
- `outputs/measure-results.json`: model query results.
- `outputs/measure-validation.json`: all 96 source-data comparisons.
- `src/audit_measures.ps1`: query/export script; `-Apply` applies the documented changes to the supplied local model port.
- `src/validate_measures.py`: independent CSV validation.
