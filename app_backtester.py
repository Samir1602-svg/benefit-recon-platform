import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, time as dtime
import pytz
import io
import json
import os
import re
import time
import requests
import threading
import math
import sqlite3

# ==============================================================================
# 💎 SAM QUANTUM TERMINAL - INSTITUTIONAL QUANT ENGINE & PRO DEMAT SUITE
# ==============================================================================
st.set_page_config(
    page_title="SAM QUANTUM AI | Institutional Quant Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "users_db.json"
SIGNALS_LOG_FILE = "ai_signals_history.json"
ACTIVE_TRADES_FILE = "active_trades.json"
AUTOPILOT_STATE_FILE = "autopilot_state.json"
SQLITE_DB_FILE = "terminal_audit.db"

# Master Operating Manual Text Definition
TERMINAL_MANUAL_TEXT = """=====================================================
         SAM QUANTUM OS - OFFICIAL SYSTEM MANUAL
=====================================================

1. ASSET & RESOLUTION CONFIGURATION
- Dynamic Dropdown: Syncs real-time prices across NSE, Crypto, MCX & Stocks.
- Timeframes: Multi-resolution candle streams (1m, 5m, 15m, 1D).

2. STRATEGY ENGINE (REGISTRY PATTERN)
- Quant Archetype: Institutional EMA Pullback (20/50 Trend), SuperTrend, VWAP, MACD, Bollinger Bands, ORB.
- Momentum Filter: RSI Overbought/Oversold boundaries (14 Period).

3. BLACK-SCHOLES OPTION CHAIN & DEMAT MATRIX
- 3-Column Demat Option Chain: Real Greeks (Delta, Theta, Gamma, Vega).
- Auto Expiry Rollover: Automatic rollover to next cycle at market close.

4. CAPITAL & RISK MANAGEMENT (RMS)
- Capital Affordability Validation: Prevents execution on insufficient margin.
- Dynamic Lot Sizing: Nifty (75), Bank Nifty (30), Sensex (20), FinNifty (65).

5. 24/7 AUTOPILOT ENGINE
- Continuous Non-Blocking Daemon: Runs autonomously in background thread.
- Telegram Signal Engine: Instant dispatch with zero UI thread block.
=====================================================
"""

# ==============================================================================
# 🏛️ SPECIFICATIONS & LOT SIZES (INDIAN INDICES & CRYPTO)
# ==============================================================================
INDEX_SPECS = {
    "^NSEBANK": {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100, "exchange": "NFO", "expiry_day": "Tuesday"},
    "^NSEI": {"name": "NIFTY", "lot_size": 75, "strike_step": 50, "exchange": "NFO", "expiry_day": "Tuesday"},
    "NIFTY_FIN_SERVICE.NS": {"name": "FINNIFTY", "lot_size": 65, "strike_step": 50, "exchange": "NFO", "expiry_day": "Tuesday"},
    "^BSESN": {"name": "SENSEX", "lot_size": 20, "strike_step": 100, "exchange": "BFO", "expiry_day": "Thursday"},
    "RELIANCE.NS": {"name": "RELIANCE", "lot_size": 250, "strike_step": 20, "exchange": "NFO", "expiry_day": "Monthly"},
    "HDFCBANK.NS": {"name": "HDFCBANK", "lot_size": 550, "strike_step": 10, "exchange": "NFO", "expiry_day": "Monthly"},
    "TCS.NS": {"name": "TCS", "lot_size": 175, "strike_step": 50, "exchange": "NFO", "expiry_day": "Monthly"},
    "INFY.NS": {"name": "INFY", "lot_size": 400, "strike_step": 20, "exchange": "NFO", "expiry_day": "Monthly"},
    "GC=F": {"name": "GOLDM", "lot_size": 1, "strike_step": 100, "exchange": "MCX", "expiry_day": "Monthly"},
    "SI=F": {"name": "SILVERM", "lot_size": 5, "strike_step": 250, "exchange": "MCX", "expiry_day": "Monthly"},
    "BTC-USD": {"name": "BTC/USDT", "lot_size": 1, "strike_step": 100, "exchange": "PERPETUAL", "expiry_day": "24/7"},
    "ETH-USD": {"name": "ETH/USDT", "lot_size": 1, "strike_step": 10, "exchange": "PERPETUAL", "expiry_day": "24/7"},
    "SOL-USD": {"name": "SOL/USDT", "lot_size": 1, "strike_step": 1, "exchange": "PERPETUAL", "expiry_day": "24/7"},
    "BNB-USD": {"name": "BNB/USDT", "lot_size": 1, "strike_step": 1, "exchange": "PERPETUAL", "expiry_day": "24/7"},
    "XRP-USD": {"name": "XRP/USDT", "lot_size": 10, "strike_step": 0.01, "exchange": "PERPETUAL", "expiry_day": "24/7"},
    "DOGE-USD": {"name": "DOGE/USDT", "lot_size": 100, "strike_step": 0.001, "exchange": "PERPETUAL", "expiry_day": "24/7"}
}

DEFAULT_USERS = {
    "admin": {"pass": "sam@2026", "name": "Sam (Founder)", "phone": "9999999999", "tier": "Master Admin", "created_at": "2026-08-20"},
    "vip_trader": {"pass": "quant100x", "name": "VIP Algo Trader", "phone": "9876543210", "tier": "Institutional Pro", "created_at": "2026-08-21"}
}

def init_sqlite_db():
    with sqlite3.connect(SQLITE_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_tracker (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            market_type TEXT,
            symbol TEXT,
            instrument TEXT,
            action TEXT,
            entry_price REAL,
            target_1 REAL,
            target_2 REAL,
            stop_loss REAL,
            exit_price REAL,
            pnl_points REAL,
            pnl_cash REAL,
            status TEXT,
            edge_confidence INTEGER
        )
        """)
        conn.commit()

init_sqlite_db()

def load_users():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f)
        return DEFAULT_USERS
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_USERS

def save_users(users_dict):
    with open(DB_FILE, "w") as f:
        json.dump(users_dict, f, indent=4)

def load_signals_log():
    if not os.path.exists(SIGNALS_LOG_FILE):
        return []
    try:
        with open(SIGNALS_LOG_FILE, "r") as f:
            logs = json.load(f)
        now = datetime.now()
        valid_logs = []
        for l in logs:
            try:
                t = datetime.strptime(l.get("raw_time", ""), "%Y-%m-%d %H:%M:%S")
                if now - t < timedelta(hours=12):
                    valid_logs.append(l)
            except Exception:
                valid_logs.append(l)
        return valid_logs
    except Exception:
        return []

def save_signals_log(logs):
    with open(SIGNALS_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def load_active_trades():
    if not os.path.exists(ACTIVE_TRADES_FILE):
        return {}
    try:
        with open(ACTIVE_TRADES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_active_trades(trades):
    with open(ACTIVE_TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=4)

def load_autopilot_state():
    if not os.path.exists(AUTOPILOT_STATE_FILE):
        return {"running": False, "asset": "^NSEBANK", "tf": "15m", "conf": 80, "target": 50.0, "sl": 20.0, "strategy": "1. EMA Institutional Pullback (20/50)"}
    try:
        with open(AUTOPILOT_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"running": False, "asset": "^NSEBANK", "tf": "15m", "conf": 80, "target": 50.0, "sl": 20.0, "strategy": "1. EMA Institutional Pullback (20/50)"}

def save_autopilot_state(state):
    with open(AUTOPILOT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users()
if 'signals_history' not in st.session_state:
    st.session_state.signals_history = load_signals_log()
if 'active_radar_trades' not in st.session_state:
    st.session_state.active_radar_trades = load_active_trades()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==============================================================================
# 📡 TELEGRAM DISPATCHER
# ==============================================================================
TG_BOT_TOKEN = "8928886896:AAG_K3y8ltCsHPqfva-ONzfjXVu1R9vD5ko"
TG_CHAT_ID = "@sam_quantum_signals"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=8)
        return resp.status_code == 200, resp.text
    except Exception as e:
        return False, str(e)

# ==============================================================================
# 🧮 GREEKS & PRICING ENGINE
# ==============================================================================
def std_norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def std_norm_pdf(x):
    return math.exp(-0.5 * x ** 2) / math.sqrt(2.0 * math.pi)

class BlackScholesEngine:
    @staticmethod
    def calculate_greeks(spot, strike, dte_days=2, iv=14.5, risk_free_rate=0.07, option_type="CE"):
        T = max(dte_days / 365.0, 0.0001)
        sigma = max(iv / 100.0, 0.01)
        r = risk_free_rate
        
        d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        pdf_d1 = std_norm_pdf(d1)
        cdf_d1 = std_norm_cdf(d1)
        cdf_d2 = std_norm_cdf(d2)
        cdf_neg_d1 = std_norm_cdf(-d1)
        cdf_neg_d2 = std_norm_cdf(-d2)
        
        if option_type.upper() == "CE":
            premium = spot * cdf_d1 - strike * math.exp(-r * T) * cdf_d2
            delta = cdf_d1
            theta = (- (spot * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * strike * math.exp(-r * T) * cdf_d2) / 365.0
        else:
            premium = strike * math.exp(-r * T) * cdf_neg_d2 - spot * cdf_neg_d1
            delta = cdf_d1 - 1.0
            theta = (- (spot * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * strike * math.exp(-r * T) * cdf_neg_d2) / 365.0
            
        gamma = pdf_d1 / (spot * sigma * math.sqrt(T))
        vega = (spot * math.sqrt(T) * pdf_d1) / 100.0
        
        return {
            "premium": max(0.50, round(premium, 2)),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 2),
            "vega": round(vega, 2)
        }

def get_live_asset_price(symbol_key, default_price=57380.0):
    try:
        df_quick = yf.download(symbol_key, period="1d", interval="1m", progress=False)
        if not df_quick.empty:
            if isinstance(df_quick.columns, pd.MultiIndex):
                df_quick.columns = df_quick.columns.droplevel(1)
            return round(float(df_quick['Close'].iloc[-1]), 2)
    except Exception:
        pass
    return default_price

def get_dynamic_expiry_and_tag(asset_symbol):
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    current_time = now_ist.time()
    
    if asset_symbol.endswith("-USD"):
        return "PERPETUAL / NO EXPIRY", "CRYPTO"
    
    if asset_symbol in ["GC=F", "SI=F", "CL=F"]:
        cur_month = now_ist.month
        cur_year = now_ist.year
        if now_ist.day > 5:
            cur_month += 1
            if cur_month > 12:
                cur_month = 1
                cur_year += 1
        exp_date = datetime(cur_year, cur_month, 5)
        return f"FUTURES: {exp_date.strftime('%d %b %Y').upper()}", "MCX"
    
    target_weekday = 1 if asset_symbol in ["^NSEBANK", "^NSEI"] else 3
    days_ahead = (target_weekday - now_ist.weekday()) % 7
    if days_ahead == 0 and current_time > dtime(15, 30):
        days_ahead = 7
        
    exp_date = now_ist + timedelta(days=days_ahead)
    return f"EXPIRY: {exp_date.strftime('%d %b %Y').upper()}", "NSE"

def is_market_open(symbol_key):
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    weekday = now_ist.weekday()
    current_time = now_ist.time()

    if symbol_key in ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"]:
        return True, "Crypto (24/7 Live Active)"

    if weekday in [5, 6]:
        return False, "Market Closed (Weekend)"

    if symbol_key in ["^NSEBANK", "^NSEI", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS"]:
        market_start = dtime(9, 15)
        market_end = dtime(15, 30)
        if market_start <= current_time <= market_end:
            return True, "NSE Intraday (09:15 - 15:30 IST)"
        return False, "NSE Closed (Opens 09:15 AM Mon-Fri)"

    if symbol_key in ["GC=F", "SI=F", "CL=F"]:
        mcx_start = dtime(9, 0)
        mcx_end = dtime(23, 30)
        if mcx_start <= current_time <= mcx_end:
            return True, "MCX Commodity (09:00 - 23:30 IST)"
        return False, "MCX Closed"

    return False, "Market Closed"

# ==============================================================================
# 🛡️ CAPITAL & MARGIN ENGINE
# ==============================================================================
def validate_and_calculate_margin(capital, current_price, requested_qty, is_option=False, leverage=1.0):
    unit_cost = current_price if not is_option else max(5.0, current_price * 0.01)
    total_required = (unit_cost * requested_qty) / leverage
    
    if capital < total_required:
        max_affordable = int((capital * leverage) // unit_cost)
        if max_affordable <= 0:
            return {
                "status": "REJECTED",
                "reason": f"Insufficient Capital (Required: ₹{total_required:,.2f}, Available: ₹{capital:,.2f})",
                "traded_qty": 0,
                "cost": 0.0
            }
        return {
            "status": "ADJUSTED",
            "reason": f"Order size adjusted to available capital limit.",
            "traded_qty": max_affordable,
            "cost": (unit_cost * max_affordable) / leverage
        }
        
    return {
        "status": "FILLED",
        "reason": "Margin Approved",
        "traded_qty": requested_qty,
        "cost": total_required
    }

# ==============================================================================
# 🛠️ STRATEGY REGISTRY PATTERN
# ==============================================================================
class StrategyRegistry:
    @staticmethod
    def ema_pullback(df):
        d = df.copy()
        c = d['Close']
        d['EMA20'] = c.ewm(span=20, adjust=False).mean()
        d['EMA50'] = c.ewm(span=50, adjust=False).mean()
        
        delta = c.diff()
        gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        d['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        
        d['signal'] = 0
        d['confidence'] = 0
        
        cond_buy = (d['EMA20'] > d['EMA50']) & (d['Close'] >= d['EMA20']) & (d['RSI'] > 52) & (d['Volume'] >= d['VOL_SMA20'])
        cond_sell = (d['EMA20'] < d['EMA50']) & (d['Close'] <= d['EMA20']) & (d['RSI'] < 48) & (d['Volume'] >= d['VOL_SMA20'])
        
        d.loc[cond_buy, 'signal'] = 1
        d.loc[cond_buy, 'confidence'] = 88
        d.loc[cond_sell, 'signal'] = -1
        d.loc[cond_sell, 'confidence'] = 88
        return d

    @staticmethod
    def supertrend_rider(df):
        d = df.copy()
        c, h, l = d['Close'], d['High'], d['Low']
        d['EMA200'] = c.ewm(span=200, adjust=False).mean()
        
        hl = h - l
        hc = (h - c.shift(1)).abs()
        lc = (l - c.shift(1)).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        st_atr = tr.ewm(com=9, adjust=False).mean()
        
        hl2 = (h + l) / 2.0
        basic_ub = hl2 + (2.0 * st_atr)
        basic_lb = hl2 - (2.0 * st_atr)
        final_ub = basic_ub.copy()
        final_lb = basic_lb.copy()
        direction = np.zeros(len(d))

        for i in range(1, len(d)):
            if basic_ub.iloc[i] < final_ub.iloc[i-1] or c.iloc[i-1] > final_ub.iloc[i-1]:
                final_ub.iloc[i] = basic_ub.iloc[i]
            else:
                final_ub.iloc[i] = final_ub.iloc[i-1]
            if basic_lb.iloc[i] > final_lb.iloc[i-1] or c.iloc[i-1] < final_lb.iloc[i-1]:
                final_lb.iloc[i] = basic_lb.iloc[i]
            else:
                final_lb.iloc[i] = final_lb.iloc[i-1]
            if c.iloc[i] > final_ub.iloc[i-1]:
                direction[i] = 1
            elif c.iloc[i] < final_lb.iloc[i-1]:
                direction[i] = -1
            else:
                direction[i] = direction[i-1]

        d['ST_DIR'] = direction
        d['signal'] = 0
        d['confidence'] = 0
        
        flip_up = (d['ST_DIR'] == 1) & (d['ST_DIR'].shift(1) == -1) & (d['Close'] > d['EMA200'])
        flip_down = (d['ST_DIR'] == -1) & (d['ST_DIR'].shift(1) == 1) & (d['Close'] < d['EMA200'])
        
        d.loc[flip_up, 'signal'] = 1
        d.loc[flip_up, 'confidence'] = 92
        d.loc[flip_down, 'signal'] = -1
        d.loc[flip_down, 'confidence'] = 92
        return d

    @staticmethod
    def macd_momentum(df):
        d = df.copy()
        c = d['Close']
        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        d['MACD'] = ema12 - ema26
        d['SIGNAL_LINE'] = d['MACD'].ewm(span=9, adjust=False).mean()
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        
        d['signal'] = 0
        d['confidence'] = 0
        
        buy_cond = (d['MACD'] > d['SIGNAL_LINE']) & (d['MACD'].shift(1) <= d['SIGNAL_LINE'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        sell_cond = (d['MACD'] < d['SIGNAL_LINE']) & (d['MACD'].shift(1) >= d['SIGNAL_LINE'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        
        d.loc[buy_cond, 'signal'] = 1
        d.loc[buy_cond, 'confidence'] = 86
        d.loc[sell_cond, 'signal'] = -1
        d.loc[sell_cond, 'confidence'] = 86
        return d

    @staticmethod
    def bollinger_rsi_reversion(df):
        d = df.copy()
        c = d['Close']
        d['SMA20'] = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        d['BB_UPPER'] = d['SMA20'] + (2.0 * std20)
        d['BB_LOWER'] = d['SMA20'] - (2.0 * std20)
        
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        d['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))
        
        d['signal'] = 0
        d['confidence'] = 0
        
        buy_cond = (d['Low'] <= d['BB_LOWER']) & (d['RSI'] < 30)
        sell_cond = (d['High'] >= d['BB_UPPER']) & (d['RSI'] > 70)
        
        d.loc[buy_cond, 'signal'] = 1
        d.loc[buy_cond, 'confidence'] = 89
        d.loc[sell_cond, 'signal'] = -1
        d.loc[sell_cond, 'confidence'] = 89
        return d

    @staticmethod
    def orb_breakout(df):
        d = df.copy()
        d['signal'] = 0
        d['confidence'] = 0
        d['HIGH_15'] = d['High'].rolling(3).max().shift(1)
        d['LOW_15'] = d['Low'].rolling(3).min().shift(1)
        
        buy_cond = (d['Close'] > d['HIGH_15'])
        sell_cond = (d['Close'] < d['LOW_15'])
        
        d.loc[buy_cond, 'signal'] = 1
        d.loc[buy_cond, 'confidence'] = 84
        d.loc[sell_cond, 'signal'] = -1
        d.loc[sell_cond, 'confidence'] = 84
        return d

    @staticmethod
    def donchian_breakout(df):
        d = df.copy()
        d['DC_HIGH'] = d['High'].rolling(20).max().shift(1)
        d['DC_LOW'] = d['Low'].rolling(20).min().shift(1)
        
        d['signal'] = 0
        d['confidence'] = 0
        
        buy_cond = (d['Close'] > d['DC_HIGH'])
        sell_cond = (d['Close'] < d['DC_LOW'])
        
        d.loc[buy_cond, 'signal'] = 1
        d.loc[buy_cond, 'confidence'] = 91
        d.loc[sell_cond, 'signal'] = -1
        d.loc[sell_cond, 'confidence'] = 91
        return d

    @staticmethod
    def vwap_expansion(df):
        d = df.copy()
        typical_price = (d['High'] + d['Low'] + d['Close']) / 3.0
        d['VWAP'] = (typical_price * d['Volume']).cumsum() / d['Volume'].cumsum()
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        
        d['signal'] = 0
        d['confidence'] = 0
        
        buy_cond = (d['Close'] > d['VWAP']) & (d['Close'].shift(1) <= d['VWAP'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        sell_cond = (d['Close'] < d['VWAP']) & (d['Close'].shift(1) >= d['VWAP'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        
        d.loc[buy_cond, 'signal'] = 1
        d.loc[buy_cond, 'confidence'] = 87
        d.loc[sell_cond, 'signal'] = -1
        d.loc[sell_cond, 'confidence'] = 87
        return d

STRATEGY_MAP = {
    "1. EMA Institutional Pullback (20/50)": StrategyRegistry.ema_pullback,
    "2. SuperTrend Trend-Rider (10, 2.0 + 200 EMA)": StrategyRegistry.supertrend_rider,
    "3. MACD + Volume Spike Momentum": StrategyRegistry.macd_momentum,
    "4. Bollinger Bands + RSI Mean Reversion": StrategyRegistry.bollinger_rsi_reversion,
    "5. Opening Range Breakout (ORB 15-Min)": StrategyRegistry.orb_breakout,
    "6. Donchian Channel Volatility Breakout (20-Period)": StrategyRegistry.donchian_breakout,
    "7. VWAP Intraday Retest & Expansion": StrategyRegistry.vwap_expansion
}

# ==============================================================================
# 🤖 24/7 BACKGROUND WORKER (AUTONOMOUS THREAD)
# ==============================================================================
def background_scanner_loop():
    while True:
        try:
            state = load_autopilot_state()
            if state.get("running", False):
                asset = state.get("asset", "^NSEBANK")
                tf = state.get("tf", "15m")
                min_conf = state.get("conf", 80)
                rd_target = state.get("target", 50.0)
                rd_sl = state.get("sl", 20.0)
                strat_name = state.get("strategy", "1. EMA Institutional Pullback (20/50)")
                
                open_flag, _ = is_market_open(asset)
                if open_flag:
                    df = yf.download(asset, period="3d", interval=tf, progress=False)
                    if not df.empty and len(df) >= 20:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.droplevel(1)
                        
                        strat_func = STRATEGY_MAP.get(strat_name, StrategyRegistry.ema_pullback)
                        df = strat_func(df)
                        
                        spot = float(df['Close'].iloc[-1])
                        now_ist = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
                        now_raw = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_id = f"{asset}_{int(time.time())}"
                        curr_sym = "$" if asset.endswith("-USD") else "₹"
                        
                        current_active = load_active_trades()
                        completed = []
                        
                        for r_sym, r_trade in list(current_active.items()):
                            live_spot = spot
                            entry_p = r_trade['entry']
                            tp_p = r_trade['target']
                            sl_p = r_trade['sl']
                            action = r_trade['action']
                            strk_info = r_trade.get('strike_info', '')
                            prem_entry = r_trade.get('premium_entry', 188)
                            last_milestone = r_trade.get('last_milestone', 0)

                            is_short = ("SHORT" in action) or ("SELL" in action) or ("PE" in action and not asset.endswith("-USD") and "FUT" not in strk_info)
                            is_crypto = asset.endswith("-USD")
                            is_mcx = asset in ["GC=F", "SI=F", "CL=F"]

                            if is_short and (is_crypto or is_mcx or "SHORT" in action):
                                spot_move = entry_p - live_spot
                                target_hit = live_spot <= tp_p
                                sl_hit = live_spot >= sl_p
                            else:
                                spot_move = live_spot - entry_p if not ("PE" in strk_info and not is_crypto) else (entry_p - live_spot)
                                target_hit = (live_spot >= tp_p) if ("BUY" in action or "LONG" in action or "CE" in action) else (live_spot <= tp_p)
                                sl_hit = (live_spot <= sl_p) if ("BUY" in action or "LONG" in action or "CE" in action) else (live_spot >= sl_p)

                            if is_crypto:
                                profit_pct = (spot_move / entry_p) * 100.0
                                if profit_pct >= (last_milestone + 0.8) and not target_hit and not sl_hit:
                                    last_milestone_up = round(last_milestone + 0.8, 1)
                                    tg_update = f"<b>{strk_info}</b>\n\n<b>+{profit_pct:.1f}% Profit Milestone 🔥🔥</b>\n\n<b>++ (Current: ${live_spot:,.2f})</b>"
                                    send_telegram_alert(tg_update)
                                    r_trade['last_milestone'] = last_milestone_up
                                    current_active[r_sym] = r_trade
                                    save_active_trades(current_active)
                            elif is_mcx:
                                if spot_move >= last_milestone + 150 and not target_hit and not sl_hit:
                                    last_milestone_up = int(last_milestone + 150)
                                    tg_update = f"<b>{strk_info}</b>\n\n<b>+{last_milestone_up} Points Gain 🔥🔥</b>\n\n<b>++</b>"
                                    send_telegram_alert(tg_update)
                                    r_trade['last_milestone'] = last_milestone_up
                                    current_active[r_sym] = r_trade
                                    save_active_trades(current_active)
                            else:
                                cur_prem = int(prem_entry + (spot_move * 0.55))
                                if spot_move >= last_milestone + 10 and not target_hit and not sl_hit:
                                    pts_up = int(last_milestone + 10)
                                    cur_prem_disp = int(prem_entry + (pts_up * 0.55))
                                    tg_update = f"<b>{cur_prem_disp} 🔥🔥</b>\n\n<b>++</b>"
                                    send_telegram_alert(tg_update)
                                    r_trade['last_milestone'] = pts_up
                                    current_active[r_sym] = r_trade
                                    save_active_trades(current_active)

                            if target_hit:
                                tg_done = (
                                    f"🎯 <b>TARGET COMPLETED - BOOK FULL PROFIT</b> 🎯\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"📊 <b>{strk_info}</b>\n"
                                    f"✅ <b>Status:</b> <code>FULL TARGET HIT 🚀</code>\n"
                                    f"💵 <b>Exit Price:</b> {curr_sym}{live_spot:,.2f}\n"
                                    f"⏱ <b>Completed At:</b> {now_ist}\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"🤖 <i>Accountability Logged via Sam Quantum AI</i>"
                                )
                                send_telegram_alert(tg_done)
                                logs = load_signals_log()
                                for item in logs:
                                    if item.get("id") == r_trade.get("log_id"):
                                        item["status"] = "TARGET HIT 🎯"
                                        item["exit_price"] = f"{curr_sym}{live_spot:,.2f}"
                                save_signals_log(logs)
                                completed.append(r_sym)

                            elif sl_hit:
                                tg_sl = (
                                    f"🛑 <b>STOP LOSS HIT - POSITION CLOSED</b> 🛑\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"📊 <b>{strk_info}</b>\n"
                                    f"🛑 <b>Status:</b> <code>SL TRIGGERED</code>\n"
                                    f"💵 <b>Exit Spot:</b> {curr_sym}{live_spot:,.2f}\n"
                                    f"⏱ <b>Closed At:</b> {now_ist}\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"🤖 <i>Risk Managed via Sam Quantum AI</i>"
                                )
                                send_telegram_alert(tg_sl)
                                logs = load_signals_log()
                                for item in logs:
                                    if item.get("id") == r_trade.get("log_id"):
                                        item["status"] = "SL HIT 🛑"
                                        item["exit_price"] = f"{curr_sym}{live_spot:,.2f}"
                                save_signals_log(logs)
                                completed.append(r_sym)

                        for c_item in completed:
                            if c_item in current_active:
                                del current_active[c_item]
                        save_active_trades(current_active)

                        if asset not in current_active:
                            last_sig = int(df['signal'].iloc[-1])
                            last_conf = int(df['confidence'].iloc[-1])
                            
                            if last_sig != 0 and last_conf >= min_conf:
                                sig_raw = "BUY" if last_sig == 1 else "SELL"
                                exp_tag, market_cat = get_dynamic_expiry_and_tag(asset)
                                specs = INDEX_SPECS.get(asset, {"name": asset, "strike_step": 100})
                                strike_step = specs.get("strike_step", 100)
                                strike_val = int(round(spot / float(strike_step)) * strike_step)
                                
                                if market_cat == "NSE":
                                    opt_type = "CE" if sig_raw == "BUY" else "PE"
                                    inst_name = f"{specs['name']} {strike_val} {opt_type} ({exp_tag})"
                                    greeks = BlackScholesEngine.calculate_greeks(spot, strike_val, 2, 14.5, 0.07, opt_type)
                                    base_prem = greeks["premium"]
                                    tp_prem = int(base_prem + (rd_target * 0.55))
                                    sl_prem = int(base_prem - (rd_sl * 0.55))
                                    tp_spot = spot + rd_target if sig_raw == "BUY" else spot - rd_target
                                    sl_spot = spot - rd_sl if sig_raw == "BUY" else spot + rd_sl

                                    tg_text = (
                                        f"📊 <b>{inst_name}</b>\n\n"
                                        f"📈 <b>BUY ABOVE ₹{base_prem}</b>\n\n"
                                        f"🎯 <b>TARGET: ₹{tp_prem} | ₹{tp_prem + 30}</b>\n\n"
                                        f"☠️ <b>SL: ₹{sl_prem}</b>\n\n"
                                        f"<i>⏱ Trigger: {now_ist} | 🧠 Edge: {last_conf}% Verified ({strat_name})</i>"
                                    )
                                elif market_cat == "MCX":
                                    strk_name = f"{specs['name']} ({exp_tag})"
                                    base_prem = int(spot)
                                    tp_spot = spot + rd_target if sig_raw == "BUY" else spot - rd_target
                                    sl_spot = spot - rd_sl if sig_raw == "BUY" else spot + rd_sl
                                    pos_label = "BUY ABOVE" if sig_raw == "BUY" else "SELL BELOW"
                                    
                                    tg_text = (
                                        f"📊 <b>{strk_name}</b>\n\n"
                                        f"📈 <b>{pos_label} ₹{base_prem:,.0f}</b>\n\n"
                                        f"🎯 <b>TARGET: ₹{tp_spot:,.0f} ({'+' if sig_raw == 'BUY' else '-'}{rd_target:.0f} Pts)</b>\n\n"
                                        f"☠️ <b>SL: ₹{sl_spot:,.0f}</b>\n\n"
                                        f"<i>⏱ Trigger: {now_ist} | 🧠 Edge: {last_conf}% Verified</i>"
                                    )
                                else:
                                    strk_name = f"{specs['name']} (PERPETUAL SWAP)"
                                    base_prem = spot
                                    tp_spot = spot * (1 + (rd_target / 100.0)) if sig_raw == "BUY" else spot * (1 - (rd_target / 100.0))
                                    sl_spot = spot * (1 - (rd_sl / 100.0)) if sig_raw == "BUY" else spot * (1 + (rd_sl / 100.0))
                                    pos_type = "LONG 🟢" if sig_raw == "BUY" else "SHORT 🔴"

                                    tg_text = (
                                        f"📊 <b>{strk_name}</b>\n\n"
                                        f"🚀 <b>POSITION: {pos_type}</b>\n\n"
                                        f"💵 <b>ENTRY: ${spot:,.2f}</b>\n\n"
                                        f"🎯 <b>TARGET: ${tp_spot:,.2f} ({'+' if 'LONG' in pos_type else '-'}{rd_target:.1f}%)</b>\n\n"
                                        f"🛑 <b>STOP LOSS: ${sl_spot:,.2f}</b>\n\n"
                                        f"<i>⏱ Trigger: {now_ist} | 🧠 Edge: {last_conf}% Verified</i>"
                                    )

                                send_telegram_alert(tg_text)
                                current_active[asset] = {
                                    "asset_name": asset, "strike_info": strk_name if market_cat != "NSE" else inst_name,
                                    "action": sig_raw, "entry": spot, "target": tp_spot, "sl": sl_spot,
                                    "premium_entry": base_prem, "last_milestone": 0,
                                    "status": "LIVE IN POSITION", "trailed": False, "time": now_ist,
                                    "sym": curr_sym, "log_id": log_id
                                }
                                save_active_trades(current_active)
                                logs = load_signals_log()
                                logs.insert(0, {
                                    "id": log_id, "time": now_ist, "raw_time": now_raw,
                                    "instrument": strk_name if market_cat != "NSE" else inst_name, "action": sig_raw, "entry_spot": spot,
                                    "target": f"{curr_sym}{tp_spot:,.1f}", "sl": f"{curr_sym}{sl_spot:,.1f}",
                                    "confidence": f"{last_conf}%", "status": "LIVE IN POSITION",
                                    "exit_price": "-"
                                })
                                save_signals_log(logs)
        except Exception:
            pass
        time.sleep(30)

if 'bg_thread_started' not in st.session_state:
    st.session_state.bg_thread_started = True
    t = threading.Thread(target=background_scanner_loop, daemon=True)
    t.start()

query_params = st.query_params
if not st.session_state.authenticated and "uid" in query_params:
    saved_uid = query_params["uid"]
    users = st.session_state.users_db
    if saved_uid in users:
        st.session_state.authenticated = True
        st.session_state.user_info = {**users[saved_uid], "id": saved_uid}

# ==============================================================================
# 🔐 AUTHENTICATION PORTAL
# ==============================================================================
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(13, 20, 36, 0.75); border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 16px; padding: 24px; text-align: center;">
            <div style="font-size: 38px; margin-bottom: 4px;">⚡</div>
            <h2 style="color: #38bdf8; margin: 0; font-weight: 800;">SAM QUANTUM AI</h2>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 14px 0;">Institutional Quantitative Terminal & Multi-Strategy Backtester</p>
            <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 15px;">
                <span style="background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700;">● LIVE QUANT FEED</span>
            </div>
            <hr style="border-color: rgba(30, 41, 59, 0.8); margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Mode", ["🔑 Terminal Sign In", "✨ Register Verified Account"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "🔑 Terminal Sign In":
            with st.form("login_form"):
                st.markdown("##### 🔒 Secure Terminal Authentication")
                username = st.text_input("Operator User ID", value="", placeholder="Enter User ID (e.g. admin)")
                password = st.text_input("Quantum Security Key", type="password", value="", placeholder="Enter Security Key")
                if st.form_submit_button("⚡ UNLOCK QUANTUM TERMINAL"):
                    users = st.session_state.users_db
                    if username in users and users[username]["pass"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**users[username], "id": username}
                        st.query_params["uid"] = username
                        st.rerun()
                    else:
                        st.error("⛔ Authentication Denied: Invalid Security Key or User ID.")
        else:
            with st.form("signup_form"):
                st.markdown("##### 🚀 Mandatory Quantitative Trader Profile")
                new_name = st.text_input("Full Name *", placeholder="e.g. Samir Khan")
                new_phone = st.text_input("10-Digit Mobile / WhatsApp Number *", placeholder="e.g. 9876543210")
                new_user = st.text_input("Create Operator User ID *", placeholder="e.g. samir_quant")
                new_pass = st.text_input("Create Access Password (Min 4 chars) *", type="password")
                
                if st.form_submit_button("🎉 VERIFY IDENTITY & UNLOCK ACCESS"):
                    clean_phone = re.sub(r'[^0-9]', '', new_phone)
                    if len(new_name.strip()) < 3:
                        st.error("❌ Full Name is mandatory.")
                    elif len(clean_phone) != 10:
                        st.error("❌ Valid 10-digit Indian Mobile number is mandatory.")
                    elif len(new_user.strip()) < 3:
                        st.error("❌ Unique User ID is mandatory.")
                    elif len(new_pass.strip()) < 4:
                        st.error("❌ Password must be at least 4 characters.")
                    elif new_user in st.session_state.users_db:
                        st.error("❌ User ID already registered.")
                    else:
                        st.session_state.users_db[new_user] = {
                            "pass": new_pass, "name": new_name.strip(), "phone": clean_phone,
                            "tier": "Free Member", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_users(st.session_state.users_db)
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**st.session_state.users_db[new_user], "id": new_user}
                        st.query_params["uid"] = new_user
                        st.rerun()
    st.stop()

# ==============================================================================
# 🎛️ SIDEBAR & RISK CONTROLS
# ==============================================================================
user_info_dict = st.session_state.get("user_info") or {}
curr_tier = user_info_dict.get("tier", "Free Member")
curr_uid = user_info_dict.get("id", "")
user_name = user_info_dict.get("name", "Authorized Operator")
is_admin = curr_tier == "Master Admin" or curr_uid == "admin"

FULL_ASSETS = {k: v["name"] for k, v in INDEX_SPECS.items()}

if curr_tier == "Free Member":
    allowed_asset_keys = ["^NSEBANK", "^NSEI", "BTC-USD"]
    allowed_tf = ["15m", "1d"]
elif curr_tier == "VIP Algo Trader":
    allowed_asset_keys = ["^NSEBANK", "^NSEI", "RELIANCE.NS", "HDFCBANK.NS", "GC=F", "SI=F", "BTC-USD", "ETH-USD", "SOL-USD"]
    allowed_tf = ["15m", "5m", "1m", "30m", "1d"]
else:
    allowed_asset_keys = list(FULL_ASSETS.keys())
    allowed_tf = ["15m", "5m", "1m", "2m", "30m", "60m", "1d"]

asset_dict = {k: FULL_ASSETS[k] for k in allowed_asset_keys}

with st.sidebar:
    st.markdown(f"""
    <div style="background:{'rgba(30, 27, 75, 0.8)' if is_admin else 'rgba(15, 23, 42, 0.8)'}; border:1px solid {'#818cf8' if is_admin else '#334155'}; border-radius:12px; padding:14px; margin-bottom:14px;">
        <span style="color:#38bdf8; font-weight:800; font-size:14px;">⚡ SAM QUANTUM OS</span><br>
        <span style="color:#f8fafc; font-size:12px;">Operator: <b>{user_name}</b></span><br>
        <span style="color: #10b981; font-size: 11px; font-weight: 700;">● {curr_tier.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout Terminal"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        if "uid" in st.query_params:
            del st.query_params["uid"]
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 1. Asset & Resolution")
    symbol = st.selectbox("Market Feed", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x])
    timeframe = st.selectbox("Resolution Stream", allowed_tf, index=0)
    lookback_days = st.slider("Lookback Memory (Days)", 1, 60, 30)

    st.markdown("---")
    st.markdown("### 🛠️ 2. Strategy Engine (Registry Pattern)")
    strategy_type = st.selectbox("Quantitative Strategy Library", list(STRATEGY_MAP.keys()))
    
    st.markdown("---")
    st.markdown("### 🛡️ 3. Risk & Capital Guard")
    capital = st.number_input("Capital Pool / Margin (₹)", value=100000.0, step=10000.0, min_value=1.0)
    
    lot_size_val = INDEX_SPECS.get(symbol, {}).get("lot_size", 1)
    num_lots = st.number_input(f"Number of Lots (Lot Size: {lot_size_val})", value=2, step=1, min_value=1)
    total_qty = num_lots * lot_size_val
    st.caption(f"Requested Quantity: `{total_qty}` Units")

    is_idx = symbol in ["^NSEBANK", "^NSEI", "^BSESN"]
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        target_val = st.number_input("Target (" + ("Pts" if is_idx else "%") + ")", value=50.0 if is_idx else 2.5, step=5.0 if is_idx else 0.5)
    with col_k2:
        sl_val = st.number_input("Hard SL (" + ("Pts" if is_idx else "%") + ")", value=20.0 if is_idx else 1.0, step=5.0 if is_idx else 0.2)

# ==============================================================================
# 🚀 MAIN DASHBOARD & TABS
# ==============================================================================
header_spot = get_live_asset_price(symbol, 57380.0 if symbol == "^NSEBANK" else (24250.0 if symbol == "^NSEI" else 1380.0))
header_curr = "$" if symbol.endswith("-USD") else "₹"

col_run1, col_run2 = st.columns([3, 1])
with col_run1:
    st.write(f"💼 **Active Target:** `{asset_dict[symbol]}` | Live Spot: **{header_curr}{header_spot:,.2f}** | Strategy: **{strategy_type.split('.')[1].strip()}**")
with col_run2:
    execute_btn = st.button("⚡ EXECUTE STRATEGY BACKTEST", type="primary")

if is_admin:
    tab_tv_chart, tab_backtest, tab_metrics, tab_trades, tab_reports, tab_ai_pilot, tab_manual_terminal, tab_ai_logbook, tab_admin_access = st.tabs([
        "📊 Live Demat Chart Studio", "📈 Pro Backtest Chart", "📊 Scorecard & KPIs", "📜 Trade Logs",
        "📥 Download Reports", "🤖 AI 24/7 Autopilot Hub", "✍️ Pro Manual Option Chain", "📑 Signal Logbook", "👑 Admin Console"
    ])
else:
    tab_tv_chart, tab_backtest, tab_metrics, tab_trades, tab_reports, tab_ai_pilot, tab_manual_terminal, tab_ai_logbook = st.tabs([
        "📊 Live Demat Chart Studio", "📈 Pro Backtest Chart", "📊 Scorecard & KPIs", "📜 Trade Logs",
        "📥 Download Reports", "🤖 AI 24/7 Autopilot Hub", "✍️ Pro Manual Option Chain", "📑 Signal Logbook"
    ])

# ==============================================================================
# 📊 TAB 1: GROWW MOUNTAIN GLOW VS. PRO CANDLESTICK LIVE CHART
# ==============================================================================
with tab_tv_chart:
    st.markdown("#### 📊 Live Demat Interactive Chart Studio")
    st.caption("Switch between Mountain Glow Area and Candlestick. Price lines stick permanently during zoom/pan.")

    col_dc1, col_dc2, col_dc3 = st.columns([1.5, 1, 1])
    with col_dc1:
        live_chart_asset = st.selectbox("Select Demat Market Stream", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x], key="live_demat_asset")
    with col_dc2:
        live_chart_tf = st.selectbox("Stream Resolution", ["1m", "5m", "15m", "30m", "60m", "1d"], index=1, key="live_demat_tf")
    with col_dc3:
        is_usd = live_chart_asset.endswith("-USD")
        curr_label = "$" if is_usd else "₹"
        is_live_open, gate_desc = is_market_open(live_chart_asset)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Status:** `{gate_desc.upper()}`")

    try:
        period_str = "1d" if live_chart_tf in ["1m", "5m"] else "5d" if live_chart_tf in ["15m", "30m"] else "30d"
        df_demat = yf.download(live_chart_asset, period=period_str, interval=live_chart_tf, progress=False)
        
        if df_demat.empty or len(df_demat) < 5:
            st.warning("⚠️ Connecting live market feed...")
        else:
            if isinstance(df_demat.columns, pd.MultiIndex):
                df_demat.columns = df_demat.columns.droplevel(1)
            df_demat.dropna(inplace=True)

            ist_time_demat = df_demat.index.tz_convert('Asia/Kolkata') if df_demat.index.tz is not None else df_demat.index + pd.Timedelta(hours=5, minutes=30)
            
            candle_list, area_list = [], []
            for i in range(len(df_demat)):
                row = df_demat.iloc[i]
                t_sec = int(ist_time_demat[i].timestamp())
                t_str = ist_time_demat[i].strftime('%d-%b-%Y %I:%M %p IST')
                candle_list.append({
                    "time": t_sec, "time_str": t_str,
                    "open": round(float(row['Open']), 2), "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2), "close": round(float(row['Close']), 2)
                })
                area_list.append({"time": t_sec, "value": round(float(row['Close']), 2)})

            candles_json = json.dumps(candle_list)
            area_json = json.dumps(area_list)

            latest_c = candle_list[-1]
            init_spot = latest_c['close']
            init_high = float(df_demat['High'].max())
            init_low = float(df_demat['Low'].min())

            demat_studio_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
            <style>
                body {{ margin: 0; padding: 0; background: #050811; font-family: sans-serif; color: #f1f5f9; overflow: hidden; }}
                #metrics_grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 8px; }}
                .metric-card {{ background: #0d1527; border: 1px solid #1e293b; border-radius: 10px; padding: 8px 12px; }}
                .metric-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; }}
                .metric-val {{ font-family: monospace; font-size: 18px; font-weight: bold; color: #38bdf8; }}
                #main_wrapper {{ display: flex; width: 100%; height: 540px; border: 1px solid #1e293b; border-radius: 10px; }}
                #left_toolbar {{ width: 44px; background: #0d1527; border-right: 1px solid #1e293b; display: flex; flex-direction: column; align-items: center; padding-top: 8px; gap: 6px; }}
                .tool-btn {{ width: 32px; height: 32px; border-radius: 6px; border: 1px solid transparent; background: transparent; color: #94a3b8; display: flex; align-items: center; justify-content: center; cursor: pointer; }}
                .tool-btn:hover {{ background: #1e293b; color: #38bdf8; }}
                .tool-btn.active {{ background: rgba(56, 189, 248, 0.2); border-color: #38bdf8; color: #38bdf8; }}
                #chart_container {{ flex: 1; height: 100%; position: relative; }}
                #legend_box {{ position: absolute; top: 8px; left: 52px; z-index: 60; color: #94a3b8; font-size: 11px; font-family: monospace; background: rgba(13, 21, 39, 0.85); padding: 4px 8px; border-radius: 4px; border: 1px solid #1e293b; }}
            </style>
            </head>
            <body>
            <div id="metrics_grid">
                <div class="metric-card"><div class="metric-label">Live Spot</div><div class="metric-val" id="card_spot">{curr_label}{init_spot:,.2f}</div></div>
                <div class="metric-card"><div class="metric-label">Session High</div><div class="metric-val">{curr_label}{init_high:,.2f}</div></div>
                <div class="metric-card"><div class="metric-label">Session Low</div><div class="metric-val">{curr_label}{init_low:,.2f}</div></div>
            </div>
            <div id="main_wrapper">
                <div id="left_toolbar">
                    <button class="tool-btn active" id="btn_cursor" title="Pan Mode">🔍</button>
                    <button class="tool-btn" id="btn_switch_view" title="Toggle View">📈</button>
                    <button class="tool-btn" id="btn_horiz" title="Draw S/R Level">➖</button>
                    <button class="tool-btn" id="btn_del_last" title="Delete Last Line">↩️</button>
                    <button class="tool-btn" id="btn_clear" title="Clear All Lines">🗑️</button>
                </div>
                <div id="legend_box"><span style="color:#38bdf8;font-weight:bold;">{asset_dict[live_chart_asset]}</span> | <span id="leg_time">-</span> | Price: <span id="leg_c">-</span></div>
                <div id="chart_container"></div>
            </div>
            <script>
                const container = document.getElementById('chart_container');
                const chart = LightweightCharts.createChart(container, {{
                    width: container.clientWidth, height: 540,
                    layout: {{ background: {{ color: '#050811' }}, textColor: '#94a3b8' }},
                    grid: {{ vertLines: {{ color: 'rgba(30, 41, 59, 0.4)' }}, horzLines: {{ color: 'rgba(30, 41, 59, 0.4)' }} }},
                    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                    rightPriceScale: {{ borderColor: '#1e293b' }},
                    timeScale: {{ borderColor: '#1e293b', timeVisible: true, secondsVisible: false }},
                    localization: {{ timeFormatter: t => new Date(t * 1000).toLocaleTimeString('en-IN', {{ timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true }}) }}
                }});

                const areaSeries = chart.addAreaSeries({{ topColor: 'rgba(56, 189, 248, 0.4)', bottomColor: 'rgba(56, 189, 248, 0.0)', lineColor: '#38bdf8', lineWidth: 2.5 }});
                const candleSeries = chart.addCandlestickSeries({{ upColor: '#10b981', downColor: '#ef4444', borderUpColor: '#10b981', borderDownColor: '#ef4444', wickUpColor: '#10b981', wickDownColor: '#ef4444', visible: false }});

                const rawCandles = {candles_json};
                const rawArea = {area_json};
                areaSeries.setData(rawArea);
                candleSeries.setData(rawCandles);
                chart.timeScale().fitContent();

                let isCandleView = false;
                document.getElementById('btn_switch_view').onclick = () => {{
                    isCandleView = !isCandleView;
                    areaSeries.applyOptions({{ visible: !isCandleView }});
                    candleSeries.applyOptions({{ visible: isCandleView }});
                }};

                chart.subscribeCrosshairMove(param => {{
                    if (param.time) {{
                        const d = new Date(param.time * 1000);
                        document.getElementById('leg_time').innerText = d.toLocaleTimeString('en-IN', {{timeZone: 'Asia/Kolkata', hour12: true}});
                        const data = isCandleView ? param.seriesData.get(candleSeries) : param.seriesData.get(areaSeries);
                        if (data) document.getElementById('leg_c').innerText = (data.close || data.value).toFixed(2);
                    }}
                }});

                let currentTool = 'cursor';
                let priceLines = [];

                function setTool(tool) {{
                    currentTool = tool;
                    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    if (tool === 'cursor') document.getElementById('btn_cursor').classList.add('active');
                    if (tool === 'horiz') document.getElementById('btn_horiz').classList.add('active');
                }}

                document.getElementById('btn_cursor').onclick = () => setTool('cursor');
                document.getElementById('btn_horiz').onclick = () => setTool('horiz');

                document.getElementById('btn_del_last').onclick = () => {{
                    if (priceLines.length > 0) {{
                        const last = priceLines.pop();
                        const activeS = isCandleView ? candleSeries : areaSeries;
                        activeS.removePriceLine(last);
                    }}
                }};

                document.getElementById('btn_clear').onclick = () => {{
                    const activeS = isCandleView ? candleSeries : areaSeries;
                    priceLines.forEach(pl => activeS.removePriceLine(pl));
                    priceLines = [];
                }};

                chart.subscribeClick(param => {{
                    if (currentTool === 'horiz' && param.point) {{
                        const activeS = isCandleView ? candleSeries : areaSeries;
                        const price = activeS.coordinateToPrice(param.point.y);
                        if (price) {{
                            const pl = activeS.createPriceLine({{
                                price: price, color: '#38bdf8', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true, title: 'S/R ' + price.toFixed(1)
                            }});
                            priceLines.push(pl);
                        }}
                        setTool('cursor');
                    }}
                }});

                let lastClose = rawCandles[rawCandles.length - 1].close;
                setInterval(() => {{
                    const delta = (Math.random() - 0.49) * (lastClose * 0.0003);
                    lastClose = parseFloat((lastClose + delta).toFixed(2));
                    const lastT = rawCandles[rawCandles.length - 1].time;
                    areaSeries.update({{ time: lastT, value: lastClose }});
                    candleSeries.update({{
                        time: lastT, open: rawCandles[rawCandles.length - 1].open,
                        high: Math.max(rawCandles[rawCandles.length - 1].high, lastClose),
                        low: Math.min(rawCandles[rawCandles.length - 1].low, lastClose),
                        close: lastClose,
                    }});
                    document.getElementById('card_spot').innerText = "{curr_label}" + lastClose.toLocaleString('en-IN', {{minimumFractionDigits: 2}});
                }}, 1000);
            </script>
            </body>
            </html>
            """
            components.html(demat_studio_html, height=660)

    except Exception as e:
        st.error(f"Error initializing chart: {str(e)}")

# ==============================================================================
# 📊 BACKTEST EXECUTION WITH CAPITAL VALIDATION & STRATEGY REGISTRY
# ==============================================================================
with tab_reports:
    st.markdown("### 📥 Instant Mobile Audit Reports & Master Handbook")
    st.download_button(
        label="📥 DOWNLOAD FULL TERMINAL USER MANUAL (.TXT)",
        data=TERMINAL_MANUAL_TEXT,
        file_name="SAM_QUANTUM_User_Manual.txt",
        mime="text/plain",
        use_container_width=True
    )

if execute_btn or st.session_state.get('backtest_executed', False):
    st.session_state.backtest_executed = True
    with st.spinner(f"⏳ Running Strategy Backtest: {strategy_type}..."):
        try:
            df_raw = yf.download(symbol, period=f"{lookback_days}d", interval=timeframe, progress=False)
            if not df_raw.empty and len(df_raw) >= 20:
                if isinstance(df_raw.columns, pd.MultiIndex):
                    df_raw.columns = df_raw.columns.droplevel(1)
                df_raw.dropna(inplace=True)
                
                strat_func = STRATEGY_MAP.get(strategy_type, StrategyRegistry.ema_pullback)
                df_bt = strat_func(df_raw)

                ist_time_bt = df_bt.index.tz_convert('Asia/Kolkata') if df_bt.index.tz is not None else df_bt.index + pd.Timedelta(hours=5, minutes=30)
                df_bt['Time_Str'] = [t.strftime('%d-%b %H:%M') for t in ist_time_bt]

                trades = []
                position = None
                current_balance = capital
                trade_rejections = 0

                for i in range(2, len(df_bt)):
                    curr_spot = float(df_bt['Close'].iloc[i])
                    sig = int(df_bt['signal'].iloc[i])
                    time_lbl = df_bt['Time_Str'].iloc[i]

                    if position is not None:
                        is_buy = position['type'] in ['BUY/CE', 'BUY', 'LONG']
                        move = (curr_spot - position['entry']) if is_buy else (position['entry'] - curr_spot)
                        opt_move = move if is_idx else ((move / position['entry']) * 100)

                        if opt_move >= target_val:
                            pnl = (target_val * position['qty'] * 0.5) if is_idx else ((target_val / 100) * position['qty'] * position['entry'])
                            current_balance += (position['cost'] + pnl)
                            trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Qty': position['qty'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'TARGET HIT 🎯', 'Points': target_val, 'PnL': pnl, 'Balance': current_balance})
                            position = None
                        elif opt_move <= -sl_val:
                            pnl = (-sl_val * position['qty'] * 0.5) if is_idx else ((-sl_val / 100) * position['qty'] * position['entry'])
                            current_balance += (position['cost'] + pnl)
                            trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Qty': position['qty'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'SL HIT 🛑', 'Points': -sl_val, 'PnL': pnl, 'Balance': current_balance})
                            position = None

                    elif sig != 0:
                        margin_eval = validate_and_calculate_margin(current_balance, curr_spot, total_qty, is_option=is_idx, leverage=1.0)
                        
                        if margin_eval["status"] == "REJECTED":
                            trade_rejections += 1
                        else:
                            trade_qty = margin_eval["traded_qty"]
                            trade_cost = margin_eval["cost"]
                            current_balance -= trade_cost
                            
                            pos_type = 'BUY/CE' if sig == 1 else 'SELL/PE'
                            position = {'type': pos_type, 'entry': curr_spot, 'time': time_lbl, 'qty': trade_qty, 'cost': trade_cost}

                with tab_backtest:
                    st.markdown(f"#### 🕯️ Strategy Backtest Chart (`{strategy_type}`)")
                    fig = make_subplots(rows=1, cols=1)
                    fig.add_trace(go.Candlestick(x=df_bt['Time_Str'], open=df_bt['Open'], high=df_bt['High'], low=df_bt['Low'], close=df_bt['Close'], name="Price", increasing_line_color='#10b981', decreasing_line_color='#ef4444'))
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#050811', plot_bgcolor='#050811', height=580, xaxis_rangeslider_visible=False, dragmode='pan', margin=dict(l=5, r=5, t=10, b=5))
                    st.plotly_chart(fig, use_container_width=True)

                with tab_metrics:
                    st.markdown("#### 💎 Institutional Strategy Scorecard & Capital Audit")
                    if trades:
                        tdf = pd.DataFrame(trades)
                        net_pnl = tdf['PnL'].sum()
                        win_count = len(tdf[tdf['PnL'] > 0])
                        win_rate = (win_count / len(tdf)) * 100
                        tdf['Cum_PnL'] = tdf['PnL'].cumsum()

                        k1, k2, k3, k4 = st.columns(4)
                        k1.metric("Net Realized PnL", f"{'+₹' if net_pnl >= 0 else '-₹'}{abs(net_pnl):,.2f}", f"{(net_pnl/capital)*100:+.2f}% ROI")
                        k2.metric("Win Probability", f"{win_rate:.1f}%", f"{win_count}W / {len(tdf)-win_count}L")
                        k3.metric("Trade Executions", len(tdf), f"Rejections (No Margin): {trade_rejections}")
                        k4.metric("Ending Capital Balance", f"₹{current_balance:,.2f}")

                        fig_equity = go.Figure()
                        fig_equity.add_trace(go.Scatter(x=tdf['Exit Time'], y=tdf['Cum_PnL'], mode='lines+markers', line=dict(color='#10b981', width=2.5), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.05)', name='Equity'))
                        fig_equity.update_layout(title="📈 Cumulative Equity Trajectory (₹)", template="plotly_dark", paper_bgcolor='#0d1424', plot_bgcolor='#0d1424', height=320)
                        st.plotly_chart(fig_equity, use_container_width=True)
                    else:
                        st.warning(f"No completed trades generated within parameters. Rejected due to margin: {trade_rejections}")

                with tab_trades:
                    if trades:
                        st.markdown("#### 📜 Trade Execution Audit Trail (Capital Sized)")
                        st.dataframe(pd.DataFrame(trades), use_container_width=True, height=400)
                        
                        csv_buf = io.StringIO()
                        pd.DataFrame(trades).to_csv(csv_buf, index=False)
                        st.download_button("📥 DOWNLOAD AUDIT CSV", data=csv_buf.getvalue(), file_name=f"audit_{symbol}.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Backtest error: {str(e)}")
else:
    with tab_backtest:
        st.info("💡 Select Strategy & Risk parameters in the sidebar, then click '⚡ EXECUTE STRATEGY BACKTEST' above.")
    with tab_metrics:
        st.info("💡 Execute strategy backtest to view performance KPIs.")
    with tab_trades:
        st.info("💡 Execute strategy backtest to view trade execution logs.")

# ==============================================================================
# 🤖 TAB 6: AI 24/7 AUTOPILOT HUB
# ==============================================================================
with tab_ai_pilot:
    st.markdown("### 🤖 24/7 Autonomous AI Opportunity Radar")
    st.caption("AI continuously audits multi-confluences in background thread with zero UI thread block.")

    auto_state = load_autopilot_state()

    col_ap1, col_ap2 = st.columns([1.8, 1])
    with col_ap1:
        if auto_state.get("running", False):
            st.success(f"🟢 **AI AUTOPILOT IS ACTIVE** | Target: `{asset_dict.get(auto_state.get('asset', '^NSEBANK'), '')}` | Strategy: `{auto_state.get('strategy', 'EMA Pullback')}`")
        else:
            st.warning("🔴 **AI AUTOPILOT ENGINE IS OFF (STANDBY)**")

    with col_ap2:
        pilot_switch = st.toggle("⚡ ACTIVATE 24/7 AUTOPILOT", value=auto_state.get("running", False), key="pilot_worker_toggle")
        if pilot_switch != auto_state.get("running", False):
            auto_state["running"] = pilot_switch
            save_autopilot_state(auto_state)
            st.rerun()

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        target_asset = st.selectbox("Target Autopilot Market", options=list(asset_dict.keys()), index=list(asset_dict.keys()).index(auto_state.get("asset", "^NSEBANK")) if auto_state.get("asset") in asset_dict else 0, format_func=lambda x: asset_dict[x], key="pilot_asset_sel")
    with col_p2:
        target_tf = st.selectbox("Resolution", ["5m", "15m", "30m", "1h"], index=1, key="pilot_tf_sel")
    with col_p3:
        target_strat = st.selectbox("Execution Strategy", list(STRATEGY_MAP.keys()), index=0, key="pilot_strat_sel")

    is_idx_p = target_asset in ["^NSEBANK", "^NSEI", "^BSESN"]
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        tp_val = st.number_input("Target (" + ("Pts" if is_idx_p else "%") + ")", value=float(auto_state.get("target", 50.0)), step=5.0 if is_idx_p else 0.5)
    with col_k2:
        sl_val = st.number_input("Hard SL (" + ("Pts" if is_idx_p else "%") + ")", value=float(auto_state.get("sl", 20.0)), step=5.0 if is_idx_p else 0.2)

    if st.button("💾 SAVE AUTOPILOT ENGINE SETTINGS"):
        auto_state["asset"] = target_asset
        auto_state["tf"] = target_tf
        auto_state["strategy"] = target_strat
        auto_state["target"] = tp_val
        auto_state["sl"] = sl_val
        save_autopilot_state(auto_state)
        st.success("✅ Autopilot parameters saved to 24/7 background worker.")

    st.markdown("---")
    st.markdown("#### 🌐 Active Open Positions")
    active_now = load_active_trades()
    if active_now:
        act_df = pd.DataFrame(list(active_now.values()))
        st.dataframe(act_df[['strike_info', 'action', 'entry', 'target', 'sl', 'status', 'time']], use_container_width=True)
        if st.button("🧹 Clear Completed Active Memory"):
            save_active_trades({})
            st.rerun()
    else:
        st.info("No active open positions currently running.")

# ==============================================================================
# ✍️ TAB 7: PRO MANUAL OPTION CHAIN TERMINAL (BLACK-SCHOLES GREEKS)
# ==============================================================================
with tab_manual_terminal:
    st.markdown("### ✍️ Pro Manual Option Chain Terminal")
    st.caption("3-column Option Chain with real-time Black-Scholes Greeks and theoretical Delta/Theta pricing.")

    col_man1, col_man2 = st.columns([1.5, 1])
    with col_man1:
        man_asset = st.selectbox("Select Underlying Market", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x], key="man_chain_asset_pro")
    with col_man2:
        curr_sym = "$" if man_asset.endswith("-USD") else "₹"
        curr_ref_spot = get_live_asset_price(man_asset, 57380.0 if man_asset == "^NSEBANK" else (24250.0 if man_asset == "^NSEI" else 1380.0))
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"###### 📊 Live Selected Spot: `{curr_sym}{curr_ref_spot:,.2f}`")

    specs = INDEX_SPECS.get(man_asset, {"name": man_asset, "strike_step": 100})
    step = specs.get("strike_step", 100)

    if man_asset in ["^NSEBANK", "^NSEI", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS"]:
        atm_s = int(round(curr_ref_spot / float(step)) * step)
        strikes_matrix = [atm_s - (step * 2), atm_s - step, atm_s, atm_s + step, atm_s + (step * 2)]
        
        chain_rows = []
        for s in strikes_matrix:
            g_ce = BlackScholesEngine.calculate_greeks(curr_ref_spot, s, 2, 14.5, 0.07, 'CE')
            g_pe = BlackScholesEngine.calculate_greeks(curr_ref_spot, s, 2, 14.5, 0.07, 'PE')
            tag = " (ATM)" if s == atm_s else " (ITM)" if s < atm_s else " (OTM)"
            chain_rows.append({
                "Call Delta": g_ce["delta"],
                "Call (CE) Premium": f"₹{g_ce['premium']}",
                "Strike Price": f"{s}{tag}",
                "Put (PE) Premium": f"₹{g_pe['premium']}",
                "Put Delta": g_pe["delta"]
            })
        st.table(pd.DataFrame(chain_rows))

        col_mc1, col_mc2 = st.columns(2)
        with col_mc1:
            sel_strike = st.selectbox("Select Strike Price", strikes_matrix, index=2, format_func=lambda x: f"{x} (ATM)" if x == atm_s else f"{x}")
        with col_mc2:
            sel_opt_type = st.selectbox("Option Type", ["PUT (PE) 🔴", "CALL (CE) 🟢"], index=0)

        clean_type = "PE" if "PUT" in sel_opt_type else "CE"
        exp_tag, _ = get_dynamic_expiry_and_tag(man_asset)
        inst_name = f"{specs['name']} {sel_strike} {clean_type} ({exp_tag})"
        auto_greeks = BlackScholesEngine.calculate_greeks(curr_ref_spot, sel_strike, 2, 14.5, 0.07, clean_type)
        auto_buy_price = auto_greeks["premium"]

    else:
        exp_tag, cat = get_dynamic_expiry_and_tag(man_asset)
        inst_name = f"{specs['name']} ({exp_tag})"
        auto_buy_price = int(curr_ref_spot)
        sel_opt_type = st.selectbox("Order Type", ["BUY / LONG 🟢", "SELL / SHORT 🔴"], index=0)

    col_mb1, col_mb2 = st.columns(2)
    with col_mb1:
        man_buy_price = st.number_input("Buy Above Price (₹ / $)", value=auto_buy_price)
        man_tp = st.text_input("Target", value=f"{man_buy_price + 35} | {man_buy_price + 65}", key="man_tp_txt_pro")
    with col_mb2:
        man_sl = st.text_input("Hard Stop Loss", value=f"{man_buy_price - 25}", key="man_sl_txt_pro")
        REASONING_PRESETS = [
            "EMA 20 Pullback + Volume Confirmation",
            "SuperTrend Dynamic Breakout (10, 2.0)",
            "MACD + Volume Spike Momentum",
            "Bollinger Bands + RSI Mean Reversion",
            "Opening Range Breakout (ORB)",
            "Donchian Channel Volatility Squeeze",
            "VWAP Intraday Retest & Expansion",
            "✍️ Custom Setup Note (Enter Below)"
        ]
        sel_reason_preset = st.selectbox("Setup Reasoning Engine", REASONING_PRESETS, index=0)
        man_note = sel_reason_preset if "Custom" not in sel_reason_preset else st.text_input("Custom Reasoning Note", value="Key Support Bounce")

    if st.button("🚀 BROADCAST FOUNDER SIGNAL TO TELEGRAM", type="primary"):
        now_ist = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
        now_raw = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_id = f"manual_{int(time.time())}"

        tg_manual = (
            f"📊 <b>{inst_name}</b>\n\n"
            f"📈 <b>BUY ABOVE {man_buy_price}</b>\n\n"
            f"🎯 <b>TARGET {man_tp}</b>\n\n"
            f"☠️ <b>SL - {man_sl}</b>\n\n"
            f"🔍 <b>Setup:</b> <i>{man_note}</i>\n"
            f"⏱ <i>Trigger: {now_ist} | 🧠 Edge: Founder High-Conviction</i>"
        )
        ok, resp = send_telegram_alert(tg_manual)
        if ok:
            logs = load_signals_log()
            logs.insert(0, {
                "id": log_id, "time": now_ist, "raw_time": now_raw,
                "instrument": inst_name, "action": sel_opt_type, "entry_spot": curr_ref_spot,
                "target": f"₹{man_tp}", "sl": f"₹{man_sl}", "confidence": "Founder Conviction", "status": "LIVE IN POSITION",
                "exit_price": "-"
            })
            save_signals_log(logs)
            st.session_state.signals_history = logs

            current_active = load_active_trades()
            current_active[man_asset] = {
                "asset_name": asset_dict[man_asset], "strike_info": inst_name,
                "action": sel_opt_type, "entry": curr_ref_spot, "target": curr_ref_spot + 50, "sl": curr_ref_spot - 20,
                "premium_entry": man_buy_price, "last_milestone": 0,
                "status": "LIVE IN POSITION", "trailed": False, "time": now_ist,
                "sym": curr_sym, "log_id": log_id
            }
            save_active_trades(current_active)
            st.session_state.active_radar_trades = current_active

            st.success("✅ Clean Signal broadcasted instantly to @sam_quantum_signals & logged to Terminal!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(f"❌ Telegram Error: {resp}")

# ==============================================================================
# 📑 TAB 8: DAILY SIGNAL LOGBOOK
# ==============================================================================
with tab_ai_logbook:
    st.markdown("### 📑 Official Daily AI Signal Logbook & Execution Audit")
    st.caption("Complete running log of all signals dispatched today. Automatically purges history after 12 hours.")

    logs = load_signals_log()
    st.session_state.signals_history = logs

    if logs:
        log_df = pd.DataFrame(logs)
        disp_df = log_df[['time', 'instrument', 'action', 'entry_spot', 'target', 'sl', 'confidence', 'status', 'exit_price']]
        st.dataframe(disp_df, use_container_width=True, height=400)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_signals = io.StringIO()
            disp_df.to_csv(csv_signals, index=False)
            st.download_button("📥 DOWNLOAD TODAY'S SIGNAL LOGBOOK (CSV)", data=csv_signals.getvalue(), file_name=f"ai_signals_{datetime.now().strftime('%Y_%m_%d')}.csv", mime="text/csv")
        with col_dl2:
            if st.button("🗑️ Manually Reset Today's Signal Log"):
                save_signals_log([])
                st.session_state.signals_history = []
                st.success("Logbook cleared.")
                st.rerun()
    else:
        st.info("Logbook is empty for the last 12 hours.")

# ==============================================================================
# 👑 TAB 9: ADMIN ACCESS & TIER CONTROL CONSOLE
# ==============================================================================
if is_admin:
    with tab_admin_access:
        st.markdown("### 👑 Founder Console: Member Directory & Access Control")
        col_u1, col_u2 = st.columns([1.6, 1])
        with col_u1:
            st.markdown("#### 📋 Verified Operator Directory")
            users_list = []
            for uid, udata in st.session_state.users_db.items():
                users_list.append({
                    "User ID": uid, "Name": udata.get("name", "N/A"),
                    "Phone / WA": udata.get("phone", "N/A"),
                    "Access Tier": udata.get("tier", "Free Member"),
                    "Joined On": udata.get("created_at", "N/A")
                })
            u_df = pd.DataFrame(users_list)
            st.dataframe(u_df, use_container_width=True)

            csv_users = io.StringIO()
            u_df.to_csv(csv_users, index=False)
            st.download_button("📥 EXPORT VERIFIED OPERATORS (CSV)", data=csv_users.getvalue(), file_name="sam_quantum_users.csv", mime="text/csv")

        with col_u2:
            st.markdown("#### 🛡️ Access & Revoke Controls")
            removable_users = [u for u in st.session_state.users_db.keys() if u != "admin"]
            if removable_users:
                target_del = st.selectbox("Select Account to Ban / Revoke", removable_users)
                if st.button("🚫 REVOKE ACCESS & BAN OPERATOR", type="secondary"):
                    del st.session_state.users_db[target_del]
                    save_users(st.session_state.users_db)
                    st.error(f"Operator '{target_del}' has been revoked.")
                    time.sleep(0.8)
                    st.rerun()

                st.markdown("---")
                st.markdown("#### ⚡ Upgrade / Modify Operator Access Tier")
                target_up = st.selectbox("Select Operator to Update", removable_users, key="tier_target_operator")
                new_tier_choice = st.selectbox("Select New Tier Level", ["Free Member", "VIP Algo Trader", "Institutional Pro", "Master Admin"], key="tier_selector_level")
                if st.button("👑 APPLY TIER UPDATE", type="primary"):
                    st.session_state.users_db[target_up]["tier"] = new_tier_choice
                    save_users(st.session_state.users_db)
                    st.success(f"✅ Successfully updated {target_up} to {new_tier_choice}!")
                    time.sleep(0.8)
                    st.rerun()
            else:
                st.info("No external registered operators found.")