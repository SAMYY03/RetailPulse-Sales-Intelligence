"""Apply compact card formats to the saved PBIR files without replacing the project."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in (root/'powerbi'/'RetailPulse.Report'/'definition').rglob('visual.json'):
    data=json.loads(p.read_text(encoding='utf-8'))
    if data['visual']['visualType']!='card': continue
    name=data['visual']['query']['queryState']['Values']['projections'][0]['field']['Measure']['Property']
    units=1000000 if name=='Revenue' else 1000 if name in ('Orders','Customers','Repeat Customers') else 1
    props=data['visual']['objects']['labels'][0]['properties']
    props['labelDisplayUnits']={'expr':{'Literal':{'Value':str(units)+'D'}}}
    props['labelPrecision']={'expr':{'Literal':{'Value':str(1 if units>1 or 'Rate' in name or '%' in name or 'Days' in name else 2)+'D'}}}
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
