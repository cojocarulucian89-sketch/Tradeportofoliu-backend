from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import io

app = Flask(__name__)
CORS(app)

# Global portfolio storage (in-memory for now)
portfolio_data = []

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "version": "2.0",
        "message": "NEWTRADE Pro AI Sentinel Backend",
        "endpoints": ["/api/portfolio", "/api/upload-csv", "/api/stock/<symbol>", "/api/optimize"]
    })

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Return current portfolio with live prices"""
    if not portfolio_data:
        return jsonify([])
    
    enriched_portfolio = []
    
    for holding in portfolio_data:
        try:
            symbol = holding['symbol']
            shares = float(holding['shares'])
            buy_price = float(holding['buyPrice'])
            
            # Fetch live price
            stock = yf.Ticker(symbol)
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
            
            if current_price == 0:
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Calculate metrics
            total_cost = shares * buy_price
            current_value = shares * current_price
            profit_loss = current_value - total_cost
            profit_loss_pct = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
            
            # Get historical data for chart
            hist = stock.history(period='1mo')
            chart_data = []
            if not hist.empty:
                chart_data = [
                    {"date": str(date.date()), "price": float(price)}
                    for date, price in hist['Close'].items()
                ]
            
            enriched_portfolio.append({
                "symbol": symbol,
                "shares": shares,
                "buyPrice": buy_price,
                "currentPrice": current_price,
                "totalCost": total_cost,
                "currentValue": current_value,
                "profitLoss": profit_loss,
                "profitLossPct": profit_loss_pct,
                "chartData": chart_data[-30:]  # Last 30 days
            })
            
        except Exception as e:
            print(f"Error processing {holding['symbol']}: {e}")
            continue
    
    return jsonify(enriched_portfolio)

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Process uploaded CSV file and update portfolio"""
    global portfolio_data
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        # Read CSV
        content = file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        
        # Expected columns: symbol, shares, buyPrice
        required_columns = ['symbol', 'shares', 'buyPrice']
        
        # Try alternative column names
        column_mapping = {
            'ticker': 'symbol',
            'stock': 'symbol',
            'quantity': 'shares',
            'qty': 'shares',
            'amount': 'shares',
            'price': 'buyPrice',
            'cost': 'buyPrice',
            'buy_price': 'buyPrice',
            'purchase_price': 'buyPrice'
        }
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Rename columns if needed
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)
        
        # Check if required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing_columns)}",
                "found_columns": list(df.columns),
                "required_columns": required_columns
            }), 400
        
        # Clean and validate data
        df = df[required_columns].dropna()
        df['symbol'] = df['symbol'].str.upper().str.strip()
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
        df['buyPrice'] = pd.to_numeric(df['buyPrice'], errors='coerce')
        df = df.dropna()
        
        # Update global portfolio
        portfolio_data = df.to_dict('records')
        
        return jsonify({
            "success": True,
            "message": f"Successfully loaded {len(portfolio_data)} holdings",
            "holdings": len(portfolio_data)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    """Get detailed information for a single stock"""
    try:
        stock = yf.Ticker(symbol.upper())
        info = stock.info
        hist = stock.history(period='6mo')
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        
        if current_price == 0 and not hist.empty:
            current_price = hist['Close'].iloc[-1]
        
        # Chart data
        chart_data = []
        if not hist.empty:
            chart_data = [
                {"date": str(date.date()), "price": float(price)}
                for date, price in hist['Close'].items()
            ]
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('longName', symbol),
            "currentPrice": current_price,
            "previousClose": info.get('previousClose', 0),
            "dayHigh": info.get('dayHigh', 0),
            "dayLow": info.get('dayLow', 0),
            "yearHigh": info.get('fiftyTwoWeekHigh', 0),
            "yearLow": info.get('fiftyTwoWeekLow', 0),
            "volume": info.get('volume', 0),
            "marketCap": info.get('marketCap', 0),
            "chartData": chart_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio():
    """AI-powered portfolio optimization"""
    try:
        # Get current portfolio
        if not portfolio_data:
            return jsonify({"error": "No portfolio data available"}), 400
        
        # Simple optimization: identify underperformers and overperformers
        analysis = []
        
        for holding in portfolio_data:
            try:
                symbol = holding['symbol']
                stock = yf.Ticker(symbol)
                info = stock.info
                
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                buy_price = float(holding['buyPrice'])
                
                if current_price > 0 and buy_price > 0:
                    performance = ((current_price - buy_price) / buy_price) * 100
                    
                    recommendation = "HOLD"
                    if performance > 20:
                        recommendation = "STRONG PERFORMER - Consider taking profits"
                    elif performance < -10:
                        recommendation = "UNDERPERFORMER - Review position"
                    elif performance > 10:
                        recommendation = "GOOD PERFORMER - Hold"
                    
                    analysis.append({
                        "symbol": symbol,
                        "performance": round(performance, 2),
                        "recommendation": recommendation
                    })
            except:
                continue
        
        return jsonify({
            "success": True,
            "message": "Portfolio optimization complete",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
