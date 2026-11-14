
import pandas as pd
import joblib
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "dataset" / "scamshield"
BACKEND_DIR = BASE_DIR / "backend"

print("Loading ScamShield dataset...")

train_df = pd.read_csv(DATA_DIR / "train.csv")
val_df = pd.read_csv(DATA_DIR / "validation.csv")
test_df = pd.read_csv(DATA_DIR / "test.csv")

# Use job-related records only.
train_df = train_df[train_df["source"] == "job"].copy()
val_df = val_df[val_df["source"] == "job"].copy()
test_df = test_df[test_df["source"] == "job"].copy()

# Prepare text and labels.
def prepare_data(df):
    X = df["text"].fillna("").astype(str)
    y = df["label"].astype(int)
    return X, y

X_train, y_train = prepare_data(train_df)
X_val, y_val = prepare_data(val_df)
X_test, y_test = prepare_data(test_df)

print("\nDATA SPLIT")
print("Training records:", len(X_train))
print("Validation records:", len(X_val))
print("Testing records:", len(X_test))

print("\nFraudulent records:")
print("Training:", int(y_train.sum()))
print("Validation:", int(y_val.sum()))
print("Testing:", int(y_test.sum()))

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        stop_words="english",
        max_features=100000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True
    )),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    ))
])

print("\nTraining TrustHire candidate model...")
model.fit(X_train, y_train)

# Choose threshold using validation data only.
val_scores = model.predict_proba(X_val)[:, 1]

precision, recall, thresholds = precision_recall_curve(
    y_val,
    val_scores
)

f1_scores = (
    2 * precision[:-1] * recall[:-1] /
    (precision[:-1] + recall[:-1] + 1e-10)
)

best_index = f1_scores.argmax()
best_threshold = float(thresholds[best_index])

print("\nBEST VALIDATION RESULTS")
print("Threshold:", round(best_threshold, 4))
print("Validation F1:", round(f1_scores[best_index], 4))

# Evaluate once on the untouched test split.
test_scores = model.predict_proba(X_test)[:, 1]
predictions = (test_scores >= best_threshold).astype(int)

print("\nFINAL TEST RESULTS")
print(classification_report(
    y_test,
    predictions,
    target_names=["Legitimate", "Fraudulent"],
    zero_division=0
))

print("Confusion Matrix:")
print(confusion_matrix(y_test, predictions))

# Save as candidate files. Do not overwrite the current model.
joblib.dump(
    model,
    BACKEND_DIR / "trusthire_model_candidate.joblib"
)

(BACKEND_DIR / "trusthire_threshold_candidate.txt").write_text(
    str(best_threshold)
)

print("\nCandidate model and threshold saved successfully.")
print("Existing TrustHire model has NOT been changed.")
