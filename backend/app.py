
import re
import joblib
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory


# ==================================================
# 1. APP CONFIGURATION
# ==================================================

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "trusthire_model.joblib"
THRESHOLD_PATH = BASE_DIR / "trusthire_threshold.txt"


# ==================================================
# 2. LOAD MACHINE LEARNING MODEL
# ==================================================

model = None
model_threshold = 0.5

try:
    model = joblib.load(MODEL_PATH)
    print("TrustHire ML model loaded successfully.")
except Exception as e:
    print("ML model could not be loaded:", e)

try:
    model_threshold = float(THRESHOLD_PATH.read_text().strip())

    if not 0 < model_threshold < 1:
        raise ValueError("Invalid threshold.")

    print("ML threshold loaded:", model_threshold)

except Exception as e:
    model_threshold = 0.5
    print("Using default ML threshold:", e)


# ==================================================
# 3. PAGE ROUTES
# ==================================================

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/analyzer")
def analyzer():
    return send_from_directory(app.static_folder, "analyzer.html")


# ==================================================
# 4. HEALTH CHECK
# ==================================================

@app.route("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "TrustHire backend is connected!",
        "model_available": model is not None
    })


# ==================================================
# 5. HELPER FUNCTIONS
# ==================================================

def sentence_has_pattern(text, patterns):
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def split_sentences(description):
    """Split sentences and lines while protecting Rs."""

    protected = re.sub(
        r"\bRs\.",
        "Rs<TRUSTHIRE_DOT>",
        description,
        flags=re.IGNORECASE
    )

    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        protected.strip()
    )

    return [
        part.replace("Rs<TRUSTHIRE_DOT>", "Rs.").strip()
        for part in parts
        if part.strip()
    ]


# --------------------------------------------------
# CONTACT EXTRACTION
# --------------------------------------------------

def extract_contact_details(description):

    emails = re.findall(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        description,
        re.IGNORECASE
    )

    urls = re.findall(
        r"(?:https?://|www\.)[^\s<>\"']+",
        description,
        re.IGNORECASE
    )

    urls = [
        url.rstrip(".,;:!?)\"}")
        for url in urls
    ]

    phones = re.findall(
        r"(?<![A-Za-z0-9])(?:\+?\d[\d\s().-]{8,}\d)(?![A-Za-z0-9])",
        description
    )

    return {
        "emails": list(dict.fromkeys(emails)),
        "urls": list(dict.fromkeys(urls)),
        "phones": list(dict.fromkeys(phones))
    }


# --------------------------------------------------
# RECRUITER SIGNATURE EXTRACTION
# --------------------------------------------------

def extract_signature_details(description):

    lines = [
        line.strip()
        for line in description.splitlines()
        if line.strip()
    ]

    recruiter_name = None
    recruiter_role = None
    organization = None

    role_words = (
        r"manager|director|recruiter|hr|"
        r"human resources|coordinator|"
        r"team lead|head|officer"
    )

    for index in range(len(lines) - 1, -1, -1):

        line = lines[index]

        if "|" not in line:
            continue

        left, right = line.split("|", 1)

        left = re.sub(
            r"^(regards|regard|best regards|sincerely|thanks)[,\s]*",
            "",
            left.strip(),
            flags=re.IGNORECASE
        )

        right = right.strip().strip("*_ ")

        if not right or len(right) > 100:
            continue

        role_match = re.search(
            rf"\b({role_words})\b",
            left,
            re.IGNORECASE
        )

        if not role_match:
            continue

        recruiter_role = role_match.group(1).title()

        name_part = left[:role_match.start()].strip()
        name_part = name_part.strip(" ,:-")

        if not name_part and index > 0:

            previous_line = lines[index - 1].strip()

            if (
                len(previous_line.split()) <= 4
                and not re.search(
                    r"\b(regards|sincerely|thanks|best regards)\b",
                    previous_line,
                    re.IGNORECASE
                )
                and not re.search(r"[@:/]", previous_line)
            ):
                name_part = previous_line

        if name_part:
            recruiter_name = name_part

        organization = right
        break

    return {
        "recruiter_name": recruiter_name,
        "recruiter_role": recruiter_role,
        "organization": organization
    }


# --------------------------------------------------
# EMPLOYER NAME EXTRACTION
# --------------------------------------------------

def extract_employer_name(description):

    explicit_patterns = [
        r"(?:company|organization|employer)\s*:\s*([^\n,;]+)",
        r"\binternship\s+at\s+([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})(?=[.!?,\n]|$)",
        r"\bposition\s+at\s+([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})(?=[.!?,\n]|$)",
        r"\brole\s+at\s+([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})(?=[.!?,\n]|$)",
        r"\bat\s+([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})(?=[.!?,\n]|$)"
    ]

    for pattern in explicit_patterns:

        match = re.search(
            pattern,
            description
        )

        if match:
            return match.group(1).strip().rstrip(".,;:!?")

    signature = extract_signature_details(description)

    if signature["organization"]:
        return signature["organization"]

    employer_patterns = [
        r"\b([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})\s+(?:is accepting applications|is inviting applications|is offering|offers|is hiring|is recruiting|has an opening)\b",

        r"\b([A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*){0,5})\s+(?:is looking for|seeks|is seeking)\b"
    ]

    for pattern in employer_patterns:

        match = re.search(pattern, description)

        if match:
            name = match.group(1).strip()

            if name.lower() not in ["we", "our"]:
                return name

    return None


# --------------------------------------------------
# OFFER DETAILS EXTRACTION
# --------------------------------------------------

def extract_offer_details(description):

    # STIPEND OR COMPENSATION
    # Avoid treating registration fees as stipends.

    money_pattern = (
        r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?"
        r"(?:\s*(?:-|–|—|to)\s*"
        r"(?:₹|Rs\.?|INR)?\s*[\d,]+(?:\.\d{1,2})?)?"
    )

    stipend = None

    for match in re.finditer(
        money_pattern,
        description,
        re.IGNORECASE
    ):

        before = description[
            max(0, match.start() - 60):match.start()
        ]

        after = description[
            match.end():match.end() + 40
        ]

        has_compensation_context = re.search(
            r"\b(stipend|salary|compensation|remuneration|paid|earn)\b",
            before,
            re.IGNORECASE
        )

        has_payment_period = re.search(
            r"\b(per month|monthly|per annum|per year)\b",
            after,
            re.IGNORECASE
        )

        if has_compensation_context or has_payment_period:

            stipend = match.group(0).strip()

            period = re.match(
                r"\s*(per month|monthly|per annum|per year)",
                after,
                re.IGNORECASE
            )

            if period:
                stipend += " " + period.group(1)

            break

    # DURATION

    duration_pattern = (
        r"\b(?:duration(?:\s+of)?|internship\s+duration)"
        r"\s*(?:is|:)?\s*"
        r"(\d+\s*(?:-|–|—|to)\s*\d+\s*"
        r"(?:days?|weeks?|months?|years?)|"
        r"\d+\s*(?:days?|weeks?|months?|years?))"
        r"|\b(?:lasts?|will\s+run\s+for|runs\s+for)"
        r"\s*(\d+\s*(?:-|–|—|to)\s*\d+\s*"
        r"(?:days?|weeks?|months?|years?)|"
        r"\d+\s*(?:days?|weeks?|months?|years?))"
        r"|\binternship\s+(?:will\s+)?for\s+"
        r"(\d+\s*(?:-|–|—|to)\s*\d+\s*"
        r"(?:days?|weeks?|months?|years?)|"
        r"\d+\s*(?:days?|weeks?|months?|years?))"
    )

    duration_match = re.search(
        duration_pattern,
        description,
        re.IGNORECASE
    )

    duration = None

    if duration_match:

        duration = next(
            (
                group.strip()
                for group in duration_match.groups()
                if group
            ),
            None
        )

        if duration:
            duration = re.sub(r"\s+", " ", duration)

    # ROLE

    role_patterns = [
        r"(?:position|role)\s*:\s*([^\n.;]+)",
        r"\bfor an?\s+([A-Z][A-Za-z /-]{2,60}?)\s+intern\b"
    ]

    role = None

    for pattern in role_patterns:

        role_match = re.search(
            pattern,
            description,
            re.IGNORECASE
        )

        if role_match:
            role = role_match.group(1).strip()
            break

    # RESPONSIBILITIES

    responsibility_patterns = [
        r"\bresponsibilities\b",
        r"\bduties\b",
        r"\byour tasks\b",
        r"\btasks include\b",
        r"\byou will be responsible\b",
        r"\byou will work on\b",
        r"\byou will assist\b",
        r"\byou will develop\b",
        r"\byou will design\b",
        r"\byou will test\b",
        r"\byou will analyze\b",
        r"\byou will manage\b",
        r"\byou will create\b"
    ]

    responsibilities_provided = sentence_has_pattern(
        description,
        responsibility_patterns
    )

    return {
        "stipend": stipend,
        "duration": duration,
        "role": role,
        "responsibilities_provided": responsibilities_provided
    }


# ==================================================
# 6. MACHINE LEARNING ASSESSMENT
# ==================================================

def assess_with_ml(description):

    if model is None:
        return {
            "available": False,
            "flagged": False,
            "message": "ML model is unavailable."
        }

    try:

        probabilities = model.predict_proba([description])
        fraud_score = float(probabilities[0][1])

        flagged = fraud_score >= model_threshold

        if flagged:
            message = (
                "The ML model identified patterns similar "
                "to fraudulent job postings in its training data. "
                "Further verification is recommended."
            )
        else:
            message = (
                "The model did not flag this text. "
                "This does not establish that the opportunity is genuine."
            )

        return {
            "available": True,
            "flagged": flagged,
            "message": message
        }

    except Exception as e:

        print("ML prediction error:", e)

        return {
            "available": False,
            "flagged": False,
            "message": "ML assessment could not be completed."
        }


# ==================================================
# 7. OFFER ANALYSIS
# ==================================================

def analyze_offer(description):

    sentences = split_sentences(description)

    warnings = []
    missing_information = []

    contacts = extract_contact_details(description)
    signature = extract_signature_details(description)
    employer_name = extract_employer_name(description)
    offer_details = extract_offer_details(description)

    # ------------------------------------------------
    # 7.1 UPFRONT PAYMENT
    # ------------------------------------------------

    fee_request_patterns = [
        r"\b(?:pay|submit|transfer|send)\b.{0,60}\b(?:registration|security|processing|training|application|verification)?\s*(?:fee|fees|deposit|charge)\b",

        r"\b(?:registration|security|processing|training|application|verification)\s+(?:fee|fees|deposit|charge)\b.{0,60}\b(?:required|mandatory|must|pay|submit|transfer|send)\b",

        r"\bpayment\s+(?:is\s+)?required\b",

        r"\b(?:fee|deposit)\s+(?:must be paid|is mandatory|is required)\b",

        r"\b(?:refundable|non-refundable)\s+(?:registration|security|training|processing)?\s*(?:fee|deposit)\b"
    ]

    fee_denial_patterns = [
        r"\bno\b(?:\s+\w+){0,4}\s+(?:registration|application|processing|security|training)\s+(?:fee|fees|deposit)\b",

        r"\bno\b.{0,45}\b(?:fee|fees|deposit|payment|charge)\b",

        r"\b(?:we\s+)?(?:do not|don't|never)\s+(?:ask|request|charge|require|collect)\b.{0,60}\b(?:pay|payment|money|fee|fees|deposit)\b",

        r"\bnot required to pay\b",

        r"\bwithout any (?:fee|fees|deposit|payment)\b",

        r"\bno upfront payment\b",

        r"\bno payment required\b"
    ]

    fee_evidence = None

    for sentence in sentences:

        clauses = re.split(
            r"\b(?:but|however|yet|although)\b",
            sentence,
            flags=re.IGNORECASE
        )

        for clause in clauses:

            has_request = sentence_has_pattern(
                clause, fee_request_patterns
            )

            is_denied = sentence_has_pattern(
                clause, fee_denial_patterns
            )

            if has_request and not is_denied:
                fee_evidence = sentence
                break

        if fee_evidence:
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
                "Verify the payment request through independently "
                "obtained official company contact details."
            )
        })

    # ------------------------------------------------
    # 7.2 SENSITIVE INFORMATION
    # ------------------------------------------------

    sensitive_patterns = [
        r"\b(?:share|send|provide|submit|enter|reveal|disclose)\b.{0,80}\b(?:passwords?|otps?|bank details|bank account details|bank account information|banking credentials|card numbers?|government id details|government-issued id|identity documents|aadhaar details)\b",

        r"\b(?:passwords?|otps?|bank details|bank account details|bank account information|banking credentials|card numbers?|government id details|government-issued id|identity documents|aadhaar details)\b.{0,60}\b(?:required|mandatory|must be provided|must be shared)\b"
    ]

    sensitive_reassurance_patterns = [
        r"\b(?:never|do not|don't)\s+(?:ask|request|collect)\b.{0,60}\b(?:passwords?|otps?|bank details|banking credentials)\b",

        r"\b(?:not required|should not|must not)\s+(?:share|send|provide)\b.{0,60}\b(?:passwords?|otps?|bank details|banking credentials)\b"
    ]

    sensitive_evidence = None

    for sentence in sentences:

        has_request = sentence_has_pattern(
            sentence, sensitive_patterns
        )

        is_reassurance = sentence_has_pattern(
            sentence, sensitive_reassurance_patterns
        )

        if has_request and not is_reassurance:
            sensitive_evidence = sentence
            break

    if sensitive_evidence:

        warnings.append({
            "title": "Sensitive information requested",
            "reason": (
                "The offer appears to request sensitive identity "
                "or financial information. Such requests deserve "
                "careful verification."
            ),
            "evidence": sensitive_evidence,
            "action": (
                "Do not share passwords, OTPs or banking credentials "
                "with recruiters. Verify any identity-document request "
                "through independently obtained official channels."
            )
        })

    # ------------------------------------------------
    # 7.3 UNUSUALLY STRONG PROMISES
    # ------------------------------------------------

    promise_patterns = [
        r"\bguaranteed\s+(?:a\s+)?(?:(?:permanent|full[- ]time|part[- ]time)\s+)?(?:job|employment|placement|position|role)\b",

        r"\bguaranteed\s+(?:job|employment|salary|income|selection)\b",

        r"\b(?:job|employment|placement|salary|income)\s+(?:is\s+)?guaranteed\b",

        r"\b100\s*%\s*guaranteed\s+(?:job|placement|selection|income|salary)\b",

        r"\bearn\b.{0,100}\b(?:with|for|in)\s+(?:just|only)\s+\d+\s+hours?\b",

        r"\b(?:make|earn)\s+(?:₹|rs\.?|inr|\$)\s*[\d,]+(?:\.\d{1,2})?.{0,100}\b(?:with|for|in)\s+(?:just|only)\s+\d+\s+hours?\b",

        r"\bearn money instantly\b",

        r"\bunlimited salary\b"
    ]

    promise_denial_patterns = [
        r"\bnot guaranteed\b",
        r"\bno guarantee\b",
        r"\bnot a guaranteed\b"
    ]

    promise_evidence = None

    for sentence in sentences:

        clauses = re.split(
            r"\b(?:but|however|yet|although)\b",
            sentence,
            flags=re.IGNORECASE
        )

        for clause in clauses:

            has_promise = sentence_has_pattern(
                clause, promise_patterns
            )

            is_denied = sentence_has_pattern(
                clause, promise_denial_patterns
            )

            if has_promise and not is_denied:
                promise_evidence = sentence
                break

        if promise_evidence:
            break

    if promise_evidence:

        warnings.append({
            "title": "Unusually strong promises",
            "reason": (
                "The offer makes unusually strong claims about "
                "guaranteed employment or high earnings for "
                "very little work. Such claims should be "
                "checked carefully."
            ),
            "evidence": promise_evidence,
            "action": (
                "Verify the compensation, working hours and "
                "employment conditions independently."
            )
        })

    # ------------------------------------------------
    # 7.4 URGENCY AND PRESSURE
    # ------------------------------------------------

    urgency_patterns = [
        r"\bonly\s+\d+\s+(?:seconds?|minutes?|hours?)\s+left\b",

        r"\b(?:apply|accept|respond|confirm|join)\s+(?:the offer\s+)?(?:immediately|right away)\b",

        r"\b(?:must|required to)\s+(?:accept|respond|confirm|join)\s+(?:the offer\s+)?(?:immediately|right away)\b",

        r"\bonly\b.{0,50}\b(?:candidates|applicants)\b.{0,50}\b(?:respond|accept|confirm|join)\b.{0,25}\b(?:immediately|right away)\b",

        r"\b(?:act|respond|confirm)\s+now\b",

        r"\blimited seats\b",

        r"\blimited time\b",

        r"\burgent payment\b",

        r"\boffer expires today\b",

        r"\b(?:lose|miss out on)\s+(?:this|the)\s+(?:opportunity|offer|position)\b",

        r"\bfirst[- ]come[- ]first[- ](?:serve|served|serve basis)\b",

        r"\bslots?\b.{0,60}\b(?:filling|fill|filled)\b.{0,60}\bfirst[- ]come\b",

        r"\b(?:last|final)\s+(?:chance|call|opportunity)\b"
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
                "The message uses urgency or limited-slot "
                "language that may pressure applicants to "
                "register before checking the opportunity."
            ),
            "evidence": urgency_evidence,
            "action": (
                "Take time to verify the organization, "
                "recruiter and opportunity before registering."
            )
        })

    # ------------------------------------------------
    # 7.5 SHORTLISTING CLAIM
    # ------------------------------------------------

    shortlist_patterns = [
        r"\byour profile has been shortlisted\b",
        r"\byou have been shortlisted\b",
        r"\byour application has been selected\b",
        r"\byou have been selected\b"
    ]

    shortlist_evidence = None

    for sentence in sentences:

        if sentence_has_pattern(sentence, shortlist_patterns):
            shortlist_evidence = sentence
            break

    if shortlist_evidence:

        selection_process_patterns = [
            r"\binterview\b",
            r"\bassessment\b",
            r"\bscreening\b",
            r"\baptitude test\b",
            r"\btechnical test\b",
            r"\bcoding test\b",
            r"\bwritten test\b"
        ]

        has_selection_details = sentence_has_pattern(
            description, selection_process_patterns
        )

        if not has_selection_details:

            warnings.append({
                "title": "Shortlisting claim needs clarification",
                "reason": (
                    "The message claims that the applicant "
                    "has been shortlisted but does not explain "
                    "the selection process."
                ),
                "evidence": shortlist_evidence,
                "action": (
                    "Confirm when and how the application was "
                    "submitted and verify the selection with "
                    "the organization independently."
                )
            })

    # ------------------------------------------------
    # 7.6 AFFILIATION AND ACCREDITATION CLAIMS
    # ------------------------------------------------

    affiliation_patterns = [
        r"\b(?:approved|recognized|recognised|authorized|authorised)\s+by\b.{0,100}\b(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM|government|government of india)\b",

        r"\b(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM)\s*[/&×-]\s*(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM)\b.{0,60}\b(?:approved|internship|program|programme)\b",

        r"\b(?:accredited|certified|endorsed)\s+by\b.{0,100}\b(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM|government)\b",

        r"\b(?:in association with|associated with|in collaboration with|official partner of|partnered with)\b.{0,100}\b(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM)\b",

        r"\b(?:IBM|AICTE|MSME|Microsoft|Adobe|NASSCOM)\s+(?:approved|accredited|certified|recognized|recognised)\b"
    ]

    affiliation_evidence = None

    for sentence in sentences:

        if sentence_has_pattern(
            sentence, affiliation_patterns
        ):
            affiliation_evidence = sentence
            break

    if affiliation_evidence:

        warnings.append({
            "title": "Unverified affiliation or accreditation claims",
            "reason": (
                "The message makes claims about approval, "
                "accreditation or association with recognized "
                "organizations. These claims have not been "
                "independently verified."
            ),
            "evidence": affiliation_evidence,
            "action": (
                "Check the claimed partnership, approval or "
                "accreditation on the relevant organization's "
                "official website."
            )
        })

    # ------------------------------------------------
    # 7.7 COMPANY AND CONTACT INFORMATION
    # ------------------------------------------------

    employer_name_mentioned = bool(employer_name)

    website_reference_mentioned = bool(
        re.search(
            r"\b(?:website|official site|careers page|careers section)\b",
            description,
            re.IGNORECASE
        )
    )

    website_url_provided = bool(contacts["urls"])
    email_provided = bool(contacts["emails"])
    phone_provided = bool(contacts["phones"])

    email_or_phone_provided = (
        email_provided or phone_provided
    )

    registration_link_mentioned = bool(
        re.search(
            r"\b(?:registration link|application link|apply here|"
            r"submit your application here|click on the below link|"
            r"registration form|application form)\b",
            description,
            re.IGNORECASE
        )
    )

    if not employer_name_mentioned:
        missing_information.append(
            "The employer's name is not clearly identified."
        )

    if not website_url_provided:
        missing_information.append(
            "A direct website or registration URL is not provided."
        )

    if not email_provided:
        missing_information.append(
            "A direct email address is not provided."
        )

    if not phone_provided:
        missing_information.append(
            "A phone number is not provided."
        )

    if not offer_details["responsibilities_provided"]:
        missing_information.append(
            "The actual job responsibilities need clarification."
        )

    # ------------------------------------------------
    # 7.8 COMPANY VERIFICATION
    # ------------------------------------------------

    company_verification = {
        "company_name_mentioned": employer_name_mentioned,
        "company_name": employer_name,

        "recruiter_name": signature["recruiter_name"],
        "recruiter_role": signature["recruiter_role"],

        "website_reference_mentioned": website_reference_mentioned,
        "website_url_provided": website_url_provided,

        "registration_link_mentioned": registration_link_mentioned,

        "email_or_phone_provided": email_or_phone_provided,
        "email_provided": email_provided,
        "phone_provided": phone_provided,

        "email": (
            contacts["emails"][0]
            if contacts["emails"] else None
        ),

        "phone": (
            contacts["phones"][0]
            if contacts["phones"] else None
        ),

        "website": (
            contacts["urls"][0]
            if contacts["urls"] else None
        ),

        "registration_link": (
            contacts["urls"][0]
            if registration_link_mentioned and contacts["urls"]
            else None
        ),

        "sender_emails": contacts["emails"],
        "provided_urls": contacts["urls"],
        "urls": contacts["urls"],

        "independent_verification": "Not performed"
    }

    # ------------------------------------------------
    # 7.9 EXTRACTED OFFER DETAILS
    # ------------------------------------------------

    extracted_details = {
        "stipend": offer_details["stipend"],
        "duration": offer_details["duration"],
        "role": offer_details["role"],
        "responsibilities_provided": (
            offer_details["responsibilities_provided"]
        )
    }

    # ------------------------------------------------
    # 7.10 VERIFICATION NOTE
    # ------------------------------------------------

    verification_note = (
        "TrustHire checks whether company and recruiter "
        "details are mentioned in the provided text. "
        "It does not independently verify company identity, "
        "website ownership, partnerships or job vacancies."
    )

    # ------------------------------------------------
    # 7.11 MACHINE LEARNING
    # ------------------------------------------------

    ml_assessment = assess_with_ml(description)

    # ------------------------------------------------
    # 7.12 REPORT STATUS
    # ------------------------------------------------

    if warnings or (
        ml_assessment["available"]
        and ml_assessment["flagged"]
    ):
        status = "Review recommended"

    elif missing_information:
        status = "More information needed"

    else:
        status = "No obvious warning signs detected"

    # ------------------------------------------------
    # 7.13 FINAL REPORT
    # ------------------------------------------------

    return {
        "status": status,
        "warning_count": len(warnings),
        "warnings": warnings,
        "missing_information": missing_information,
        "company_verification": company_verification,
        "extracted_details": extracted_details,
        "verification_note": verification_note,
        "ml_assessment": ml_assessment,

        "verification_steps": [
            "Find the organization's official website independently.",

            "Check whether the vacancy appears on its official careers page.",

            "Verify the recruiter's identity using independently obtained contact details.",

            "Verify claimed partnerships, approvals and certifications through the relevant organizations.",

            "Read the written offer and understand all payment and personal-information requests."
        ],

        "disclaimer": (
            "This is an automated preliminary review based on "
            "text patterns and a machine learning model trained "
            "on an older dataset. It cannot verify a company, "
            "partnership or job vacancy, or prove whether an "
            "opportunity is genuine or fraudulent."
        )
    }


# ==================================================
# 8. API ENDPOINT
# ==================================================

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


# ==================================================
# 9. RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)
