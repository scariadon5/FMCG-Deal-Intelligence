import joblib

model = joblib.load("models/relevance_classifier.pkl")
vectorizer = joblib.load("models/tfidf_vectorizer.pkl")

while True:
    headline = input("\nHeadline: ")

    x = vectorizer.transform([headline])

    probability = model.predict_proba(x)[0][1]
    prediction = model.predict(x)[0]

    print(f"\nPrediction : {'Relevant' if prediction else 'Not Relevant'}")
    print(f"Probability: {probability:.4f}")