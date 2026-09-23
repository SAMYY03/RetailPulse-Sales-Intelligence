# RetailPulse implementation notes

## Report structure

RetailPulse has three pages: Executive Overview, Product & Customer Analysis, and Performance Drivers. The pages share synchronized year, month and state slicers.

## Measures added

- Revenue PY, YoY Revenue Change and YoY Revenue Growth %
- Delivered Orders, Delivery Eligible Orders, Late Orders, Late Delivery Rate and Average Delivery Days
- Reviewed Orders and Average Review Score
- Customers, Repeat Customers, Repeat Customer Rate and Revenue per Customer

The date table covers complete calendar years and keeps month names in chronological order.

## Calculation rules

Delivery and review measures transfer the selected sales order IDs to their supporting tables. This preserves filters from the sales model while keeping one result per order. Delivery metrics count each order once. Review calculations average valid scores within each order before calculating the overall average.

Year-over-year measures require one selected calendar year, compare the selected dates with the preceding year and return blank when a valid baseline is unavailable. Whole-year comparisons may include incomplete historical years, so they should not automatically be described as like-for-like full-year comparisons.

## Validation results

All 220 source-data comparisons passed for 22 measures. The checks cover totals, 2017, 2018, July 2018, São Paulo, the bed/bath/table category, delivered and canceled orders, combined filters and empty selections.

For the July 2018 validation scenario: revenue was 895,507.22; year-over-year revenue growth was 79.81%; the late-delivery rate was 3.38% (208 of 6,156 eligible orders); average delivery time was 8.89 calendar days; and the average review score was 4.27 out of 5 across 6,228 reviewed orders.

The key artifacts are `outputs/measure-validation.json`, `outputs/portfolio-kpi-export.json` and `powerbi/measures.dax`.

## Generated insight layer

`src/generate_weekly_brief.py` turns seven validated July 2018 measures into a short structured brief. It uses Qwen2.5 through the local Ollama API by default, rejects unsupported numeric claims and records the source context for every displayed value. `outputs/weekly_sales_brief.sample.md` demonstrates the checked rendering path without invoking a model.
