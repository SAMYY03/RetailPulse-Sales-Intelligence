# RetailPulse — Sales Intelligence

RetailPulse is a three-page Power BI portfolio project built around a practical e-commerce question: **what is driving sales performance, and where should a manager look next?**

The report brings revenue, orders, customers, product demand, delivery performance and review scores into one place. I also built an independent Python validation workflow so the headline figures can be checked against the source CSV files.

## Dashboard pages

- **Executive Overview** — revenue, orders, customers, average order value and year-over-year growth, with monthly, state and category views.
- **Product & Customer Analysis** — category demand, customer trends, repeat purchasing and revenue per customer.
- **Performance Drivers** — revenue changes by state and category, late deliveries, delivery duration and review scores.

### Executive Overview

![Executive Overview](screenshots/01-executive-overview.png)

### Product & Customer Analysis

![Product and Customer Analysis](screenshots/02-product-customers.png)

### Performance Drivers

![Performance Drivers](screenshots/03-performance-drivers.png)

## A few findings

For July 2018, compared with July 2017:

- Merchandise revenue reached **895,507.22**, up **79.81%** year over year.
- The dataset contains **6,273** orders with items for the month.
- **208 of 6,156** eligible delivered orders were late, a **3.38%** late-delivery rate.
- The average delivery time was **8.89 days**.
- The order-weighted review score was **4.27 out of 5** across **6,228** reviewed orders.

These are historical observations, not causal conclusions. The dashboard is designed to help narrow the next investigation by category, state and order volume.

## Modeling choices

- Customer counts use the persistent customer identifier rather than the order-specific identifier.
- Delivery measures count each order once.
- Review scores are averaged per order before the overall average is calculated.
- Year-over-year measures require one selected calendar year and return blank when no valid prior-year baseline exists.
- Revenue includes merchandise prices across all order statuses and excludes freight. It is not profit or net recognized revenue.
- The 2018 data is incomplete, which is disclosed in the report.

## Validation

- **22 DAX measures** checked independently against the source data.
- **220 comparisons passed** across totals, years, months, states, categories, statuses, combined filters and empty selections.
- **49 Power BI definition files** passed schema validation.
- All three pages were reviewed from Power BI Desktop screenshots.

## Open the project

1. Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2. Place the CSV files in the `data` folder. See [data setup](data/README.md) for the expected filenames.
3. Update the Power Query source paths for your computer.
4. Open `powerbi/RetailPulse.pbip` in Power BI Desktop and keep the sibling report and semantic-model folders together.

Raw CSV files, local model caches and backup files are excluded from this repository.

## Repository guide

- [Portfolio case study](documentation/portfolio-case-study.md)
- [Dashboard pages and interpretation notes](documentation/dashboard-pages.md)
- [Measure audit](documentation/measure-audit.md)
- [Implementation notes and KPI definitions](documentation/project-continuation.md)
- [DAX measures](powerbi/measures.dax)
- [Independent validation results](outputs/measure-validation.json)

## Tools used

Power BI Desktop, Power Query, DAX and Python.
