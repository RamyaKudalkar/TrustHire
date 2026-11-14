
# TrustHire – Know Before You Apply

TrustHire is a student-focused job and internship opportunity assessment tool that helps students identify potential warning signs before applying.

It analyzes pasted job and internship offer messages or descriptions using rule-based text analysis and a Machine Learning model. It generates an understandable report highlighting possible warning signs, supporting evidence, missing information, and practical verification steps.

TrustHire does not label opportunities as definitively genuine or fraudulent. Its purpose is to help students make more informed decisions.

## Problem

Students frequently encounter job and internship opportunities online. Some offers may contain suspicious payment requests, requests for sensitive information, unrealistic promises, or pressure to accept immediately.

Identifying these warning signs and knowing what to verify can be challenging, especially for students applying for their first opportunities.

## Solution

TrustHire provides a preliminary assessment of pasted job and internship offer messages or descriptions.

It combines rule-based detection with Machine Learning to:

- Identify potential warning signs.
- Highlight sentences that triggered rule-based warnings.
- Identify information that may need clarification.
- Provide company verification guidance.
- Generate a practical verification checklist.

The report explains why an opportunity may need further review instead of simply displaying a genuine or fraudulent label.

## Key Features

- **Warning Sign Detection:** Identifies potential upfront payment requests, sensitive information requests, urgency tactics, and unusually strong promises.
- **Evidence-Based Reports:** Displays the original text evidence associated with detected rule-based warnings.
- **Context-Aware Checks:** Attempts to distinguish warning signs from reassuring statements and ordinary application information.
- **Machine Learning Assessment:** Uses a TF-IDF and Logistic Regression model to identify patterns similar to fraudulent job postings in its training dataset.
- **Missing Information Detection:** Highlights details such as employer identity and direct contact information that may need clarification.
- **Company Verification Guidance:** Distinguishes between company details mentioned in an offer and details independently verified.
- **Verification Checklist:** Provides practical steps students can follow before proceeding with an opportunity.
- **Privacy-Conscious Design:** The MVP does not intentionally store submitted job descriptions.
- **Input Validation:** Validates submitted descriptions and enforces a maximum input length of 10,000 characters.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python |
| Web Framework | Flask |
| Rule-Based Analysis | Python, Regular Expressions |
| Text Processing | TF-IDF |
| Machine Learning | Logistic Regression |
| Model Storage | Joblib |
| Active Model Dataset | Fake Job Postings Dataset |

## How It Works

1. The user opens TrustHire and navigates to the analyzer.
2. The user pastes a job or internship offer message or description.
3. The Flask backend validates the submitted text.
4. Rule-based checks examine the description for potential warning signs.
5. The Machine Learning model evaluates patterns in the submitted text.
6. The backend combines the results into a preliminary assessment.
7. The frontend displays warnings, evidence, missing information, the ML assessment, and verification guidance.

The overall report recommends further review when rule-based detection identifies warnings. The ML assessment is presented separately and does not override the rule-based findings.

## Project Structure

```text
TrustHire/
├── frontend/
│   ├── index.html
│   ├── analyzer.html
│   ├── style.css
│   └── script.js
│
├── backend/
│   ├── app.py
│   ├── train_model.py
│   ├── trusthire_model.joblib
│   └── trusthire_threshold.txt
│
├── dataset/
│   ├── fake_job_postings.csv
│   └── scamshield/
│       ├── train.csv
│       ├── validation.csv
│       └── test.csv
│
├── .gitignore
└── README.md
```

**Notes:**

- The virtual environment and Python cache files are excluded from version control.
- Dataset files may be kept locally rather than committed to the repository.
- The active model and threshold files are required for the ML assessment.
- The ScamShield CSV files are used by the training script for a separate candidate-model experiment. They are not loaded by the live application.
- Candidate model files are experimental outputs and are not included in the current project structure.

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

### 4. Install dependencies

```bash
pip install flask joblib scikit-learn pandas
```

### 5. Run the application

```bash
python backend/app.py
```

### 6. Open TrustHire

Visit:

http://127.0.0.1:5000

Keep the backend terminal running while using the application.

**Important:** The active model files must be present in the `backend/` directory for Machine Learning assessment to work.

## Machine Learning Model

The active TrustHire model uses:

- TF-IDF for text feature extraction.
- Logistic Regression for classification.
- A classification threshold selected during validation.

The active model was trained using the Fake Job Postings dataset, which contains job postings labelled as legitimate or fraudulent.

The application loads the following files:

- `backend/trusthire_model.joblib`
- `backend/trusthire_threshold.txt`

The application uses the model to produce an additional assessment alongside its rule-based analysis.

## Model Evaluation

The active model was evaluated using a held-out test split with duplicate-aware grouping to reduce data leakage from repeated postings.

| Metric | Fraudulent Class |
|---|---:|
| Precision | 0.80 |
| Recall | 0.83 |
| F1-score | 0.81 |

The test split contained 173 fraudulent examples.

- Correctly identified: 144
- Missed: 29

These results describe performance on the selected dataset split. They do not represent guaranteed performance on real-world messages, newly created scams, or every type of job opportunity.

## Candidate Model Experiment

An additional candidate model was trained using job-related records from the ScamShield dataset.

The candidate training pipeline:

- Uses job-related records rather than SMS records.
- Uses TF-IDF and Logistic Regression.
- Selects a classification threshold using validation data.
- Evaluates performance on a separate test split.
- Saves candidate files without overwriting the active model.

The candidate model is not currently used by the Flask application.

Its results are experimental and should not be interpreted as proof of improved real-world detection.

To rerun this experiment, the three ScamShield CSV files must be available in `dataset/scamshield/`. Running `train_model.py` generates candidate model and threshold files; these are not used by the current Flask application.

## Important Limitations

- TrustHire provides an automated preliminary assessment, not a final fraud verdict.
- It does not independently verify companies, recruiters, websites, or vacancies.
- No detected warning signs do not guarantee that an opportunity is genuine.
- The active Machine Learning model was trained on an older dataset and may not recognize newer scam patterns.
- The available benchmark data primarily contains job-board postings, which may differ from short recruitment messages and emails.
- Text-based rules may miss warning signs or identify patterns that require human review.
- The model's assessment is not proof that an opportunity is fraudulent.
- Students should independently verify opportunities before sharing sensitive information or making payments.

## Future Improvements

- Improve detection using more advanced natural language processing techniques.
- Expand warning-sign patterns and context handling.
- Train and evaluate models using more diverse and recent datasets.
- Add support for additional languages.
- Improve report explanations and verification guidance.
- Explore independent company and website verification capabilities.

## Project Goal

To help students make more informed decisions about job and internship opportunities through transparent, explainable, and accessible risk assessment.

**TrustHire – Know Before You Apply.**
