"""Validate PBIR schemas and measure bindings. Downloads only Microsoft public schemas."""
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
from jsonschema import Draft7Validator, RefResolver
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'src'/'schemas'/'cache'
CACHE.mkdir(parents=True,exist_ok=True)
def retrieve(url):
    # Microsoft's embedded schema $id uses a dot while its published filename uses a hyphen.
    url=url.replace('/schema.embedded.json','/schema-embedded.json')
    if urlparse(url).hostname != 'developer.microsoft.com': raise ValueError('Unexpected schema host')
    cache=CACHE/urlparse(url).path.lstrip('/')
    if not cache.exists():
        cache.parent.mkdir(parents=True,exist_ok=True)
        cache.write_bytes(urllib.request.urlopen(url,timeout=30).read())
    return json.loads(cache.read_text(encoding='utf-8-sig'))
files=list((ROOT/'powerbi'/'RetailPulse.Report').rglob('*.json'))+[ROOT/'powerbi'/'RetailPulse.Report'/'definition.pbir',ROOT/'powerbi'/'RetailPulse.SemanticModel'/'definition.pbism']
errors=[]
checked=0
for path in files:
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    if '$schema' not in data: continue
    schema=retrieve(data['$schema'])
    validator=Draft7Validator(schema, resolver=RefResolver(base_uri=data['$schema'],referrer=schema,handlers={'https':retrieve}))
    for error in validator.iter_errors(data): errors.append(f'{path.relative_to(ROOT)}: {list(error.path)}: {error.message}')
    checked+=1
def tmdl_name(value):
    value=value.strip()
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value

tables={}
for path in (ROOT/'powerbi'/'RetailPulse.SemanticModel'/'definition'/'tables').glob('*.tmdl'):
    text=path.read_text(encoding='utf-8-sig')
    table_match=re.search(r'^table\s+(.+)$', text, re.MULTILINE)
    if not table_match: continue
    table=tables.setdefault(tmdl_name(table_match.group(1)), {'columns':set(),'measures':set()})
    for match in re.finditer(r'^\s*column\s+(.+?)(?:\s*=.*)?$', text, re.MULTILINE):
        table['columns'].add(tmdl_name(match.group(1)))
    for match in re.finditer(r'^\s*measure\s+(.+?)\s*=', text, re.MULTILINE):
        table['measures'].add(tmdl_name(match.group(1)))
for path in (ROOT/'powerbi'/'RetailPulse.Report').rglob('visual.json'):
    data=json.loads(path.read_text(encoding='utf-8'))
    for role in data['visual'].get('query',{}).get('queryState',{}).values():
        for projection in role['projections']:
            kind,exp=next(iter(projection['field'].items()))
            table=tables[exp['Expression']['SourceRef']['Entity']]
            assert exp['Property'] in table['measures' if kind=='Measure' else 'columns'], projection
    p=data['position']; assert p['x']>=0 and p['y']>=0 and p['x']+p['width']<=1280 and p['y']+p['height']<=800
print(f'{checked} files schema-checked; {len(errors)} errors; all visual bindings and page bounds verified.')
for error in errors: print(error)
(ROOT/'outputs'/'dashboard-validation.json').write_text(json.dumps({'files':checked,'errors':errors},indent=2))
if errors: raise SystemExit(1)
