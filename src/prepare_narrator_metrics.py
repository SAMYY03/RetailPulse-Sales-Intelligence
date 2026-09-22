"""Package Power BI KPI exports for a narrator without exposing customer records."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((root / 'outputs' / name).read_text(encoding='utf-8-sig'))

validation = load('measure-validation.json')
if validation['failures'] or validation['checks'] < 220:
    raise SystemExit('Run the full KPI validation successfully before preparing narrator inputs.')
export = load('portfolio-kpi-export.json')
period = '2018-07'
monthly = [r for r in export['monthly'] if r['[Revenue]'] is not None]
current = next(r for r in monthly if r['DimDate[Year Month]'] == period)
def clean(row):
    return {k.strip('[]'): v for k, v in row.items() if k.startswith('[')}
def drivers(rows, dimension):
    rows = [r for r in rows if r.get('[Revenue]') is not None]
    ordered = sorted(rows, key=lambda r: r.get('[YoY Revenue Change]') or 0)
    return {
        'largest_revenue': [{'name': r[dimension] or 'Unclassified', **clean(r)} for r in sorted(rows, key=lambda r: r['[Revenue]'], reverse=True)[:5]],
        'largest_increases': [{'name': r[dimension] or 'Unclassified', **clean(r)} for r in reversed(ordered) if (r.get('[YoY Revenue Change]') or 0) > 0][:3],
        'largest_decreases': [{'name': r[dimension] or 'Unclassified', **clean(r)} for r in ordered if (r.get('[YoY Revenue Change]') or 0) < 0][:3],
    }
payload = {
    'project': 'RetailPulse AI',
    'period': period,
    'comparison_period': '2017-07',
    'source': 'Live Power BI DAX export from frjkt.pbix, reconciled against local Olist CSVs',
    'validation': {'checks_passed': validation['checks'], 'failures': 0, 'scope': '22 measures across 10 test selections; not every exported subgroup individually reconciled'},
    'definitions': {
        'Revenue': 'Merchandise value excluding freight, all order statuses; not recognized net revenue.',
        'Orders': 'Orders containing sales items.',
        'Repeat Customer Rate': 'Multiple orders within this selection, not lifetime retention.',
        'Late Delivery Rate': 'Late calendar-date deliveries / delivered orders with actual and estimated dates.',
        'Average Review Score': 'Equal-weight average of per-order mean valid review scores.',
        'rates': 'Rates are fractions: 0.05 means 5%.',
    },
    'limitations': [
        'Historical demonstration period, not current business performance.',
        'July 2018 is an explicit sample month; it is not an automatically inferred latest complete period.',
        'Missing comparisons remain null; never interpret null as zero growth.',
        'No costs, margins, refunds or causal explanations are established by these metrics.',
        'The report retains its original dollar-symbol formatting; currency conversion is not performed.',
    ],
    'kpis': clean(current),
    'category_drivers': drivers(export['categories'], 'DimProdut[category]'),
    'state_drivers': drivers(export['states'], 'DimCustomer[State]'),
}
(root / 'outputs' / 'ai_metrics.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
print(json.dumps({'period': period, 'kpis': payload['kpis']}, indent=2))
