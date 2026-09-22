# RetailPulse AI continuation

Context recovered from the recent task **Build BI Portfolio Project** on 21 September 2026.

## Original project direction

Build a Power BI sales dashboard with an automated insight narrator. Power BI/DAX calculates metrics; Python packages validated aggregates; an LLM explains those aggregates. The intended report has three pages: Executive Overview, Product & Customer Analysis, and Performance Drivers.

The earlier conversation stopped while fixing customer measures. Its next planned work was YoY revenue growth, late-delivery rate, average review score, and narrator-ready exports. The customer issue was resolved in the preceding audit using the existing customer dimension, without duplicating customer IDs into FactSales.

## This continuation

- Added Revenue PY, YoY Revenue Change, and YoY Revenue Growth %.
- Added Delivered Orders, Delivery Eligible Orders, Late Orders, Late Delivery Rate, and Average Delivery Days.
- Added Reviewed Orders and Average Review Score.
- Extended DimDate to complete calendar years and preserved chronological month sorting.
- Added aggregate monthly, category, and state exports, a July 2018 narrator input package, and a grounded narration prompt.

Delivery and review measures explicitly transfer the selected sales order IDs to their auxiliary tables. This preserves date, product, state, and status selections without changing model relationships. Delivery metrics count an order once; review averages first average valid scores per order, then average across orders. No order-item multiplication is introduced.

YoY metrics require a single calendar year in the current selection, compare the selected dates with the preceding year, and return blank without a valid baseline. Use DimDate fields for date slicers. Whole-year comparisons can include incomplete historical years: do not present those as like-for-like complete years. The narrator sample explicitly uses July 2018 versus July 2017.

## Remaining stages

1. Three report-page definitions are built in `powerbi/RetailPulse.pbip`, with 41 native elements and 49 schema-validated files. The user reported completing the requested visual/slicer check. Automated screenshot verification remains unavailable. See `dashboard-pages.md`.
2. Paid AI narration was skipped at the user’s request. The launcher now generates the free offline template without an API key or network request. See `ai-narrator.md`.
3. Review the narrative against the supplied metrics, then finish portfolio screenshots and the project README.

No public publishing or recurring automation was configured.

## Validation results

All 220 source-data comparisons passed: 22 measures across total, 2017, 2018, July 2018, SP, bed_bath_table, delivered, canceled, combined year/state/category, and empty selections. The validator independently recomputes results from the CSV files, including prior-year revenue and order-weighted delivery/review calculations.

July 2018 sample: revenue 895,507.22; YoY revenue growth 79.81%; late-delivery rate 3.38% (208 of 6,156 eligible orders); average delivery 8.89 calendar days; average review score 4.27/5 across 6,228 reviewed orders. These are observed metrics, not causal findings.

Artifacts: `outputs/measure-validation.json`, `outputs/portfolio-kpi-export.json`, `outputs/ai_metrics.json`, `prompts/executive_summary_prompt.txt`, and `powerbi/measures.dax`. The preceding report was backed up as `outputs/frjkt-before-portfolio-kpis.pbix`.
