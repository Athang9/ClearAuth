"""
appeals_generator.py
Automatically drafts a formal appeal letter when a PA is denied using Groq API.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from groq import Groq
from models import PADecision, ExtractedFields, AppealLetter
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

APPEAL_PROMPT = """You are a senior healthcare appeals specialist writing a formal prior
authorization appeal letter on behalf of a healthcare provider.

Write a professional, medically grounded appeal letter that:
1. Opens with the specific denial reason and states the provider disagrees
2. Cites the patient's clinical situation and why the procedure is medically necessary
3. References why alternatives are unsuitable for this patient
4. Cites relevant clinical guidelines supporting the procedure
5. Closes with a request for expedited review and peer-to-peer discussion offer
6. Uses today's date and formal letter structure
7. Is under 400 words — concise and persuasive

Return ONLY the letter text. No commentary, no placeholders."""


def generate_appeal(decision: PADecision, fields: ExtractedFields) -> AppealLetter:
    context = f"""
Patient ID: {fields.patient_id}
Patient Age: {fields.patient_age or 'Not specified'}
Payer: {fields.payer}
Procedure Codes: {', '.join(fields.procedure_codes)}
Diagnosis Codes: {', '.join(fields.diagnosis_codes)}
Urgency: {fields.urgency}
Clinical Justification: {fields.clinical_justification}
Ordering Provider: {fields.ordering_provider}
Denial Reason: {decision.reason}
Missing Criteria: {', '.join(decision.missing_criteria) if decision.missing_criteria else 'Not specified'}
"""
    prompt = f"{APPEAL_PROMPT}\n\nCASE DETAILS:\n{context}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
    )
    letter_text = response.choices[0].message.content.strip()

    return AppealLetter(
        case_id=decision.case_id,
        denial_reason=decision.reason,
        letter_text=letter_text,
        evidence_cited=fields.diagnosis_codes + fields.procedure_codes
    )
