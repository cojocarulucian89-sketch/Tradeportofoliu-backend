from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Demo portfolio data
DEMO_PORTFOLIO = [
    {"symbol": "AAPL", "shares": 50, "value": 8750.00},
    {"symbol": "GOOGL", "shares": 30, "value": 4200.00},
    {"symbol": "MSFT", "shares": 40, "value": 11200.00},
    {"symbol": "AMZN", "shares": 20, "value": 2800.00},
    {"symbol": "TSLA", "shares": 25, "value": 4375.00}
]

@app.route('/')
def home():
    return jsonify({"status": "NEWTRADE Pro AI Sentinel API - Running"})

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    return jsonify(DEMO_PORTFOLIO)

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio():
    # Return optimized demo data
    optimized = [
        {"symbol": "AAPL", "shares": 55, "value": 9625.00},
        {"symbol": "GOOGL", "shares": 35, "value": 4900.00},
        {"symbol": "MSFT", "shares": 45, "value": 12600.00},
        {"symbol": "AMZN", "shares": 22, "value": 3080.00},
        {"symbol": "TSLA", "shares": 28, "value": 4900.00}
    ]
    return jsonify(optimized)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
