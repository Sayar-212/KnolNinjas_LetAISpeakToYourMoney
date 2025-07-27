import yfinance as yf
from twelvedata import TDClient
import os
import requests
from dotenv import load_dotenv

load_dotenv()
# Setup API key
TD_API_KEY = os.getenv("TD_API_KEY")
if TD_API_KEY is None:
    raise ValueError("TD_API_KEY is not set")

FMP_API_KEY = os.getenv("FMP_API_KEY")
if FMP_API_KEY is None:
    raise ValueError("FMP_API_KEY is not set")

td = TDClient(apikey=TD_API_KEY)

def fetch_from_twelvedata(ticker: str) -> dict:
    """Try getting data from Twelve Data API"""
    try:
        df = td.time_series(symbol=ticker, interval="1day", outputsize=180).as_pandas()

        if df.empty:
            return None

        volatility = df["close"].pct_change().std()

        return {
            "source": "TwelveData",
            "price": round(df["close"].iloc[-1], 2),
            "volatility": round(volatility, 4),
            "history": {str(date.date()): round(price, 2) for date, price in df["close"].tail(5).items()},
        }

    except Exception:
        return None


def fetch_from_yfinance(ticker: str) -> dict:
    """Fallback to yfinance for basic data"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="6mo")

        if history.empty:
            return None

        volatility = history["Close"].pct_change().std()

        return {
            "source": "yfinance",
            "price": info.get("currentPrice"),
            "pe_ratio": info.get("trailingPE"),
            "beta": info.get("beta"),
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "volatility": round(volatility, 4),
            "history": history["Close"].tail(5).to_dict(),
        }

    except Exception:
        return None

def fetch_from_fmp(ticker: str) -> dict:
    """Final fallback using FMP for price and basic fundamentals"""
    try:
        base_url = "https://financialmodelingprep.com/api/v3"
        quote_resp = requests.get(f"{base_url}/quote/{ticker}?apikey={FMP_API_KEY}")
        profile_resp = requests.get(f"{base_url}/profile/{ticker}?apikey={FMP_API_KEY}")
        hist_resp = requests.get(f"{base_url}/historical-price-full/{ticker}?serietype=line&timeseries=5&apikey={FMP_API_KEY}")

        if quote_resp.status_code != 200 or profile_resp.status_code != 200:
            return None

        quote = quote_resp.json()[0] if quote_resp.json() else None
        profile = profile_resp.json()[0] if profile_resp.json() else None
        history = hist_resp.json().get("historical", []) if hist_resp.status_code == 200 else []

        if not quote or not profile:
            return None

        history_data = {h["date"]: round(h["close"], 2) for h in history}

        return {
            "source": "FMP",
            "price": quote.get("price"),
            "pe_ratio": quote.get("pe"),
            "beta": profile.get("beta"),
            "market_cap": quote.get("marketCap"),
            "dividend_yield": profile.get("lastDiv") or 0.0,
            "sector": profile.get("sector"),
            "volatility": None,  # Optional: Can compute if more data is fetched
            "history": history_data,
        }
    except Exception:
        return None

def get_global_stock_risk_data(ticker: str) -> dict:
    """
    Fetches historical and fundamental stock data for a given ticker symbol.

    Use this tool when you need data to analyze a stock's risk or performance.
    It provides information such as:
    - Current price
    - Volatility (based on recent price changes)
    - PE ratio, beta, market cap, dividend yield, and sector (if available)
    - Recent closing prices

    It automatically selects the best available data source and works globally across most listed stocks.
    """
    print(f"Fetching risk data for: {ticker}")

    # Try Twelve Data first
    data = fetch_from_twelvedata(ticker)
    if data:
        print("Fetched from Twelve Data")
        return {"status": "success", "ticker": ticker, **data}

    # Fallback to yfinance
    data = fetch_from_yfinance(ticker)
    if data:
        print("Fetched from yfinance")
        return {"status": "success", "ticker": ticker, **data}

    data = fetch_from_fmp(ticker)
    if data:
        print("Data from FMP")
        return {"status": "success", "ticker": ticker, **data}

    return {
        "status": "error",
        "ticker": ticker,
        "error_message": "Unable to retrieve data from Twelve Data or yfinance. The stock may be delisted or unsupported.",
    }
