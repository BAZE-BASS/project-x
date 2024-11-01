from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import pandas as pd

# Load the labeled data
data = pd.read_csv('labeled_traffic_data.csv')
X = data[['tx_bytes', 'rx_bytes']]  # Features
y = data['label']  # Labels

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
clf = DecisionTreeClassifier(max_depth=5, random_state=42)
clf.fit(X_train, y_train)

# Evaluate the model
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print("Model Accuracy:", accuracy)
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the trained model
joblib.dump(clf, 'traffic_model.joblib')
print("Model saved as 'traffic_model.joblib'")
