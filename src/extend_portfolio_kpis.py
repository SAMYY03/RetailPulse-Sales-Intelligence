"""Prepare explicitly scoped growth and customer-experience DAX measures."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
selected = 'KEEPFILTERS(TREATAS(VALUES(FactSales[OrderID]), Orders[order_id]))'
delivered = 'KEEPFILTERS(Orders[order_status] = "delivered")'
valid_delivery = 'FILTER(Orders, NOT ISBLANK(Orders[order_delivered_customer_date]) && NOT ISBLANK(Orders[order_estimated_delivery_date]))'
review_filter = 'KEEPFILTERS(TREATAS(VALUES(FactSales[OrderID]), olist_order_reviews_dataset[order_id])), KEEPFILTERS(olist_order_reviews_dataset[review_score] >= 1), KEEPFILTERS(olist_order_reviews_dataset[review_score] <= 5)'
money = '\\$#,0.00;(\\$#,0.00);\\$0.00'
definitions = [
    ['Revenue PY', 'IF(HASONEVALUE(DimDate[Year]), CALCULATE([Revenue], DATEADD(DimDate[Date], -1, YEAR)))', money, 'Revenue over the selected calendar dates shifted back one year. Blank for selections spanning multiple years or absent prior data. Use DimDate for date slicing.', 'Growth'],
    ['YoY Revenue Change', 'IF(NOT ISBLANK([Revenue]) && NOT ISBLANK([Revenue PY]), [Revenue] - [Revenue PY])', money, 'Selected revenue minus prior-year comparable-date revenue; blank without a comparison.', 'Growth'],
    ['YoY Revenue Growth %', 'DIVIDE([YoY Revenue Change], [Revenue PY])', '0.0%', 'Revenue change divided by prior-year revenue; blank for missing or zero baselines. Incomplete periods must be disclosed.', 'Growth'],
    ['Delivered Orders', f'CALCULATE(COUNTROWS(Orders), {selected}, {delivered})', '#,0', 'Distinct delivered orders with selected sales items, counted once per order.', 'Delivery'],
    ['Delivery Eligible Orders', f'CALCULATE(COUNTROWS(Orders), {selected}, {delivered}, {valid_delivery})', '#,0', 'Delivered orders with both actual and estimated delivery dates, used as the late-rate denominator.', 'Delivery'],
    ['Late Orders', f'CALCULATE(COUNTROWS(Orders), {selected}, {delivered}, FILTER(Orders, NOT ISBLANK(Orders[order_delivered_customer_date]) && NOT ISBLANK(Orders[order_estimated_delivery_date]) && INT(Orders[order_delivered_customer_date]) > INT(Orders[order_estimated_delivery_date])))', '#,0', 'Eligible orders arriving after the estimated calendar date. Same-day arrival is on time.', 'Delivery'],
    ['Late Delivery Rate', 'IF([Delivery Eligible Orders] > 0, DIVIDE(COALESCE([Late Orders], 0), [Delivery Eligible Orders]))', '0.0%', 'Late orders / eligible delivered orders; blank when no eligible deliveries exist.', 'Delivery'],
    ['Average Delivery Days', f'CALCULATE(AVERAGEX(FILTER(Orders, NOT ISBLANK(Orders[order_purchase_timestamp]) && NOT ISBLANK(Orders[order_delivered_customer_date]) && Orders[order_delivered_customer_date] >= Orders[order_purchase_timestamp]), DATEDIFF(Orders[order_purchase_timestamp], Orders[order_delivered_customer_date], DAY)), {selected}, {delivered})', '0.0', 'Mean calendar days from purchase to actual delivery, one observation per delivered order. Missing or negative durations excluded.', 'Delivery'],
    ['Reviewed Orders', f'CALCULATE(DISTINCTCOUNT(olist_order_reviews_dataset[order_id]), {review_filter})', '#,0', 'Selected orders with at least one valid 1–5 review score.', 'Customer Experience'],
    ['Average Review Score', f'CALCULATE(AVERAGEX(VALUES(olist_order_reviews_dataset[order_id]), CALCULATE(AVERAGE(olist_order_reviews_dataset[review_score]))), {review_filter})', '0.00', 'Mean of each selected order’s mean valid review score. Equal weight per order prevents multiple responses or sales items overweighting an order.', 'Customer Experience'],
]
(root / 'powerbi' / 'portfolio-kpis.json').write_text(json.dumps(definitions, indent=2), encoding='utf-8')
