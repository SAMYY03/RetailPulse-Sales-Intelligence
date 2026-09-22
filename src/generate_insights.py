"""Generate grounded executive briefs through the OpenAI Responses API.

Standard library only. --preview is offline and never presented as API output.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ('summary', 'drivers', 'risks', 'actions', 'limitations')
TOKEN = re.compile(r'\{\{(f\d+)\}\}')
SCHEMA = {'type': 'object', 'properties': {
    k: {'type': 'string'} if k == 'summary' else {'type': 'array', 'items': {'type': 'string'}}
    for k in SECTIONS}, 'required': list(SECTIONS), 'additionalProperties': False}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_key_input(key):
    key = key.strip()
    if not re.fullmatch(r'sk-[A-Za-z0-9_-]+', key):
        raise ValueError('The key was not pasted correctly. Copy the full API key, reopen Run AI Brief.cmd, and use Ctrl+V in the password box to paste it. No request was sent.')
    return key

def ask_key_dialog():
    import tkinter as tk
    from tkinter import simpledialog
    window = tk.Tk()
    window.withdraw()
    window.attributes('-topmost', True)
    try:
        return simpledialog.askstring(
            'RetailPulse — API key',
            'Paste your OpenAI API key here using Ctrl+V.\nThe key is hidden and is not saved.',
            show='*', parent=window) or ''
    finally:
        window.destroy()

def catalog(metrics):
    if metrics.get('validation', {}).get('failures') != 0 or metrics.get('validation', {}).get('checks_passed', 0) < 220:
        raise ValueError('Metrics must carry a passing validation result before narration.')
    facts = {}
    def add(label, value):
        facts[f'f{len(facts):03}'] = {'label': label, 'display': value}
    add('Reporting period', metrics['period'])
    add('Comparison period', metrics['comparison_period'])
    def metric(label, name, value):
        if value is None:
            display = 'unavailable'
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'Invalid numeric metric: {name}')
            if 'Rate' in name or '%' in name:
                display = f'{value:.2%}'
            elif name in ('Orders', 'Units Sold', 'Customers', 'Repeat Customers', 'Delivered Orders', 'Delivery Eligible Orders', 'Late Orders', 'Reviewed Orders'):
                display = f'{value:,.0f}'
            else:
                display = f'{value:,.2f}'
        add(label, display)
    for name, value in metrics['kpis'].items(): metric(name, name, value)
    for dimension in ('category_drivers', 'state_drivers'):
        for group in ('largest_increases', 'largest_decreases'):
            for row in metrics[dimension][group]:
                for name in ('Revenue', 'YoY Revenue Change', 'YoY Revenue Growth %'):
                    metric(f"{dimension}/{group}/{row['name']}/{name}", name, row[name])
    return facts

def validate_brief(brief, facts):
    if not isinstance(brief, dict) or set(brief) != set(SECTIONS): raise ValueError('Unexpected response structure.')
    if not isinstance(brief['summary'], str): raise ValueError('Summary must be text.')
    if len(brief['summary'].split()) > 120: raise ValueError('Summary exceeds 120 words.')
    if not TOKEN.search(brief['summary']): raise ValueError('Summary must reference supplied facts.')
    for key in SECTIONS[1:]:
        if not isinstance(brief[key], list) or not all(isinstance(s, str) for s in brief[key]): raise ValueError('Sections must contain text lists.')
    if not 1 <= len(brief['actions']) <= 3: raise ValueError('Provide one to three investigation actions.')
    for text in [brief['summary']] + [s for key in SECTIONS[1:] for s in brief[key]]:
        if not text.strip(): raise ValueError('Empty statement.')
        for ref in TOKEN.findall(text):
            if ref not in facts: raise ValueError(f'Unknown fact reference: {ref}')
        remainder = TOKEN.sub('', text)
        if re.search(r'\d', remainder) or '{{' in remainder or '}}' in remainder:
            raise ValueError('Numbers and periods must use supplied fact placeholders.')

def extract_response(response):
    if response.get('status') != 'completed': raise ValueError('API response is incomplete; no brief saved.')
    parts = []
    for item in response.get('output', []):
        if item.get('type') != 'message': continue
        for content in item.get('content', []):
            if content.get('type') == 'refusal': raise ValueError('The API refused the request; no brief saved.')
            if content.get('type') == 'output_text': parts.append(content['text'])
    if not parts: raise ValueError('No output text returned.')
    return json.loads(''.join(parts))

def request_brief(model, key, instructions, metrics, facts):
    # Only aggregated facts and definitions are sent. No CSV rows or customer IDs.
    payload = {'model': model, 'store': False, 'max_output_tokens': 4000,
               'instructions': instructions,
               'input': json.dumps({'facts': facts, 'definitions': metrics['definitions'], 'limitations': metrics['limitations']}),
               'text': {'format': {'type': 'json_schema', 'name': 'executive_brief', 'strict': True, 'schema': SCHEMA}}}
    request = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(payload).encode(),
                                     headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = 'The server did not provide a readable error explanation.'
        try:
            raw_error = exc.read(65536).decode('utf-8', errors='replace')
            if raw_error.strip():
                detail = re.sub(r'<[^>]*>', ' ', raw_error)
            error = json.loads(raw_error).get('error', {})
            if isinstance(error, dict):
                detail = str(error.get('message') or detail)
        except (ValueError, OSError, AttributeError):
            pass
        # Never echo a credential, even if the server includes it in its error.
        detail = detail.replace(key, '[REDACTED]') if key else detail
        detail = re.sub(r'sk-[A-Za-z0-9_*-]+', '[REDACTED]', detail)
        detail = ' '.join(detail.split())[:1500]
        diagnostic = f'API request failed with HTTP {exc.code}: {detail} No brief saved.'
        diagnostic += '\nResponse type: ' + str(exc.headers.get('Content-Type', 'not supplied'))
        diagnostic += '\nRequest ID: ' + str(exc.headers.get('x-request-id', 'not supplied'))
        (ROOT/'outputs'/'last_api_error.txt').write_text(diagnostic, encoding='utf-8')
        raise ValueError(diagnostic) from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('API connection failed or timed out. No brief saved; no automatic paid retry was attempted.') from None

def preview(facts):
    refs = {v['label']: '{{'+k+'}}' for k,v in facts.items()}
    return {'summary': f"Historical reporting period {refs['Reporting period']} is compared with {refs['Comparison period']}. Merchandise revenue was {refs['Revenue']}, with year-over-year growth of {refs['YoY Revenue Growth %']}. Orders totaled {refs['Orders']}. This is an offline template preview, not AI-generated analysis.",
            'drivers': ['Review the category and state revenue changes in the Performance Drivers dashboard to identify contributors; changes alone do not establish causes.'],
            'risks': [f"Late deliveries: {refs['Late Orders']} of {refs['Delivery Eligible Orders']} eligible delivered orders, a rate of {refs['Late Delivery Rate']}.", f"The order-weighted average review score was {refs['Average Review Score']} across {refs['Reviewed Orders']} reviewed orders."],
            'actions': ['Investigate late deliveries by category and state before attributing causes.', 'Review category and state revenue changes alongside order counts.'],
            'limitations': ['Historical public dataset; revenue includes all statuses and excludes freight.', 'Repeat purchases are measured within the selection, not lifetime retention. No causal conclusions are established.']}

def render(brief, facts, mode):
    used = []
    def replace(match):
        ref=match.group(1)
        if ref not in used: used.append(ref)
        return facts[ref]['display'] + f' [{ref}]'
    lines = ['# RetailPulse AI — Executive Sales Brief', '',
             '**Offline template preview — no API call made.**' if mode == 'preview' else '**API-generated draft — review business interpretations before sharing.**', '']
    for key in SECTIONS:
        lines += ['## '+key.title(), '']
        values=[brief[key]] if key=='summary' else brief[key]
        lines += [('' if key=='summary' else '- ')+TOKEN.sub(replace, text) for text in values]
        lines += ['']
    lines += ['## Evidence', ''] + [f"- [{ref}] {facts[ref]['label']}: {facts[ref]['display']}" for ref in used]
    return '\n'.join(lines)+'\n'

def main():
    settings=json.loads((ROOT/'config'/'narrator.json').read_text(encoding='utf-8'))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics',type=Path,default=ROOT/'outputs'/'ai_metrics.json')
    parser.add_argument('--model',default=os.getenv('OPENAI_MODEL') or settings['model'])
    parser.add_argument('--ask-key',action='store_true',help='Privately prompt for a missing key; keep it in memory only.')
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    raw=args.metrics.read_bytes(); metrics=json.loads(raw.decode('utf-8-sig')); facts=catalog(metrics)
    prompt=(ROOT/'prompts'/'executive_summary_prompt.txt').read_text(encoding='utf-8')
    prompt += '\nReturn the requested JSON structure. All numbers, dates and percentages MUST be placeholders from the fact catalog, e.g. {{f000}}. Do not write literal digits or calculate new values. Use placeholders only for their exact labeled meaning. The renderer inserts formatted values and evidence references. Write one to three investigation actions.\n'
    response={}
    if args.preview: brief=preview(facts)
    else:
        key=os.getenv('OPENAI_API_KEY')
        if not key and args.ask_key:
            key=ask_key_dialog().strip()
        if not key or not args.model: raise ValueError('API key missing. Open Run AI Brief.cmd to enter it privately, or set OPENAI_API_KEY locally.')
        key=validate_key_input(key)
        response=request_brief(args.model,key,prompt,metrics,facts)
        brief=extract_response(response)
    validate_brief(brief,facts)
    mode='preview' if args.preview else 'api'; stem='sample_brief_preview' if args.preview else 'executive_sales_brief'
    markdown=render(brief,facts,mode)
    (ROOT/'outputs'/f'{stem}.md').write_text(markdown,encoding='utf-8')
    (ROOT/'outputs'/f'{stem}.json').write_text(json.dumps(brief,indent=2),encoding='utf-8')
    provenance={'mode':mode,'created_utc':datetime.now(timezone.utc).isoformat(),'model':response.get('model'),
                'response_id':response.get('id'),'usage':response.get('usage'),'metrics_sha256':digest(raw),
                'prompt_sha256':digest(prompt.encode()),'output_sha256':digest(markdown.encode()),
                'checks':'Structure, known fact references, no literal numeric claims, summary length and action count. Semantic accuracy still requires human review.'}
    (ROOT/'outputs'/f'{stem}.provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(f'Saved {stem}.md ({mode}).')

if __name__=='__main__':
    try: main()
    except (ValueError,OSError) as exc: print(str(exc),file=sys.stderr); sys.exit(1)
