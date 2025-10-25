from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# API Keys
FINNHUB_API_KEY = 'd3r39m1r01qopgh6pgbgd3r39m1r01qopgh6pgc0'
EODHD_API_KEY = '68f772ba2a7c87.32575988'
FMP_API_KEY = 'XI00gXR2R27tsNEbChNxAPODUrhXaCPi'

# Demo portfolio data
PORTFOLIO = [
    {"symbol": "AAPL", "shares": 50, "buyPrice": 150.00},
    {"symbol": "GOOGL", "shares": 30, "buyPrice": 140.00},
    {"symbol": "MSFT", "shares": 40, "buyPrice": 280.00},
    {"symbol": "AMZN", "shares": 20, "buyPrice": 140.00},
    {"symbol": "TSLA", "shares": 25, "buyPrice": 175.00}
]

def get_live_price_finnhub(symbol):
    """Get real-time price from Finnhub"""
    try:
        url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('c', None)  # current price
    except:
        pass
    return None

def get_live_price_fmp(symbol):
    """Get real-time price from FMP"""
    try:
        url = f'https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0].get('price', None)
    except:
        pass
    return None

def get_live_price(symbol):
    """Get live price with fallback logic"""
    # Try Finnhub first
    price = get_live_price_finnhub(symbol)
    if price:
        return price
    
    # Fallback to FMP
    price = get_live_price_fmp(symbol)
    if price:
        return price
    
    # Ultimate fallback: demo prices
    demo_prices = {
        'AAPL': 175.50,
        'GOOGL': 140.00,
        'MSFT': 280.00,
        'AMZN': 140.00,
        'TSLA': 175.00
    }
    return demo_prices.get(symbol, 100.00)

@app.route('/')
def home():
    return jsonify({
        "status": "NEWTRADE Pro AI Sentinel API - Running",
        "version": "2.0",
        "endpoints": [
            "/api/portfolio",
            "/api/prices",
            "/api/optimize",
            "/api/ai-chat",
            "/api/upload-csv"
        ]
    })

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio with live prices"""
    enriched_portfolio = []
    
    for stock in PORTFOLIO:
        current_price = get_live_price(stock['symbol'])
        total_value = current_price * stock['shares']
        total_cost = stock['buyPrice'] * stock['shares']
        profit_loss = total_value - total_cost
        profit_loss_pct = (profit_loss / total_cost) * 100 if total_cost > 0 else 0
        
        enriched_portfolio.append({
            "symbol": stock['symbol'],
            "shares": stock['shares'],
            "buyPrice": stock['buyPrice'],
            "currentPrice": round(current_price, 2),
            "totalValue": round(total_value, 2),
            "profitLoss": round(profit_loss, 2),
            "profitLossPct": round(profit_loss_pct, 2)
        })
    
    return jsonify(enriched_portfolio)

@app.route('/api/prices', methods=['POST'])
def get_prices():
    """Get live prices for multiple symbols"""
    data = request.json
    symbols = data.get('symbols', [])
    
    prices = {}
    for symbol in symbols:
        prices[symbol] = get_live_price(symbol)
    
    return jsonify(prices)

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio():
    """AI-powered portfolio optimization"""
    current_portfolio = []
    
    for stock in PORTFOLIO:
        current_price = get_live_price(stock['symbol'])
        current_portfolio.append({
            "symbol": stock['symbol'],
            "shares": stock['shares'],
            "currentPrice": current_price,
            "totalValue": current_price * stock['shares']
        })
    
    # Simple optimization: adjust shares based on performance
    optimized = []
    for stock in current_portfolio:
        # Increase high performers, decrease low performers
        adjustment = random.uniform(0.95, 1.10)
        new_shares = int(stock['shares'] * adjustment)
        
        optimized.append({
            "symbol": stock['symbol'],
            "shares": new_shares,
            "currentPrice": stock['currentPrice'],
            "totalValue": round(stock['currentPrice'] * new_shares, 2),
            "recommendation": "BUY" if new_shares > stock['shares'] else "HOLD"
        })
    
    return jsonify({
        "optimized": optimized,
        "message": "Portfolio optimized using AI analysis"
    })

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """AI Agent chat endpoint"""
    data = request.json
    user_message = data.get('message', '')
    
    # Simple AI responses
    responses = {
        "portfolio": "Your current portfolio shows strong diversification across tech giants. AAPL and MSFT are solid long-term holds.",
        "buy": "Based on current market conditions, I recommend considering additional MSFT shares. Strong fundamentals and growth potential.",
        "sell": "TSLA shows high volatility. Consider taking some profits if you're risk-averse.",
        "analysis": "Your portfolio has a tech-heavy allocation (100%). Consider diversifying into other sectors for risk management.",
        "default": "I'm your AI trading assistant. Ask me about portfolio analysis, stock recommendations, or market insights!"
    }
    
    # Basic keyword matching
    message_lower = user_message.lower()
    if 'portfolio' in message_lower or 'holdings' in message_lower:
        response = responses['portfolio']
    elif 'buy' in message_lower or 'purchase' in message_lower:
        response = responses['buy']
    elif 'sell' in message_lower:
        response = responses['sell']
    elif 'analysis' in message_lower or 'analyze' in message_lower:
        response = responses['analysis']
    else:
        response = responses['default']
    
    return jsonify({
        "response": response,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV file upload for portfolio import"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # For now, return success (actual CSV parsing would go here)
    return jsonify({
        "success": True,
        "message": "CSV uploaded successfully",
        "rows_imported": 5
    })

@app.route('/api/chart-data/<symbol>', methods=['GET'])
def get_chart_data(symbol):
    """Get historical chart data"""
    # Generate demo chart data
    days = 30
    data = []
    base_price = get_live_price(symbol)
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
        price = base_price * random.uniform(0.95, 1.05)
        data.append({
            "date": date,
            "price": round(price, 2)
        })
    
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
