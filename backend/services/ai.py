import re
import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = """You are a professional building inspection report writer.
You receive text from two documents:
1. Site Inspection Report — visual observations
2. Thermal Imaging Report — temperature readings and thermal findings

Generate a Detailed Diagnostic Report (DDR) as strict JSON.

Rules:
- Do NOT invent facts not present in the documents.
- Missing info → "Not Available".
- Conflicting info → "Conflict: [description]".
- Plain, client-friendly language. No jargon.
- Merge and deduplicate findings per area.
- Combine visual and thermal data logically.

Return ONLY valid JSON. No markdown, no preamble. Schema:
{
  "report_title": "string",
  "property_name": "string",
  "inspection_date": "string",
  "report_ref": "string",
  "property_issue_summary": "string",
  "areas": [
    {
      "area_name": "string",
      "visual_observation": "string",
      "thermal_finding": "string",
      "visual_image_label": "string or Not Available",
      "thermal_image_label": "string or Not Available",
      "probable_root_cause": "string",
      "severity": "Critical | High | Medium | Low",
      "severity_reasoning": "string"
    }
  ],
  "overall_severity": "Critical | High | Medium | Low",
  "recommended_actions": [
    { "action": "string", "priority": "Immediate | Short-term | Long-term", "area": "string" }
  ],
  "additional_notes": ["string"],
  "missing_or_unclear": ["string"]
}"""


def generate_ddr(inspection_text: str, thermal_text: str) -> dict:
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"=== INSPECTION REPORT ===\n{inspection_text}\n\n"
                f"=== THERMAL REPORT ===\n{thermal_text}\n\n"
                "Generate the DDR JSON now."
            )},
        ],
        temperature=0.2,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*",     "", raw)
    raw = re.sub(r"\s*```$",     "", raw)
    return json.loads(raw)
