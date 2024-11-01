const express = require('express');
const axios = require('axios');
const app = express();
const PORT = 3000;

app.use(express.json());

// Endpoint to receive traffic data and get prediction
app.post('/classify-traffic', async (req, res) => {
    const { tx_bytes, rx_bytes } = req.body;

    try {
        // Send data to Flask server
        const response = await axios.post('http://localhost:5000/predict', {
            tx_bytes,
            rx_bytes
        });

        // Respond with the classification result
        res.json({ prediction: response.data.prediction });
    } catch (error) {
        console.error('Error communicating with ML server:', error.message);
        res.status(500).json({ error: 'Failed to classify traffic' });
    }
});

app.listen(PORT, () => {
    console.log(`Node server running on http://localhost:${PORT}`);
});
