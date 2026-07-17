"""
train_classifier.py

Stage-1 relevance classifier: TF-IDF + Logistic Regression.
Distinguishes "FMCG deal" text from everything else (business_negative + general_negative).

Run: python src/training/train_classifier.py
"""

import os
import pandas as pd
import joblib
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

DATA_PATH = "data/labeled/training_data.csv"
MODEL_DIR = "models"
MODEL_PATH = f"{MODEL_DIR}/relevance_classifier.pkl"
VECTORIZER_PATH = f"{MODEL_DIR}/tfidf_vectorizer.pkl"

# TF-IDF settings
MAX_FEATURES = 5000
NGRAM_RANGE = (1, 2)  # unigrams + bigrams, e.g. catches "joint venture" as one feature

# Logistic Regression settings
C_VALUE = 1.0
CLASS_WEIGHT = "balanced"  # critical given ~18:1 negative:positive imbalance


def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str)
    # Binary target: 1 = fmcg_deal_positive, 0 = everything else
    df["target"] = (df["label"] == "fmcg_deal_positive").astype(int)
    return df


def train_and_evaluate():
    df = load_data()
    print(f"Total rows: {len(df)}")
    print(f"Positive: {df['target'].sum()}  Negative: {(df['target'] == 0).sum()}")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["target"],
        test_size=0.2,
        random_state=42,
        stratify=df["target"],  # keeps the same pos/neg ratio in both splits
    )

    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        ngram_range=NGRAM_RANGE,
        stop_words="english",
        lowercase=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(
        C=C_VALUE,
        class_weight=CLASS_WEIGHT,
        max_iter=1000,
        random_state=42,
    )
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    report = classification_report(y_test, y_pred, target_names=["not_relevant", "fmcg_deal"], output_dict=True)
    report_text = classification_report(y_test, y_pred, target_names=["not_relevant", "fmcg_deal"])
    cm = confusion_matrix(y_test, y_pred)

    print("\n=== Classification Report ===")
    print(report_text)
    print("=== Confusion Matrix ===")
    print("           pred_neg  pred_pos")
    print(f"actual_neg   {cm[0][0]:>6}    {cm[0][1]:>6}")
    print(f"actual_pos   {cm[1][0]:>6}    {cm[1][1]:>6}")

    # --- MLflow logging ---
    mlflow.set_experiment("fmcg-relevance-classifier")
    with mlflow.start_run():
        mlflow.log_param("max_features", MAX_FEATURES)
        mlflow.log_param("ngram_range", str(NGRAM_RANGE))
        mlflow.log_param("C", C_VALUE)
        mlflow.log_param("class_weight", CLASS_WEIGHT)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))

        mlflow.log_metric("precision_positive", report["fmcg_deal"]["precision"])
        mlflow.log_metric("recall_positive", report["fmcg_deal"]["recall"])
        mlflow.log_metric("f1_positive", report["fmcg_deal"]["f1-score"])
        mlflow.log_metric("accuracy", report["accuracy"])

        mlflow.sklearn.log_model(model, "model")

    # --- Save artifacts for the live pipeline to use ---
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved vectorizer to {VECTORIZER_PATH}")


if __name__ == "__main__":
    train_and_evaluate()