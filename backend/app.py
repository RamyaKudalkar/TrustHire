
import re

from flask import Flask, jsonify, request, send_from_directory

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "TrustHire backend is connected!"
    })


def sentence_has_pattern(sentence, patterns):
    """Check whether a sentence matches any supplied regex pattern."""
    return any(
        re.search(pattern, sentence, re.IGNORECASE)
        for pattern in patterns
    )


def split_sentences(description):
    """Split sentences without treating Rs. as the end of a sentence."""

    protected_description = re.sub(
        r"\bRs\.",
        "Rs<TRUSTHIRE_DOT>",
        description,
        flags=re.IGNORECASE
    )

    parts = re.split(
        r"(?<=[.!?])\s+",
        protected_description.strip()
    )

    sentences = [
        part.replace("Rs<TRUSTHIRE_DOT>", "Rs.").strip()
        for part in parts
        if part.strip()
    ]

    return sentences


def analyze_offer(description):
    text = description.lower()
    warnings = []

    sentences = split_sentences(description)

    # 1. Check for upfront payment requests

    fee_request_patterns = [
        r"\b(?:pay|submit|transfer|send)\b.{0,50}\b(?:registration|security|processing|training|application|verification)?\s*(?:fee|deposit|charge)\b",
        r"\b(?:registration|security|processing|training|application|verification)\s+(?:fee|deposit|charge)\b.{0,50}\b(?:required|mandatory|must|pay|submit|transfer|send)\b",
        r"\bpayment\s+(?:is\s+)?required\b",
        r"\b(?:fee|deposit)\s+(?:must be paid|is mandatory|is required)\b"
    ]

    fee_denial_patterns = [
        r"\bno\b.{0,45}\b(?:fee|fees|deposit|payment|charge)\b",
        r"\b(?:do not|don't|never)\s+(?:charge|request|require|collect)\b.{0,45}\b(?:fee|fees|deposit|payment)\b",
        r"\bnot required to pay\b",
        r"\bwithout any (?:fee|fees|deposit|payment)\b",
        r"\bno upfront payment\b"
    ]

    fee_evidence = None

    for sentence in sentences:
        has_fee_request = sentence_has_pattern(
            sentence, fee_request_patterns
        )

        fee_is_denied = sentence_has_pattern(
            sentence, fee_denial_patterns
        )

        if has_fee_request and not fee_is_denied:
            fee_evidence = sentence
            break

    if fee_evidence:
        warnings.append({
            "title": "Possible upfront payment request",
            "reason": (
                "The offer mentions a fee or deposit. "
                "Requests for payment during recruitment "
                "deserve careful checking."
            ),
            "evidence": fee_evidence,
            "action": (
                "Contact the company through its independently "
                "found official website to confirm whether "
                "this payment is legitimate."
            )
        })

    # 2. Check for sensitive information requests

    sensitive_patterns = [
        r"\b(?:share|send|provide|submit|enter|reveal|disclose)\b.{0,45}\b(?:passwords?|otps?|bank details|bank account details|banking credentials|card numbers?)\b",
        r"\b(?:passwords?|otps?|bank details|bank account details|banking credentials|card numbers?)\b.{0,45}\b(?:required|mandatory|must be provided|must be shared)\b"
    ]

    sensitive_reassurance_patterns = [
        r"\b(?:never|do not|don't)\s+(?:ask|request|collect)\b.{0,45}\b(?:passwords?|otps?|bank details|banking credentials)\b",
        r"\b(?:not required|should not|must not)\s+(?:share|send|provide)\b.{0,45}\b(?:passwords?|otps?|bank details|banking credentials)\b"
    ]

    sensitive_evidence = None

    for sentence in sentences:
        contains_request = sentence_has_pattern(
            sentence, sensitive_patterns
        )

        is_reassurance = sentence_has_pattern(
            sentence, sensitive_reassurance_patterns
        )

        if contains_request and not is_reassurance:
            sensitive_evidence = sentence
            break

    if sensitive_evidence:
        warnings.append({
            "title": "Sensitive information requested",
            "reason": (
                "The offer appears to request passwords, OTPs "
                "or banking credentials. These are serious "
                "warning signs."
            ),
            "evidence": sensitive_evidence,
            "action": (
                "Do not share passwords, OTPs or banking "
                "credentials with recruiters."
            )
        })

    # 3. Check for unusually strong promises

    promise_patterns = [
        r"\bguaranteed income\b",
        r"\bearn money instantly\b",
        r"\bunlimited salary\b",
        r"\bguaranteed selection\b",
        r"\b100%\s+guaranteed\s+(?:job|selection|income)\b"
    ]

    promise_denial_patterns = [
        r"\bnot guaranteed\b",
        r"\bno guarantee\b",
        r"\bnot a guaranteed\b"
    ]

    promise_evidence = None

    for sentence in sentences:
        has_promise = sentence_has_pattern(
            sentence, promise_patterns
        )

        is_denial = sentence_has_pattern(
            sentence, promise_denial_patterns
        )

        if has_promise and not is_denial:
            promise_evidence = sentence
            break

    if promise_evidence:
        warnings.append({
            "title": "Unusually strong promises",
            "reason": (
                "Guaranteed income or selection claims may "
                "create unrealistic expectations."
            ),
            "evidence": promise_evidence,
            "action": (
                "Ask for a written job description, "
                "compensation details and selection process."
            )
        })

    # 4. Check for urgency and pressure

    urgency_patterns = [
        r"\bonly\s+\d+\s+(?:seconds?|minutes?|hours?)\s+left\b",
        r"\b(?:apply|accept|respond|confirm|join)\s+(?:the offer\s+)?(?:immediately|right away|now)\b",
        r"\b(?:must|required to)\s+(?:accept|respond|confirm|join)\s+(?:the offer\s+)?(?:immediately|right away|now)\b",
        r"\b(?:act|respond|apply)\s+now\b",
        r"\blimited seats\b",
        r"\blimited time\b",
        r"\burgent payment\b",
        r"\boffer expires today\b",
        r"\b(?:lose|miss out on)\s+(?:this|the)\s+(?:opportunity|offer|position)\b"
    ]

    urgency_reassurance_patterns = [
        r"\bno pressure to\b",
        r"\bno need to (?:apply|respond|accept)\s+immediately\b",
        r"\byou can take your time\b"
    ]

    urgency_evidence = None

    for sentence in sentences:
        has_urgency = sentence_has_pattern(
            sentence, urgency_patterns
        )

        is_reassurance = sentence_has_pattern(
            sentence, urgency_reassurance_patterns
        )

        if has_urgency and not is_reassurance:
            urgency_evidence = sentence
            break

    if urgency_evidence:
        warnings.append({
            "title": "Pressure to act quickly",
            "reason": (
                "Urgency can discourage applicants from "
                "checking an opportunity carefully "
                "before responding."
            ),
            "evidence": urgency_evidence,
            "action": (
                "Take time to verify the recruiter and "
                "opportunity before responding."
            )
        })

    # 5. Check employer and contact information

    missing_information = []

    employer_pattern = (
        r"\b([A-Z][A-Za-z0-9&.,'-]*"
        r"(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,4})"
        r"\s+(?:is offering|offers|is hiring|is recruiting|has an opening)\b"
    )

    employer_match = re.search(
        employer_pattern, description
    )

    employer_name_mentioned = bool(
        employer_match
        and employer_match.group(1).strip().lower()
        not in ["we", "our"]
    )

    contact_information_mentioned = any(
        phrase in text
        for phrase in [
            "website",
            "official email",
            "contact"
        ]
    )

    if not employer_name_mentioned:
        missing_information.append(
            "The employer's name is not clearly mentioned."
        )

    if not contact_information_mentioned:
        missing_information.append(
            "No official website or contact information is mentioned."
        )

    if not any(
        word in text
        for word in ["responsibilities", "role", "work"]
    ):
        missing_information.append(
            "The actual job responsibilities need clarification."
        )

    # 6. Company verification awareness

    company_verification = {
        "company_name_mentioned": employer_name_mentioned,
        "contact_information_mentioned": contact_information_mentioned,
        "independent_verification": "Not performed",
        "message": (
            "TrustHire has not independently verified the company's "
            "identity, website, recruiter or job vacancy."
        )
    }

    verification_note = (
        "A company name mentioned in an offer does not prove that "
        "the company or opportunity is genuine. Its identity and "
        "the vacancy must be verified independently."
    )

    # 7. Determine report status

    if warnings:
        status = "Review recommended"
    elif missing_information:
        status = "More information needed"
    else:
        status = "No obvious warning signs detected"

    return {
        "status": status,
        "warning_count": len(warnings),
        "warnings": warnings,
        "missing_information": missing_information,
        "company_verification": company_verification,
        "verification_note": verification_note,
        "verification_steps": [
            "Find the company's official website independently.",
            "Check whether the vacancy appears on its official careers page.",
            "Verify the recruiter's identity using independently obtained company contact details.",
            "Read the written offer and understand all payment and personal-information requests."
        ],
        "disclaimer": (
            "This is an automated preliminary review based on "
            "text patterns. It cannot verify a company or prove "
            "whether an opportunity is genuine or fraudulent."
        )
    }


# 8. API endpoint

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send a valid job description."
        }), 400

    description = data.get("description", "")

    if not isinstance(description, str):
        return jsonify({
            "status": "error",
            "message": "The job description must be text."
        }), 400

    description = description.strip()

    if not description:
        return jsonify({
            "status": "error",
            "message": "Please enter a job description."
        }), 400

    if len(description) < 30:
        return jsonify({
            "status": "error",
            "message": "Please enter more details to analyze."
        }), 400

    if len(description) > 10000:
        return jsonify({
            "status": "error",
            "message": "Please keep the description under 10,000 characters."
        }), 400

    report = analyze_offer(description)

    return jsonify({
        "status": "success",
        "report": report
    })


if __name__ == "__main__":
    app.run(debug=True)
