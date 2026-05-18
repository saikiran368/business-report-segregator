"""
summary_engine.py
Generates data-driven summaries from PDF table content using Claude.
Uses inference profile IDs (required for this AWS account).
"""

import boto3
import json
from botocore.exceptions import ClientError

DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-6"


def generate_summary(
    table: dict,
    ref_example_summary: str = None,
    model_id: str = DEFAULT_MODEL,
    region: str = "us-east-1",
) -> list:
    table_text = _format_table(table)
    prompt     = _build_prompt(table_text, ref_example_summary)

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        body   = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(
            modelId=model_id, body=body,
            contentType="application/json", accept="application/json",
        )
        raw = json.loads(response["body"].read())["content"][0]["text"].strip()
        return _parse_bullets(raw)

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code == "AccessDeniedException":
            return ["Bedrock access denied — enable model in Bedrock Console → Model Access."]
        if code in ("ResourceNotFoundException", "ValidationException"):
            return [f"Model error: {msg}"]
        return [f"AWS error ({code}): {msg}"]
    except Exception as e:
        return [f"Summary failed: {str(e)}"]


def _build_prompt(table_text: str, ref_example: str = None) -> str:
    style_section = ""
    if ref_example:
        style_section = f"""
=== REFERENCE STYLE (match this tone and level of detail) ===
{ref_example[:800]}
=== END REFERENCE ===

"""
    return f"""You are an operations analyst. Analyze the table data below and write a concise summary.
{style_section}
=== TABLE DATA ===
{table_text}
=== END TABLE DATA ===

STRICT RULES:
- Every number, percentage, site name, or value you mention MUST come directly from the table above
- Do NOT invent or assume any data not present in the table
- Write 4 to 6 bullet points, each 1-2 sentences
- Focus on: key totals, notable variances (over/under budget), trends, outliers
- Use plain text — no markdown bold, no headers
- Start each bullet with a dash (-)
- If the table shows Budget vs Actuals, highlight sites significantly over or under budget

Summary:"""


def _format_table(table: dict) -> str:
    headers  = table.get("headers", [])
    all_rows = table.get("all_rows", [])
    rows     = table.get("rows", all_rows[1:] if len(all_rows) > 1 else [])

    lines = [" | ".join(str(h) for h in headers[:16])]
    lines.append("-" * 80)
    for row in rows[:40]:
        line = " | ".join(str(c) for c in row[:16])
        if line.strip(" |"):
            lines.append(line)
    if len(rows) > 40:
        lines.append(f"... and {len(rows) - 40} more rows")
    return "\n".join(lines)


def _parse_bullets(raw: str) -> list:
    bullets = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line[0] in ("-", "•", "*", "–", "—"):
            bullets.append(line[1:].strip())
        elif line[0].isdigit() and len(line) > 2 and line[1] in (".", ")"):
            bullets.append(line[2:].strip())
        elif line and not line.startswith("#") and not line.startswith("==="):
            bullets.append(line)
    return bullets if bullets else ["No summary generated."]


def get_available_models() -> dict:
    """Inference profile IDs — required for this AWS account."""
    return {
        "Claude Sonnet 4.6 (Recommended)": "us.anthropic.claude-sonnet-4-6",
        "Claude Haiku 4.5 (Fast)":          "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "Claude Sonnet 4.5":                "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "Claude Opus 4.6 (Most capable)":   "us.anthropic.claude-opus-4-6-v1",
    }
