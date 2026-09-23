"""Create a grounded sales brief from validated RetailPulse measures."""
import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
METRICS = {
    "revenue": ("Revenue", "currency"),
    "growth": ("YoY Revenue Growth %", "percent"),
    "orders": ("Orders", "integer"),
    "customers": ("Customers", "integer"),
    "late_rate": ("Late Delivery Rate", "percent"),
    "delivery_days": ("Average Delivery Days", "decimal"),
    "review_score": ("Average Review Score", "decimal"),
}
SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "overview": {"type": "string"},
        "highlights": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "risks": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "next_steps": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
    },
    "required": ["headline", "overview", "highlights", "risks", "next_steps"],
    "additionalProperties": False,
}
OLLAMA_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "enum": [
            "Sales growth with delivery and customer experience in view",
            "Revenue momentum supported by active customer demand",
            "Commercial performance with operational measures to monitor",
        ]},
        "overview": {"type": "string", "enum": [
            "Revenue was {{revenue}}, with year-over-year growth of {{growth}}, across {{orders}} orders and {{customers}} customers."
        ]},
        "highlights": {"type": "array", "items": {"type": "string", "enum": [
            "Late deliveries represented {{late_rate}} of eligible delivered orders.",
            "Average delivery time was {{delivery_days}} days.",
            "Average review score was {{review_score}} out of five.",
        ]}, "minItems": 3, "maxItems": 3, "uniqueItems": True},
        "risks": {"type": "array", "items": {"type": "string", "enum": [
            "Delivery timeliness remains a metric to monitor at {{late_rate}}.",
            "Customer experience should be reviewed alongside the {{review_score}} average review score.",
        ]}, "minItems": 1, "maxItems": 2, "uniqueItems": True},
        "next_steps": {"type": "array", "items": {"type": "string", "enum": [
            "Break down delivery timing by state and category to identify where delays are concentrated.",
            "Review affected orders before proposing a cause for late delivery.",
            "Compare category revenue with order volume before interpreting the growth pattern.",
        ]}, "minItems": 1, "maxItems": 3, "uniqueItems": True},
    },
    "required": ["headline", "overview", "highlights", "risks", "next_steps"],
    "additionalProperties": False,
}
INSTRUCTIONS = """You write a concise executive sales brief from supplied facts.
Use only the supplied facts. Never calculate, infer a cause, invent a number, or claim a ranking.
Every number and date must be written as its exact placeholder, such as {{revenue}}.
Do not write literal digits. Keep the full response under 180 words.
Use every supplied placeholder at least once. Do not add a percent or currency symbol after a placeholder.
The overview must use {{revenue}}, {{growth}}, {{orders}}, and {{customers}}.
The highlights must use {{late_rate}}, {{delivery_days}}, and {{review_score}}.
Do not claim that delivery or review metrics increased, decreased, improved, or worsened because no comparison is supplied.
Risks may only identify supplied metrics to monitor; do not invent external risks, causes, forecasts, or business events.
Next steps must investigate the dashboard by category, state, or affected orders. Do not recommend campaigns or investments.
Use neutral business language and make next steps investigative rather than causal."""


def _display(value, style):
    if style == "currency":
        return f"${value:,.2f}"
    if style == "percent":
        return f"{value:.1%}"
    if style == "integer":
        return f"{value:,.0f}"
    return f"{value:.2f}"


def load_facts(path, context="month201807"):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("failures") or data.get("checks", 0) < 220:
        raise ValueError("The measure validation must pass before a brief can be generated.")
    rows = {(r["context"], r["measure"]): r for r in data["results"]}
    facts = {}
    for key, (measure, style) in METRICS.items():
        row = rows.get((context, measure))
        if not row or not row.get("passed") or row.get("actual") is None:
            raise ValueError(f"Missing validated measure: {context}/{measure}")
        facts[key] = {
            "label": measure,
            "value": row["actual"],
            "display": _display(row["actual"], style),
            "source": f"{context}/{measure}",
        }
    return facts


def build_payload(facts, model):
    prompt = {"period": "current reporting period", "comparison": "prior-year period", "fact_catalog": {
        key: {"meaning": fact["label"], "use_exactly": "{{" + key + "}}"} for key, fact in facts.items()
    }}
    return {
        "model": model,
        "store": False,
        "max_output_tokens": 1200,
        "instructions": INSTRUCTIONS,
        "input": json.dumps(prompt, ensure_ascii=False),
        "text": {"format": {"type": "json_schema", "name": "weekly_sales_brief", "strict": True, "schema": SCHEMA}},
    }


def build_ollama_payload(facts, model):
    prompt = {"period": "current reporting period", "comparison": "prior-year period", "fact_catalog": {
        key: {"meaning": fact["label"], "use_exactly": "{{" + key + "}}"} for key, fact in facts.items()
    }}
    return {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": INSTRUCTIONS + "\nSelect only from the approved language in this schema:\n" + json.dumps(OLLAMA_SCHEMA)},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "format": OLLAMA_SCHEMA,
        "options": {"temperature": 0},
    }


def call_api(payload, api_key):
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            message = ""
        message = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", message)[:500]
        raise ValueError(f"API request failed ({exc.code}). {message}".strip()) from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(f"API connection failed: {exc.reason if hasattr(exc, 'reason') else 'timeout'}") from None


def call_ollama(payload):
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Ollama request failed ({exc.code}).") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Ollama is not running or the local model timed out.") from None


def extract_brief(response):
    if response.get("status") != "completed":
        raise ValueError("The model response was incomplete.")
    text = "".join(
        part.get("text", "")
        for item in response.get("output", []) if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    )
    if not text:
        raise ValueError("The model returned no usable text.")
    return json.loads(text)


def extract_ollama_brief(response):
    if not response.get("done"):
        raise ValueError("The local model response was incomplete.")
    text = response.get("message", {}).get("content", "")
    if not text:
        raise ValueError("The local model returned no usable text.")
    return json.loads(text)


def validate_brief(brief, facts):
    if set(brief) != set(SCHEMA["required"]):
        raise ValueError("Unexpected response structure.")
    text_fields = [brief["headline"], brief["overview"]]
    list_fields = [brief["highlights"], brief["risks"], brief["next_steps"]]
    if not all(isinstance(v, str) and v.strip() for v in text_fields):
        raise ValueError("Headline and overview must contain text.")
    if not all(isinstance(v, list) and 1 <= len(v) <= 4 and all(isinstance(x, str) and x.strip() for x in v) for v in list_fields):
        raise ValueError("Each list section must contain one to four statements.")
    combined = " ".join(text_fields + [x for values in list_fields for x in values])
    refs = set(TOKEN.findall(combined))
    if not refs <= set(facts) or "{{" in TOKEN.sub("", combined) or re.search(r"\d", TOKEN.sub("", combined)):
        raise ValueError("The brief contains an unknown placeholder or an unsupported number.")
    if refs != set(facts) or len(combined.split()) > 180:
        raise ValueError("The brief must cite every supplied fact and stay under 180 words.")


def render(brief, facts, note):
    used = []
    def replace(match):
        key = match.group(1)
        if key not in used:
            used.append(key)
        return f"{facts[key]['display']} [{key}]"
    lines = ["# Weekly Sales Brief", "", note, "", f"## {TOKEN.sub(replace, brief['headline'])}", "", TOKEN.sub(replace, brief["overview"]), ""]
    for key, title in (("highlights", "Highlights"), ("risks", "Risks"), ("next_steps", "Next steps")):
        lines.extend([f"## {title}", ""] + [f"- {TOKEN.sub(replace, item)}" for item in brief[key]] + [""])
    lines.extend(["## Evidence", ""] + [f"- [{key}] {facts[key]['label']}: {facts[key]['display']} (`{facts[key]['source']}`)" for key in used])
    return "\n".join(lines) + "\n"


def sample_brief():
    return {
        "headline": "Revenue grew while delivery and review indicators remained visible",
        "overview": "July revenue reached {{revenue}}, representing {{growth}} year-over-year growth across {{orders}} orders and {{customers}} customers.",
        "highlights": ["Average delivery time was {{delivery_days}} days.", "The average review score was {{review_score}} out of five."],
        "risks": ["The late-delivery rate was {{late_rate}}; investigate affected orders before assigning a cause."],
        "next_steps": ["Compare delivery performance by state and category, then review whether the pattern is concentrated or broad."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "outputs" / "measure-validation.json")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "weekly_sales_brief.md")
    parser.add_argument("--context", default="month201807")
    parser.add_argument("--provider", choices=("ollama", "openai"), default=os.getenv("RETAILPULSE_LLM_PROVIDER", "ollama"))
    parser.add_argument("--model")
    parser.add_argument("--sample", action="store_true", help="Render the checked sample without an API call.")
    args = parser.parse_args()
    args.model = args.model or ("qwen2.5:1.5b" if args.provider == "ollama" else os.getenv("OPENAI_MODEL", "gpt-6-astra"))
    raw = args.input.read_bytes()
    facts = load_facts(args.input, args.context)
    if args.sample:
        brief, response = sample_brief(), {}
        if args.output == ROOT / "outputs" / "weekly_sales_brief.md":
            args.output = ROOT / "outputs" / "weekly_sales_brief.sample.md"
        note = "**Sample layout using validated metrics — no API call was made.**"
    else:
        if args.provider == "ollama":
            response = call_ollama(build_ollama_payload(facts, args.model))
            brief = extract_ollama_brief(response)
            note = "**Locally generated draft — review interpretations before sharing.**"
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set. No request was sent.")
            response = call_api(build_payload(facts, args.model), api_key)
            brief = extract_brief(response)
            note = "**API-generated draft — review interpretations before sharing.**"
    validate_brief(brief, facts)
    markdown = render(brief, facts, note)
    args.output.write_text(markdown, encoding="utf-8")
    provenance = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "sample" if args.sample else args.provider,
        "provider": "sample" if args.sample else args.provider,
        "model": response.get("model") or (None if args.sample else args.model),
        "response_id": response.get("id"),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "context": args.context,
        "facts": list(facts),
    }
    args.output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Saved {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc))
