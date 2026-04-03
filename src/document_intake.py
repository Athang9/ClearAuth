"""
document_intake.py
Extracts structured fields from clinical note PDFs using Groq API.
Includes retry logic and graceful error handling so a bad AI response
never crashes the pipeline.
"""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from groq import Groq
from pypdf import PdfReader
from models import ClinicalNote, ExtractedFields
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

EXTRACT_PROMPT = """You are a clinical data extraction specialist.
Extract structured fields from the following clinical note.
Return ONLY valid JSON — no markdown, no explanation, no code fences, just raw JSON:
{
  "patient_id": "string (use the ID from the note, or 'UNKNOWN')",
  "patient_age": integer or null,
  "diagnosis_codes": ["list of ICD-10 codes as strings"],
  "procedure_codes": ["list of CPT codes as strings"],
  "clinical_justification": "1-2 sentence clinical rationale for the procedure",
  "ordering_provider": "provider name or 'UNKNOWN'",
  "payer": "insurance payer name or 'UNKNOWN'",
  "urgency": "routine or urgent or emergent"
}"""

# Stricter prompt used on retry — explicitly forbids any non-JSON output
EXTRACT_PROMPT_STRICT = """IMPORTANT: Output ONLY a raw JSON object. No text before or after.
No markdown. No backticks. No explanation. Start your response with { and end with }.

Extract these fields from the clinical note:
{
  "patient_id": "string",
  "patient_age": integer or null,
  "diagnosis_codes": ["ICD-10 codes"],
  "procedure_codes": ["CPT codes"],
  "clinical_justification": "string",
  "ordering_provider": "string",
  "payer": "string",
  "urgency": "routine or urgent or emergent"
}"""


def _clean_raw(raw: str) -> str:
    """Strip markdown code fences if the model adds them anyway."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        # parts[1] is the content between first pair of backticks
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _call_groq(prompt: str) -> str:
    """Make one Groq API call and return raw text."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def extract_fields(note: ClinicalNote, max_retries: int = 3) -> ExtractedFields:
    """
    Send clinical note to Groq and parse the response.
    Retries up to max_retries times on JSON errors or validation failures.
    Uses a stricter prompt on subsequent attempts.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        prompt_to_use = EXTRACT_PROMPT if attempt == 1 else EXTRACT_PROMPT_STRICT
        full_prompt   = f"{prompt_to_use}\n\n---\nCLINICAL NOTE:\n{note.raw_text}"

        try:
            raw  = _call_groq(full_prompt)
            raw  = _clean_raw(raw)
            data = json.loads(raw)
            return ExtractedFields(**data)

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error (attempt {attempt}): {e}"
            print(f"  [retry {attempt}/{max_retries}] Bad JSON from model — retrying...")

        except Exception as e:
            last_error = f"Validation error (attempt {attempt}): {e}"
            print(f"  [retry {attempt}/{max_retries}] Field validation failed — retrying...")

        if attempt < max_retries:
            time.sleep(1)  # brief pause before retry

    # All retries exhausted — return a safe fallback instead of crashing
    print(f"  [WARNING] Extraction failed after {max_retries} attempts. Using fallback values.")
    print(f"  Last error: {last_error}")
    return ExtractedFields(
        patient_id="EXTRACTION_FAILED",
        patient_age=None,
        diagnosis_codes=[],
        procedure_codes=[],
        clinical_justification="Extraction failed — manual review required.",
        ordering_provider="UNKNOWN",
        payer="UNKNOWN",
        urgency="routine"
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Pull raw text from a PDF. Returns empty string if PDF can't be read."""
    try:
        reader = PdfReader(pdf_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print(f"  [WARNING] Could not read PDF: {e}")
        return ""


def intake_pdf(pdf_path: str) -> ExtractedFields:
    """Full intake: read PDF → send to Groq → return structured data."""
    print(f"  Reading PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        print("  [WARNING] PDF appears empty or unreadable. Using fallback values.")
        return ExtractedFields(
            patient_id="UNREADABLE_PDF",
            patient_age=None,
            diagnosis_codes=[],
            procedure_codes=[],
            clinical_justification="PDF could not be read — manual review required.",
            ordering_provider="UNKNOWN",
            payer="UNKNOWN",
            urgency="routine"
        )

    note = ClinicalNote(raw_text=text, source_file=pdf_path)
    print("  Sending to Groq (llama-3.3-70b) for extraction...")
    return extract_fields(note)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python document_intake.py <path_to_pdf>")
        sys.exit(1)
    result = intake_pdf(sys.argv[1])
    print(result.model_dump_json(indent=2))
