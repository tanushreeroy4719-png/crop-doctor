import json
import os

from config import Config

_DISEASE_INFO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "data", "disease_info.json")

with open(_DISEASE_INFO_PATH) as f:
    DISEASE_INFO = json.load(f)


def _readable_answers(answers):
    labels = {
        "leaf_discoloration": "Leaf discoloration",
        "wilting": "Wilting / dropping",
        "weather": "Recent weather",
        "temperature": "Temperature",
        "fertilizer": "Recent fertilizer use",
        "pesticide": "Previous pesticide use",
        "insects": "Insects observed",
        "pest_damage": "Pest damage evidence",
        "watering": "Watering frequency",
        "growth_stage": "Plant age / growth stage",
    }
    lines = []
    for key, value in answers.items():
        if value and value.lower() != "select...":
            lines.append(f"{labels.get(key, key)}: {value}")
    return lines


def _rule_based_report(disease_key, confidence, answers):
    info = DISEASE_INFO.get(disease_key, {
        "crop": "Plant", "condition": disease_key, "healthy": False,
        "summary": "No details available for this class yet.",
        "treatment": "Consult a local agricultural extension office.",
        "prevention": "Monitor the plant regularly."
    })
    context_lines = _readable_answers(answers)
    context_block = "\n".join(f"- {line}" for line in context_lines) if context_lines else "- No extra details provided."

    if info["healthy"]:
        return (
            f"## Diagnosis: {info['crop']} — Healthy\n\n"
            f"Confidence: {confidence * 100:.1f}%\n\n"
            f"{info['summary']}\n\n"
            "### What to do\n"
            f"{info['prevention']}\n\n"
            "### Notes from your answers\n"
            f"{context_block}\n"
        )

    return (
        f"## Diagnosis: {info['crop']} — {info['condition']}\n\n"
        f"Confidence: {confidence * 100:.1f}%\n\n"
        f"### What this is\n{info['summary']}\n\n"
        f"### Recommended treatment\n{info['treatment']}\n\n"
        f"### Prevention going forward\n{info['prevention']}\n\n"
        "### Notes from your answers\n"
        f"{context_block}\n\n"
        "_This is an automated first read, not a substitute for a local "
        "agronomist or extension office, especially for large-scale "
        "treatment decisions._"
    )


def _claude_report(disease_key, confidence, answers):
    from anthropic import Anthropic

    info = DISEASE_INFO.get(disease_key, {})
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context_lines = _readable_answers(answers)
    context_block = "\n".join(f"- {line}" for line in context_lines) if context_lines else "- No extra details provided."

    prompt = f"""You are an agronomist writing a short farmer-facing report.

Model prediction: {info.get('crop', 'Unknown crop')} — {info.get('condition', disease_key)}
Model confidence: {confidence * 100:.1f}%
Reference summary: {info.get('summary', 'N/A')}
Reference treatment: {info.get('treatment', 'N/A')}
Reference prevention: {info.get('prevention', 'N/A')}

Farmer-reported context:
{context_block}

Write a concise Markdown report with headings ## Diagnosis, ### What this means,
### Recommended treatment, ### Prevention. Use the farmer-reported context to
tailor advice (e.g. adjust watering guidance if they reported overwatering).
Keep it under 220 words, plain language, no bullet spam. If confidence is
below 60%, open with a one-line caveat recommending a second photo or expert
opinion before treating."""

    resp = client.messages.create(
        model=Config.ANTHROPIC_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if hasattr(block, "text"))


def generate_report(disease_key, confidence, answers):
    """Returns (report_markdown, used_ai_bool)."""
    if Config.ANTHROPIC_API_KEY:
        try:
            return _claude_report(disease_key, confidence, answers), True
        except Exception:
            # Fall through to rule-based so a bad/missing key never breaks the app.
            pass
    return _rule_based_report(disease_key, confidence, answers), False
