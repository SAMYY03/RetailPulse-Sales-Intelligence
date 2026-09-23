# RetailPulse dashboard pages

Open `powerbi/RetailPulse.pbip` in Power BI Desktop. Keep its sibling `.Report` and `.SemanticModel` folders together. The original `frjkt.pbix` remains the earlier KPI-only report.

## Executive Overview

Revenue, Orders, Customers, AOV and YoY Revenue Growth cards; monthly revenue versus prior-year revenue; state contribution; category revenue; monthly order volume.

## Product & Customer Analysis

Customer count, repeat customer count/rate and revenue per customer; category unit demand; a category performance table; monthly customer trend. Repeat purchase is evaluated within the selected period, not over customer lifetime.

## Performance Drivers

YoY growth, late-delivery rate, average delivery days and average review score; revenue changes by state/category; a category-level customer-experience table with denominator counts.

## Interaction and interpretation

- Year, month and state slicers are configured consistently on all pages, with sync groups.
- The initial year selection is 2018. This dataset contains an incomplete 2018, and the page footer discloses this. Use July 2018 for a focused year-over-year walkthrough.
- Clearing year filters can make YoY measures blank intentionally; they require a single calendar year selection.
- Category charts expose the full list via scrolling. Tables support sorting and selecting categories.
- Revenue includes all order statuses and excludes freight. It is not net recognized revenue.
- Currency formatting retains the original dollar symbol; no conversion was performed.

## Verification

The report definition comprises three pages and 41 native elements, including text and slicers. Microsoft public JSON schemas validate 49 files with no errors. All measure/column bindings and page bounds are checked. The refreshed model passed all 220 independent CSV-based KPI comparisons.

The user supplied Power BI Desktop screenshots for all three pages on 22 September 2026. They confirm that titles, KPI cards, slicers, charts, tables and disclosure notes render at readable sizes without visible overlap. The category and state visuals intentionally use scrollbars. The screenshots show the full 2018 selection with all months and all states; interactive slicer behavior was checked separately by the user.

The captures are saved under `screenshots/` as `01-executive-overview.png`, `02-product-customers.png` and `03-performance-drivers.png`.

## Rebuild

Close the dashboard project before rebuilding; Power BI can overwrite external changes when saving. Run `python src/build_dashboard.py`, followed by `python src/validate_dashboard.py`. The latter requires `jsonschema` (installed locally under `src/vendor` for this session), and fetches uncached Microsoft public schema documents.

The project uses the documented [PBIR report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) and [semantic-model project structure](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).
