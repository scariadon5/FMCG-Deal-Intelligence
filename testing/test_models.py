import joblib

# Load saved objects
model = joblib.load("models/relevance_classifier.pkl")
vectorizer = joblib.load("models/tfidf_vectorizer.pkl")

print("=" * 60)
print("FMCG Relevance Classifier")
print("Type 'exit' to quit.")
print("=" * 60)

while True:
    headline = input("\nEnter Headline: ")

    if headline.lower() == "exit":
        break

    # Convert headline into TF-IDF vector
    x = vectorizer.transform([headline])

    # Probability that headline is relevant
    probability = model.predict_proba(x)[0][1]

    # Final prediction
    prediction = model.predict(x)[0]

    print("-" * 50)
    print("Prediction :", "Relevant ✅" if prediction else "Not Relevant ❌")
    print(f"Confidence : {probability:.4f}")