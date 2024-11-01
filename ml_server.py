from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)
model = joblib.load('traffic_model.joblib')  # Ensure the model file is in the same directory

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    tx_bytes = data.get('tx_bytes', 0)
    rx_bytes = data.get('rx_bytes', 0)
    prediction = model.predict([[tx_bytes, rx_bytes]])
    result = 'attack' if prediction[0] == 'attack' else 'normal'
    return jsonify({'prediction': result})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Listen on all interfaces
