# RetailPulse — E-commerce Sales Intelligence

## Project overview

A three-page Power BI portfolio project that brings sales, customer purchasing and delivery experience into one report. It combines 22 DAX measures with independent Python checks and a free, locally generated summary. No paid API is required.

## Business problem

An e-commerce manager needs to understand how sales are changing, which product categories and states contribute to performance, and whether delivery and review metrics warrant investigation. Order-item data must be aggregated carefully so that customers, deliveries and reviews are not counted multiple times.

## What was built

- **Executive Overview:** revenue, orders, customers, average order value and year-over-year growth, with monthly, state and category breakdowns.
- **Product & Customer Analysis:** category performance, customer trends and repeat purchasing within the selected period.
- **Performance Drivers:** revenue changes alongside delivery timeliness, delivery duration and order-weighted review scores.
- **Validation workflow:** 220 independent comparisons across 22 measures and ten filter selections, including combined filters and an empty selection.
- **Offline summary:** a reproducible template with formatted figures, evidence references and source hashes.

## Important modeling decisions

Customer counts use the persistent customer identifier rather than the order-specific customer identifier. Delivery calculations count each order once. Review scores first average valid reviews for each order, then average those order scores. Selected sales orders filter the delivery and review calculations so category and state selections remain relevant.

Year-over-year measures require a single selected calendar year and return blank when a prior-year baseline is unavailable. Revenue includes all order statuses and excludes freight; it should not be described as profit or net recognized revenue.

## Example findings: July 2018

| Metric | Result |
|---|---:|
| Merchandise revenue, in source monetary units | 895,507.22 |
| Revenue growth versus July 2017 | 79.81% |
| Orders with items | 6,273 |
| Late-delivery rate | 3.38% |
| Late / eligible delivered orders | 208 / 6,156 |
| Average delivery duration | 8.89 calendar days |
| Order-weighted review score | 4.27 / 5 |
| Reviewed orders | 6,228 |

These are historical observations. Revenue growth does not establish its cause, and these results do not demonstrate business impact from using the dashboard. Investigate category and state contributions alongside order counts before proposing explanations.

## Evidence and limitations

The model passed 220 source-data comparisons. Forty-nine report definition files passed schema validation. Screenshots from Power BI Desktop confirm that all three pages render with readable titles, KPI cards, slicers, charts, tables and disclosure notes. Scrollbars shown in the category and state visuals are intentional for exploring the full lists.

The dataset covers historical orders from 2016–2018, with incomplete 2018 coverage. Repeat purchasing is measured within the selection, not over customer lifetime. No currency conversion, margin, profit or churn analysis is claimed. The summary is a template, not AI-generated output. Paid API narration was excluded from the final scope.

## Short portfolio description

Built a three-page Power BI e-commerce dashboard with 22 DAX measures covering sales, customer purchasing and delivery experience. Verified metrics through 220 independent Python comparisons, corrected customer and order-level aggregation, and added a free offline summary with traceable figures.

## Two-minute demonstration

1. Open `powerbi/RetailPulse.pbip` and select July 2018.
2. Start on Executive Overview: explain revenue, orders and the prior-year comparison.
3. Open Product & Customer Analysis: compare categories and explain the repeat-customer definition.
4. Open Performance Drivers: explain late-delivery denominators and order-weighted review scores.
5. Change the state selection and demonstrate how the related metrics respond.
6. Finish with the validation evidence and offline summary. Explain the historical-data limitations.

## Dashboard screenshots

The portfolio includes actual Power BI Desktop captures using the full 2018 selection, all months and all states:

- [Executive Overview](../screenshots/01-executive-overview.png)
- [Product & Customer Analysis](../screenshots/02-product-customers.png)
- [Performance Drivers](../screenshots/03-performance-drivers.png)

The July 2018 findings above are a separate focused validation example and should not be presented as the active filter state in these screenshots.

Before distributing source data, document its original download location and applicable license. Update the Power Query source paths when moving the project to another workstation.
