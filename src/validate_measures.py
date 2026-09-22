"""Independently reconcile DAX results against the source CSV files."""
import csv
import json
import math
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT / 'data' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

orders = {r['order_id']: r for r in read('olist_orders_dataset.csv')}
customers = {r['customer_id']: r for r in read('olist_customers_dataset.csv')}
products = {r['product_id']: r for r in read('olist_products_dataset.csv')}
translations = {r['product_category_name']: r['product_category_name_english'] for r in read('product_category_name_translation.csv')}
items = read('olist_order_items_dataset.csv')
reviews = defaultdict(list)
for review in read('olist_order_reviews_dataset.csv'):
    score = int(review['review_score'])
    if 1 <= score <= 5:
        reviews[review['order_id']].append(score)
assert len({(r['order_id'], r['order_item_id']) for r in items}) == len(items), 'Duplicate sales-item keys'
actual = json.loads((ROOT / 'outputs' / 'measure-results.json').read_text(encoding='utf-8-sig'))
checks = []
for context, result in actual.items():
    selected = []
    for item in items:
        order = orders[item['order_id']]
        customer = customers[order['customer_id']]
        category = translations.get(products[item['product_id']]['product_category_name'])
        year = order['order_purchase_timestamp'][:4]
        if context in ('year2017', 'combined') and year != '2017': continue
        if context == 'year2018' and year != '2018': continue
        if context == 'month201807' and order['order_purchase_timestamp'][:7] != '2018-07': continue
        if context in ('stateSP', 'combined') and customer['customer_state'] != 'SP': continue
        if context in ('category', 'combined') and category != 'bed_bath_table': continue
        if context in ('delivered', 'canceled') and order['order_status'] != context: continue
        if context == 'empty': continue
        selected.append((item, customer))
    revenue = sum((Decimal(i['price']) for i, _ in selected), Decimal(0))
    freight = sum((Decimal(i['freight_value']) for i, _ in selected), Decimal(0))
    order_ids = {i['order_id'] for i, _ in selected}
    person_orders = defaultdict(set)
    for i, c in selected:
        assert c['customer_unique_id'], 'Missing persistent customer identifier'
        person_orders[c['customer_unique_id']].add(i['order_id'])
    norders, ncustomers = len(order_ids), len(person_orders)
    repeats = sum(len(ids) > 1 for ids in person_orders.values())
    expected = {
        'Revenue': float(revenue) if selected else None,
        'Freight Revenue': float(freight) if selected else None,
        'Total Order Value': float(revenue + freight) if selected else None,
        'Orders': norders or None,
        'Units Sold': len(selected) or None,
        'Customers': ncustomers or None,
        'AOV': float(revenue / norders) if norders else 0,
        'AOV Including Freight': float((revenue + freight) / norders) if norders else 0,
        'Units per Order': len(selected) / norders if norders else 0,
        'Revenue per Customer': float(revenue / ncustomers) if ncustomers else 0,
        'Repeat Customers': repeats or None,
        'Repeat Customer Rate': repeats / ncustomers if ncustomers else 0,
    }
    if '[Revenue PY]' in result:
        prior = []
        for item in items:
            order = orders[item['order_id']]
            customer = customers[order['customer_id']]
            category = translations.get(products[item['product_id']]['product_category_name'])
            if context in ('year2017', 'combined'):
                if order['order_purchase_timestamp'][:4] != '2016': continue
            elif context == 'year2018':
                if order['order_purchase_timestamp'][:4] != '2017': continue
            elif context == 'month201807':
                if order['order_purchase_timestamp'][:7] != '2017-07': continue
            else: continue
            if context == 'combined' and (customer['customer_state'] != 'SP' or category != 'bed_bath_table'): continue
            prior.append(Decimal(item['price']))
        prior_revenue = float(sum(prior)) if prior else None
        change = float(revenue) - prior_revenue if selected and prior_revenue is not None else None
        delivered_orders = [orders[oid] for oid in order_ids if orders[oid]['order_status'] == 'delivered']
        eligible = [o for o in delivered_orders if o['order_delivered_customer_date'] and o['order_estimated_delivery_date']]
        late = sum(o['order_delivered_customer_date'][:10] > o['order_estimated_delivery_date'][:10] for o in eligible)
        durations = [(datetime.fromisoformat(o['order_delivered_customer_date']).date() - datetime.fromisoformat(o['order_purchase_timestamp']).date()).days for o in delivered_orders if o['order_delivered_customer_date'] and o['order_purchase_timestamp'] and o['order_delivered_customer_date'] >= o['order_purchase_timestamp']]
        order_scores = [sum(reviews[oid]) / len(reviews[oid]) for oid in order_ids if reviews[oid]]
        expected.update({
            'Revenue PY': prior_revenue,
            'YoY Revenue Change': change,
            'YoY Revenue Growth %': change / prior_revenue if change is not None and prior_revenue else None,
            'Delivered Orders': len(delivered_orders) or None,
            'Delivery Eligible Orders': len(eligible) or None,
            'Late Orders': late or None,
            'Late Delivery Rate': late / len(eligible) if eligible else None,
            'Average Delivery Days': sum(durations) / len(durations) if durations else None,
            'Reviewed Orders': len(order_scores) or None,
            'Average Review Score': sum(order_scores) / len(order_scores) if order_scores else None,
        })
    for name, value in expected.items():
        observed = result[f'[{name}]']
        passed = observed is None if value is None else observed is not None and math.isclose(value, observed, rel_tol=1e-10, abs_tol=1e-6)
        checks.append({'context': context, 'measure': name, 'expected': value, 'actual': observed, 'passed': passed})
failures = [c for c in checks if not c['passed']]
(ROOT / 'outputs' / 'measure-validation.json').write_text(json.dumps({'checks': len(checks), 'failures': failures, 'results': checks}, indent=2))
print(f'{len(checks)-len(failures)}/{len(checks)} checks passed; {len(items):,} unique sales-item rows verified.')
if failures:
    print(json.dumps(failures, indent=2))
    raise SystemExit(1)
