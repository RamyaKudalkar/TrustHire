# TrustHire – Know Before You Apply

TrustHire is a student-focused job and internship opportunity assessment tool. It helps students identify potential warning signs, understand missing information, and learn how to verify opportunities before applying.

## Problem

Students frequently encounter job and internship offers online. Some opportunities may contain suspicious payment requests, requests for sensitive information, unrealistic promises, or pressure to accept immediately.

It can be difficult for students to identify these warning signs and know what to verify.

## Solution

TrustHire analyzes the text of a job or internship description and generates an easy-to-understand preliminary assessment.

Instead of simply labelling an opportunity as genuine or fraudulent, it explains detected warning signs, highlights missing information, and provides a verification checklist.

## Key Features

- **Warning Sign Detection:** Identifies potential upfront payment requests, sensitive information requests, urgency tactics, and unrealistic promises.
- **Evidence-Based Reports:** Displays the exact sentence that triggered a warning.
- **Context-Aware Checks:** Attempts to distinguish warning signs from reassuring statements and ordinary application information.
- **Missing Information Detection:** Highlights information such as company contact details and job responsibilities that may need clarification.
- **Company Verification Guidance:** Explains the difference between a company name being mentioned and its identity being independently verified.
- **Verification Checklist:** Provides practical steps students can follow before accepting an opportunity.
- **Privacy-Conscious Design:** Submitted descriptions are not stored by the MVP.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python |
| Web Framework | Flask |
| Analysis | Rule-based text analysis |

## Project Structure

```text
TrustHire/
├── frontend/
│   ├── index.html
│   ├── analyzer.html
│   ├── style.css
│   └── script.js
├── backend/
│   └── app.py
├── .gitignore
└── README.md
```

Note: The local virtual environment (`venv/`) and `.env` file are excluded from version control.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/RamyaKudalkar/TrustHire.git
cd TrustHire
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Flask

```bash
pip install flask
```

### 5. Run the application

```bash
python backend/app.py
```

### 6. Open TrustHire

Visit:

http://127.0.0.1:5000

Keep the backend terminal running while using the application.

## How It Works

1. Open TrustHire and navigate to the analyzer.
2. Paste a job or internship description into the text area.
3. TrustHire checks the description for potential warning signs.
4. The backend prepares a preliminary assessment.
5. The frontend displays detected warnings, supporting evidence, missing information, and verification steps.
6. Use the report to understand what needs further checking.

## Important Limitations

- TrustHire provides an automated preliminary assessment, not a final fraud verdict.
- It does not independently verify companies, recruiters, websites, or vacancies.
- No detected warning signs do not guarantee that an opportunity is genuine.
- Text-based rules may miss some warning signs or identify patterns that need human review.
- Students should independently verify opportunities before sharing personal information or making payments.

## Future Improvements

- Improve detection using more advanced language-processing techniques.
- Expand warning-sign patterns and context handling.
- Add support for more languages.
- Improve report explanations and verification guidance.

## Project Goal

To help students make more informed decisions about job and internship opportunities through transparent, explainable, and accessible risk assessment.

**TrustHire – Know Before You Apply.**