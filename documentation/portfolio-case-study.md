# RetailPulse — E-commerce Sales Intelligence

## Why I built it

An e-commerce manager should be able to answer a few basic questions quickly: Are sales growing? Which categories and states matter most? Are delivery problems affecting the customer experience? The source data sits at different levels, so answering those questions correctly requires more than placing charts on a page.

I built RetailPulse as a three-page Power BI report that keeps those questions connected and makes the calculation rules clear.

## What the report covers

- **Executive Overview:** revenue, orders, customers, average order value and year-over-year growth, with monthly, state and category breakdowns.
- **Product & Customer Analysis:** category demand, customer trends, repeat purchasing and revenue per customer.
- **Performance Drivers:** revenue changes alongside delivery timeliness, delivery duration and order-weighted review scores.

The final model contains 22 DAX measures. A separate Python workflow recalculates the results from the CSV files and checks them across ten filter scenarios.

## The modeling work that mattered

The original customer field identifies a customer within an order, so I used the persistent customer identifier for customer counts and repeat-purchase measures. Delivery records are counted once per order. Review scores are first averaged within each order, then averaged across orders so an order with several review rows does not carry extra weight.

Delivery and review calculations receive the selected order set from the sales table. This keeps date, product, state and status filters meaningful without introducing duplicate rows into the sales fact.

Year-over-year measures require a single calendar year and return blank when the comparison period is unavailable. Revenue includes merchandise price across all order statuses and excludes freight; it should not be interpreted as profit or net recognized revenue.

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

The figures show what happened in the historical data. They do not prove why revenue changed or whether delivery performance caused a review outcome. The next step is to compare category and state contributions alongside order counts.

## Quality checks

The model passed 220 source-data comparisons. Forty-nine report definition files passed schema validation. Power BI Desktop screenshots confirm that the three pages render with readable titles, KPI cards, slicers, charts, tables and disclosure notes. Scrollbars in the category and state visuals are intentional because the lists are longer than the available space.

The data covers historical orders from 2016–2018, and 2018 is incomplete. Repeat purchasing is measured within the selected period rather than over a customer's lifetime. No currency conversion, margin, profit or churn analysis is claimed.

## Two-minute walkthrough

1. Open `powerbi/RetailPulse.pbip` and select July 2018.
2. Start on Executive Overview and explain revenue, order volume and the prior-year comparison.
3. Open Product & Customer Analysis and compare category demand with customer behavior.
4. Open Performance Drivers and explain the late-delivery denominator and order-weighted review score.
5. Change the state filter to show how the report responds.
6. Finish with the validation evidence and the limits of the historical dataset.

## Dashboard screenshots

The repository contains Power BI Desktop captures using the full 2018 selection, all months and all states:

- [Executive Overview](../screenshots/01-executive-overview.png)
- [Product & Customer Analysis](../screenshots/02-product-customers.png)
- [Performance Drivers](../screenshots/03-performance-drivers.png)

The July 2018 example above is a focused validation scenario and is separate from the filter state shown in these screenshots.
