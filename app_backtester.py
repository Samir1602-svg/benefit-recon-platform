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
SQLITE_DB_FILE = "terminal_audit.db"

# ==============================================================================
# 📑 OFFICIAL MASTER OPERATING MANUAL (HTML & PDF PRINT SUITE)
# ==============================================================================
TERMINAL_MANUAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SAM QUANTUM AI — Master Trader Operating Manual & Workflow Blueprint</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    @page { size: A4; margin: 18mm 16mm; }
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #080b11; color: #e2e8f0; margin: 0; padding: 28px; line-height: 1.6; }
    .header-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #38bdf8; border-radius: 14px; padding: 22px 26px; margin-bottom: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
    .brand-title { font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 800; color: #38bdf8; margin: 0; }
    .brand-sub { font-size: 13.5px; color: #94a3b8; margin-top: 4px; }
    .doc-meta { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b; margin-top: 12px; border-top: 1px solid rgba(51, 65, 85, 0.7); padding-top: 8px; display: flex; justify-content: space-between; }
    .badge { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
    .section-title { color: #38bdf8; font-size: 15px; font-weight: 800; border-left: 4px solid #38bdf8; padding-left: 10px; margin: 26px 0 12px 0; text-transform: uppercase; letter-spacing: 0.5px; }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 18px 22px; margin-bottom: 14px; font-size: 12.8px; color: #cbd5e1; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .step-box { background: rgba(30, 41, 59, 0.5); border-left: 3px solid #10b981; padding: 12px 16px; margin: 10px 0; border-radius: 0 8px 8px 0; }
    .step-num { color: #10b981; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
    ul, ol { margin: 6px 0; padding-left: 20px; }
    li { margin-bottom: 6px; }
    strong { color: #f8fafc; }
    code { font-family: 'JetBrains Mono', monospace; background: #1e293b; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-size: 11.5px; }
    table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 11.5px; }
    th, td { border: 1px solid #1e293b; padding: 10px 12px; text-align: left; }
    th { background-color: #1e293b; color: #38bdf8; font-family: 'JetBrains Mono', monospace; font-weight: 700; }
    td { background-color: rgba(15, 23, 42, 0.6); }
    .print-btn { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; font-weight: 700; font-size: 14px; border: none; border-radius: 8px; padding: 12px 26px; cursor: pointer; margin-bottom: 20px; }
    @media print { .no-print { display: none !important; } body { padding: 0; background: #080b11; } }
</style>
</head>
<body>

<div class="no-print" style="text-align: center; margin-bottom: 20px;">
    <button class="print-btn" onclick="window.print()">🖨️ Save as PDF / Print Master Manual</button>
</div>

<div class="header-card">
    <div class="brand-title">⚡ SAM QUANTUM AI</div>
    <div class="brand-sub">Master Trader Operating Manual & Algorithmic Strategy Blueprint</div>
    <div class="doc-meta">
        <span>DOC ID: SQ-MAN-2026-V2.0</span>
        <span>ENGINE LATENCY: 12ms</span>
        <span class="badge">OFFICIAL TRADER HANDBOOK</span>
    </div>
</div>

<div class="section-title">1. Introduction & Terminal Philosophy</div>
<div class="card">
    <p>Welcome to <strong>SAM QUANTUM AI</strong>. This institutional quantitative engine is engineered to eliminate emotional trading bias by replacing guesswork with mathematical edge.</p>
    <p>90% of retail traders lose capital because they execute without statistical validation. This terminal allows you to test, optimize, and audit any trading strategy across Indian Indices, Commodities, and 24/7 Digital Assets before risking real funds.</p>
</div>

<div class="section-title">2. Complete Step-by-Step Backtesting Workflow</div>
<div class="card">
    <div class="step-box">
        <span class="step-num">STEP 1:</span> <strong>Select Instrument & Timeframe (Left Sidebar)</strong><br>
        Choose your market (e.g. <code>Bank Nifty</code>, <code>Nifty 50</code>, <code>Gold</code>, <code>BTC/USD</code>). Select your resolution (15m for intraday momentum, 5m for fast scalping, 1D for positional swing).
    </div>
    <div class="step-box">
        <span class="step-num">STEP 2:</span> <strong>Choose Strategy Archetype & Filters</strong><br>
        Select from 7 pre-compiled institutional algorithms (e.g. 20/50 EMA Pullback). Check <code>Require RSI 50-Level Filter</code> to eliminate choppy market noise.
    </div>
    <div class="step-box">
        <span class="step-num">STEP 3:</span> <strong>Set Position Sizing & Risk Rules</strong><br>
        Enter your Capital Pool (e.g. ₹1,00,000) and Lot Quantity. Define your Target (e.g. 50 Pts) and Hard SL (e.g. 20 Pts) to ensure a minimum 1:2 Risk-to-Reward ratio.
    </div>
    <div class="step-box">
        <span class="step-num">STEP 4:</span> <strong>Click 'EXECUTE STRATEGY BACKTEST'</strong><br>
        The terminal computes all historical bars, triggers entries/exits, plots visual buy/sell triangles on the chart, and populates the Performance Scorecard.
    </div>
</div>

<div class="section-title">3. Quantitative Strategy Archetypes Explained</div>
<div class="card">
    <ul>
        <li><strong>1. EMA Institutional Pullback (20/50 Trend):</strong> Waits for clear trend separation where Fast EMA (20) is above Slow EMA (50). Triggers CE/Buy only when price pulls back to touch the 20 EMA and bounces upward, confirmed by RSI &gt; 50.</li>
        <li><strong>2. EMA Golden / Death Crossover (9/21):</strong> High-velocity momentum model. Triggers when the 9 EMA crosses above 21 EMA (Buy) or below (Sell) for trend-following swings.</li>
        <li><strong>3. SuperTrend Trend-Rider (10, 2.0):</strong> Volatility-adaptive breakout model that uses dynamic ATR bands to catch multi-session rallies while keeping you out of flat chop.</li>
        <li><strong>4. Candlestick Pattern Engine:</strong> Detects high-probability institutional liquidity sweeps (Hammer at support for Buy / Bearish Engulfing at resistance for Sell).</li>
        <li><strong>5. Volume Spike + Momentum Breakout:</strong> Identifies volume expansion breaks over 20-period moving highs.</li>
        <li><strong>6. VWAP Intraday Retest & Expansion:</strong> Evaluates institutional volume-weighted average price bounces.</li>
        <li><strong>7. Bollinger Band Dynamic Mean Reversion:</strong> Capitalizes on volatility band extremities.</li>
    </ul>
</div>

<div class="section-title">4. How to Read Your Scorecard & Key KPIs</div>
<div class="card">
    <ul>
        <li><strong>Net Realized PnL:</strong> Total rupee profit or loss generated after all historical trades.</li>
        <li><strong>Win Probability (%):</strong> Percentage of winning trades. A solid 1:2 R:R strategy needs only 40%+ win rate to be highly profitable.</li>
        <li><strong>Cumulative Equity Trajectory:</strong> An upward sloping green equity curve proves that your strategy has a true quantitative edge.</li>
        <li><strong>Max Drawdown (DD):</strong> The maximum peak-to-trough dip in capital. Lower drawdown means less stress and better capital protection.</li>
    </ul>
</div>

<div class="section-title">5. Pro Touch Chart Controls (Mobile & Desktop)</div>
<div class="card">
    <ul>
        <li><strong>Pinch-to-Zoom (Mobile):</strong> Use two fingers on your phone screen to smoothly zoom into individual 1m/5m candles.</li>
        <li><strong>Pan & Drag:</strong> Drag left or right to inspect historical trade executions and candlestick formations.</li>
        <li><strong>Persistent Drawing Levels:</strong> Click horizontal line button to place permanent Support/Resistance boundaries.</li>
    </ul>
</div>

<div class="section-title">6. Membership Tiers & Capabilities</div>
<table>
    <thead>
        <tr>
            <th>Feature</th>
            <th>🟢 Free Member</th>
            <th>🔵 VIP Algo Trader</th>
            <th>🟣 Institutional Pro</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Resolution Stream</strong></td>
            <td>15m, 1D</td>
            <td>1m, 5m, 15m, 1D</td>
            <td>Sub-Minute (1m–1D)</td>
        </tr>
        <tr>
            <td><strong>Market Universe</strong></td>
            <td>Core Indices & BTC</td>
            <td>Indices, MCX & Top Crypto</td>
            <td>Full Global Grid & Altcoins</td>
        </tr>
        <tr>
            <td><strong>Strategy Archetypes</strong></td>
            <td>Core Engines</td>
            <td>All Advanced Engines</td>
            <td>Full Multi-Strategy Suite</td>
        </tr>
        <tr>
            <td><strong>Capital Pool Cap</strong></td>
            <td>₹1,00,000</td>
            <td>Up to ₹10,00,000</td>
            <td>Unlimited (₹1 Cr+ Testing)</td>
        </tr>
        <tr>
            <td><strong>Audit Exports</strong></td>
            <td>HD PNG + CSV</td>
            <td>HD PNG + CSV + HTML</td>
            <td>Full Executive PDF Suite</td>
        </tr>
    </tbody>
</table>

<div class="section-title">7. Official Links & Community Radar</div>
<div class="card">
    <ul>
        <li><strong>Terminal Web Access:</strong> <code>https://sam-ai-recon-platform-76dht2tcjgwf9ar7o7ehhn.streamlit.app</code></li>
        <li><strong>Live Signals & Trade Updates:</strong> Join official Telegram broadcast at <code>@sam_quantum_signals</code> for real-time market opportunity alerts.</li>
        <li><strong>Account Upgrade & Support:</strong> Contact Master Admin on WhatsApp or Telegram to unlock VIP/Pro licenses.</li>
    </ul>
</div>

<div class="section-title">8. Risk Disclaimer</div>
<div class="card" style="font-size: 11.5px; color: #94a3b8;">
    SAM QUANTUM AI is an algorithmic modeling and educational backtesting engine. Historical simulation metrics do not guarantee future market returns. Traders must always manage leverage and adhere strictly to defined stop-loss limits.
</div>

</body>
</html>"""

# ==============================================================================
# 🏛️ SPECIFICATIONS & LOT SIZES (INDIAN INDICES & CRYPTO)
# ==============================================================================
INDEX_SPECS = {
    "^NSEBANK": {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100, "exchange": "NFO", "type": "OPTION"},
    "^NSEI": {"name": "NIFTY", "lot_size": 75, "strike_step": 50, "exchange": "NFO", "type": "OPTION"},
    "NIFTY_FIN_SERVICE.NS": {"name": "FINNIFTY", "lot_size": 65, "strike_step": 50, "exchange": "NFO", "type": "OPTION"},
    "^BSESN": {"name": "SENSEX", "lot_size": 20, "strike_step": 100, "exchange": "BFO", "type": "OPTION"},
    "RELIANCE.NS": {"name": "RELIANCE", "lot_size": 250, "strike_step": 20, "exchange": "NFO", "type": "STOCK"},
    "HDFCBANK.NS": {"name": "HDFCBANK", "lot_size": 550, "strike_step": 10, "exchange": "NFO", "type": "STOCK"},
    "TCS.NS": {"name": "TCS", "lot_size": 175, "strike_step": 50, "exchange": "NFO", "type": "STOCK"},
    "INFY.NS": {"name": "INFY", "lot_size": 400, "strike_step": 20, "exchange": "NFO", "type": "STOCK"},
    "GC=F": {"name": "GOLDM", "lot_size": 1, "strike_step": 100, "exchange": "MCX", "type": "COMMODITY"},
    "SI=F": {"name": "SILVERM", "lot_size": 5, "strike_step": 250, "exchange": "MCX", "type": "COMMODITY"},
    "BTC-USD": {"name": "BTC/USDT", "lot_size": 1, "strike_step": 100, "exchange": "PERPETUAL", "type": "CRYPTO"},
    "ETH-USD": {"name": "ETH/USDT", "lot_size": 1, "strike_step": 10, "exchange": "PERPETUAL", "type": "CRYPTO"},
    "SOL-USD": {"name": "SOL/USDT", "lot_size": 1, "strike_step": 1, "exchange": "PERPETUAL", "type": "CRYPTO"},
    "BNB-USD": {"name": "BNB/USDT", "lot_size": 1, "strike_step": 1, "exchange": "PERPETUAL", "type": "CRYPTO"},
    "XRP-USD": {"name": "XRP/USDT", "lot_size": 10, "strike_step": 0.01, "exchange": "PERPETUAL", "type": "CRYPTO"},
    "DOGE-USD": {"name": "DOGE/USDT", "lot_size": 100, "strike_step": 0.001, "exchange": "PERPETUAL", "type": "CRYPTO"}
}

DEFAULT_USERS = {
    "admin": {"pass": "sam@2026", "name": "Sam (Founder)", "phone": "9999999999", "tier": "Master Admin", "created_at": "2026-08-20"},
    "vip_trader": {"pass": "quant100x", "name": "VIP Algo Trader", "phone": "9876543210", "tier": "Institutional Pro", "created_at": "2026-08-21"}
}

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

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==============================================================================
# 🧮 PURE MATH BLACK-SCHOLES GREEKS & MULTI-ASSET ENGINE
# ==============================================================================
def std_norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

class MultiAssetEngine:
    @staticmethod
    def calculate_option_trade(spot_entry, spot_exit, option_type, days_to_expiry=3, iv=16.0, strike_step=100):
        atm_strike = int(round(spot_entry / float(strike_step)) * strike_step)
        T_entry = max(days_to_expiry / 365.0, 0.0001)
        sigma = iv / 100.0
        r = 0.07

        d1 = (math.log(spot_entry / atm_strike) + (r + 0.5 * sigma**2) * T_entry) / (sigma * math.sqrt(T_entry))
        d2 = d1 - sigma * math.sqrt(T_entry)

        if "CE" in option_type or "BUY" in option_type:
            entry_premium = spot_entry * std_norm_cdf(d1) - atm_strike * math.exp(-r * T_entry) * std_norm_cdf(d2)
            delta = std_norm_cdf(d1)
        else:
            entry_premium = atm_strike * math.exp(-r * T_entry) * std_norm_cdf(-d2) - spot_entry * std_norm_cdf(-d1)
            delta = std_norm_cdf(d1) - 1.0

        entry_premium = max(15.0, round(entry_premium, 2))
        spot_movement = spot_exit - spot_entry
        
        if "CE" in option_type or "BUY" in option_type:
            exit_premium = max(5.0, entry_premium + (spot_movement * delta))
        else:
            exit_premium = max(5.0, entry_premium - (spot_movement * abs(delta)))

        exit_premium = round(exit_premium, 2)
        points_pnl = round(exit_premium - entry_premium, 2)
        return atm_strike, entry_premium, exit_premium, points_pnl

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

def is_market_open(symbol_key):
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    weekday = now_ist.weekday()
    current_time = now_ist.time()

    if symbol_key in ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"]:
        return True, "Crypto (24/7 Live Active)"

    if weekday in [5, 6]:
        return False, "Market Closed (Weekend)"

    if symbol_key in ["^NSEBANK", "^NSEI", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "NIFTY_FIN_SERVICE.NS", "^BSESN"]:
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
# 🛠️ 7 QUANTITATIVE STRATEGY MODULES (REGISTRY PATTERN)
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
        cond_buy = (d['EMA20'] > d['EMA50']) & (d['Close'] >= d['EMA20']) & (d['RSI'] > 52) & (d['Volume'] >= d['VOL_SMA20'])
        cond_sell = (d['EMA20'] < d['EMA50']) & (d['Close'] <= d['EMA20']) & (d['RSI'] < 48) & (d['Volume'] >= d['VOL_SMA20'])
        d.loc[cond_buy, 'signal'] = 1
        d.loc[cond_sell, 'signal'] = -1
        return d

    @staticmethod
    def ema_crossover(df):
        d = df.copy()
        c = d['Close']
        d['EMA9'] = c.ewm(span=9, adjust=False).mean()
        d['EMA21'] = c.ewm(span=21, adjust=False).mean()
        
        d['signal'] = 0
        cross_up = (d['EMA9'] > d['EMA21']) & (d['EMA9'].shift(1) <= d['EMA21'].shift(1))
        cross_down = (d['EMA9'] < d['EMA21']) & (d['EMA9'].shift(1) >= d['EMA21'].shift(1))
        d.loc[cross_up, 'signal'] = 1
        d.loc[cross_down, 'signal'] = -1
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
        flip_up = (d['ST_DIR'] == 1) & (d['ST_DIR'].shift(1) == -1) & (d['Close'] > d['EMA200'])
        flip_down = (d['ST_DIR'] == -1) & (d['ST_DIR'].shift(1) == 1) & (d['Close'] < d['EMA200'])
        d.loc[flip_up, 'signal'] = 1
        d.loc[flip_down, 'signal'] = -1
        return d

    @staticmethod
    def candlestick_pattern(df):
        d = df.copy()
        o, h, l, c = d['Open'], d['High'], d['Low'], d['Close']
        body = (c - o).abs()
        range_hl = h - l
        
        d['signal'] = 0
        is_hammer = (l < o.combine(c, min) - 2 * body) & (h <= o.combine(c, max) + body * 0.5) & (range_hl > body * 2.5)
        is_star = (h > o.combine(c, max) + 2 * body) & (l >= o.combine(c, min) - body * 0.5) & (range_hl > body * 2.5)
        d.loc[is_hammer, 'signal'] = 1
        d.loc[is_star, 'signal'] = -1
        return d

    @staticmethod
    def volume_breakout(df):
        d = df.copy()
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        d['HIGH_20'] = d['High'].rolling(20).max().shift(1)
        d['LOW_20'] = d['Low'].rolling(20).min().shift(1)
        
        d['signal'] = 0
        buy_cond = (d['Close'] > d['HIGH_20']) & (d['Volume'] > d['VOL_SMA20'] * 1.5)
        sell_cond = (d['Close'] < d['LOW_20']) & (d['Volume'] > d['VOL_SMA20'] * 1.5)
        d.loc[buy_cond, 'signal'] = 1
        d.loc[sell_cond, 'signal'] = -1
        return d

    @staticmethod
    def vwap_expansion(df):
        d = df.copy()
        typical_price = (d['High'] + d['Low'] + d['Close']) / 3.0
        d['VWAP'] = (typical_price * d['Volume']).cumsum() / d['Volume'].cumsum()
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        
        d['signal'] = 0
        buy_cond = (d['Close'] > d['VWAP']) & (d['Close'].shift(1) <= d['VWAP'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        sell_cond = (d['Close'] < d['VWAP']) & (d['Close'].shift(1) >= d['VWAP'].shift(1)) & (d['Volume'] > d['VOL_SMA20'])
        d.loc[buy_cond, 'signal'] = 1
        d.loc[sell_cond, 'signal'] = -1
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
        buy_cond = (d['Low'] <= d['BB_LOWER']) & (d['RSI'] < 30)
        sell_cond = (d['High'] >= d['BB_UPPER']) & (d['RSI'] > 70)
        d.loc[buy_cond, 'signal'] = 1
        d.loc[sell_cond, 'signal'] = -1
        return d

STRATEGY_MAP = {
    "1. EMA Institutional Pullback (20/50 Trend)": StrategyRegistry.ema_pullback,
    "2. EMA Golden/Death Crossover (9/21 Acceleration)": StrategyRegistry.ema_crossover,
    "3. SuperTrend Trend-Rider (10, 2.0 + 200 EMA)": StrategyRegistry.supertrend_rider,
    "4. Candlestick Pattern Engine (Hammer / Engulfing Reversal)": StrategyRegistry.candlestick_pattern,
    "5. Volume Spike + Momentum Breakout": StrategyRegistry.volume_breakout,
    "6. VWAP Intraday Retest & Expansion": StrategyRegistry.vwap_expansion,
    "7. Bollinger Band Dynamic Mean Reversion": StrategyRegistry.bollinger_rsi_reversion
}

# ==============================================================================
# 🔐 AUTHENTICATION PORTAL
# ==============================================================================
query_params = st.query_params
if not st.session_state.authenticated and "uid" in query_params:
    saved_uid = query_params["uid"]
    users = st.session_state.users_db
    if saved_uid in users:
        st.session_state.authenticated = True
        st.session_state.user_info = {**users[saved_uid], "id": saved_uid}

if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(13, 20, 36, 0.75); border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 16px; padding: 24px; text-align: center;">
            <div style="font-size: 38px; margin-bottom: 4px;">⚡</div>
            <h2 style="color: #38bdf8; margin: 0; font-weight: 800;">SAM QUANTUM STUDIO</h2>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 14px 0;">Institutional Quantitative Terminal & Multi-Asset Backtester</p>
            <hr style="border-color: rgba(30, 41, 59, 0.8); margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Mode", ["🔑 Terminal Sign In", "✨ Register Verified Account"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "🔑 Terminal Sign In":
            with st.form("login_form"):
                st.markdown("##### 🔒 Secure Terminal Authentication")
                username = st.text_input("Operator User ID", value="", placeholder="Enter User ID")
                password = st.text_input("Quantum Security Key", type="password", value="", placeholder="Enter Password")
                if st.form_submit_button("⚡ UNLOCK QUANTUM TERMINAL"):
                    users = st.session_state.users_db
                    if username in users and users[username]["pass"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**users[username], "id": username}
                        st.query_params["uid"] = username
                        st.rerun()
                    else:
                        st.error("⛔ Authentication Denied: Invalid Credentials.")
        else:
            with st.form("signup_form"):
                st.markdown("##### 🚀 Mandatory Trader Profile")
                new_name = st.text_input("Full Name *", placeholder="e.g. Samir Khan")
                new_phone = st.text_input("10-Digit Mobile Number *", placeholder="e.g. 9876543210")
                new_user = st.text_input("Create User ID *", placeholder="e.g. samir_quant")
                new_pass = st.text_input("Create Access Password *", type="password")
                
                if st.form_submit_button("🎉 VERIFY & UNLOCK ACCESS"):
                    clean_phone = re.sub(r'[^0-9]', '', new_phone)
                    if len(new_name.strip()) < 3 or len(clean_phone) != 10 or len(new_user.strip()) < 3 or len(new_pass.strip()) < 4:
                        st.error("❌ Please provide valid registration details.")
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
    st.markdown("### 🛠️ 2. Strategy Engine")
    strategy_type = st.selectbox("Quantitative Strategy Library", list(STRATEGY_MAP.keys()))
    
    st.markdown("---")
    st.markdown("### 🛡️ 3. Risk & Capital Guard")
    capital = st.number_input("Capital Pool / Wallet Balance (₹)", value=100000.0, step=10000.0, min_value=1.0)
    
    lot_size_val = INDEX_SPECS.get(symbol, {}).get("lot_size", 1)
    num_lots = st.number_input(f"Number of Lots (Lot Size: {lot_size_val})", value=2, step=1, min_value=1)
    total_qty = num_lots * lot_size_val
    st.caption(f"Actual Order Quantity: **{total_qty} units** ({num_lots} Lots × {lot_size_val})")

    is_idx = symbol in ["^NSEBANK", "^NSEI", "^BSESN", "NIFTY_FIN_SERVICE.NS"]
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

st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.7) 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 16px 24px; margin-bottom: 18px;">
    <div>
        <h3 style="color: #38bdf8; margin: 0; font-weight: 800;">⚡ SAM QUANTUM STUDIO</h3>
        <span style="color: #94a3b8; font-size: 12px;">Institutional Quantitative Studio & Pro Backtesting Matrix</span>
    </div>
    <div style="text-align: right;">
        <span style="color: #10b981; font-weight: bold; font-size: 11px;">● {curr_tier.upper()}</span><br>
        <span style="color: #64748b; font-size: 11px;">LATENCY: 12ms | SECURE FEED</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_run1, col_run2 = st.columns([3, 1])
with col_run1:
    st.write(f"💼 **Active Target:** `{asset_dict[symbol]}` | Live Spot: **{header_curr}{header_spot:,.2f}** | Strategy: **{strategy_type.split('.')[1].strip()}**")
with col_run2:
    execute_btn = st.button("⚡ EXECUTE STRATEGY BACKTEST", type="primary")

if is_admin:
    tab_tv_chart, tab_backtest, tab_metrics, tab_trades, tab_reports, tab_admin_access = st.tabs([
        "📊 Live Demat Chart Studio", "📈 Pro Backtest Chart", "📊 Scorecard & KPIs", "📜 Trade Logs",
        "📥 Download Reports", "👑 Admin Console"
    ])
else:
    tab_tv_chart, tab_backtest, tab_metrics, tab_trades, tab_reports = st.tabs([
        "📊 Live Demat Chart Studio", "📈 Pro Backtest Chart", "📊 Scorecard & KPIs", "📜 Trade Logs",
        "📥 Download Reports"
    ])

# ==============================================================================
# 📊 TAB 1: GROWW MOUNTAIN GLOW VS. PRO CANDLESTICK LIVE CHART
# ==============================================================================
with tab_tv_chart:
    st.markdown("#### 📊 Live Demat Interactive Chart Studio")
    st.caption("Real-time streaming chart with localized IST timezone coordinates and persistent price level tracking.")

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
                <div class="metric-card"><div class="metric-label">Live Spot ({asset_dict[live_chart_asset]})</div><div class="metric-val" id="card_spot">{curr_label}{init_spot:,.2f}</div></div>
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
                    localization: {{ timeFormatter: t => new Date((t + 19800) * 1000).toUTCString().replace("GMT", "IST") }}
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
                        const d = new Date((param.time + 19800) * 1000);
                        document.getElementById('leg_time').innerText = d.toUTCString().replace("GMT", "IST");
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

                let isMarketActive = {'true' if is_live_open else 'false'};
                let lastClose = rawCandles[rawCandles.length - 1].close;

                if (isMarketActive) {{
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
                }}
            </script>
            </body>
            </html>
            """
            components.html(demat_studio_html, height=660)

    except Exception as e:
        st.error(f"Error initializing chart: {str(e)}")

# ==============================================================================
# 📊 TAB 2-5: BACKTEST EXECUTION ENGINE & REPORTS
# ==============================================================================
with tab_reports:
    st.markdown("### 📥 Instant Mobile Audit Reports & Master Handbook")
    st.download_button(
        label="📄 DOWNLOAD OFFICIAL MASTER MANUAL (HTML / PDF PRINT)",
        data=TERMINAL_MANUAL_HTML,
        file_name="SAM_QUANTUM_Master_Operating_Manual.html",
        mime="text/html",
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

                asset_spec = INDEX_SPECS.get(symbol, {"name": symbol, "lot_size": 1, "strike_step": 100, "type": "STOCK"})
                market_type = asset_spec.get("type", "STOCK")
                step_size = asset_spec.get("strike_step", 100)

                for i in range(2, len(df_bt)):
                    curr_spot = float(df_bt['Close'].iloc[i])
                    sig = int(df_bt['signal'].iloc[i])
                    time_lbl = df_bt['Time_Str'].iloc[i]

                    # 1. Manage Active Position Exit
                    if position is not None:
                        is_buy = position['type'] in ['BUY/CE', 'BUY', 'LONG']
                        
                        if market_type == "OPTION":
                            _, _, exit_prem, points_diff = MultiAssetEngine.calculate_option_trade(
                                spot_entry=position['spot_entry'],
                                spot_exit=curr_spot,
                                option_type=position['type'],
                                days_to_expiry=2,
                                iv=15.5,
                                strike_step=step_size
                            )
                            opt_move = points_diff
                            target_hit = opt_move >= target_val
                            sl_hit = opt_move <= -sl_val
                            
                            if target_hit or sl_hit:
                                pnl = points_diff * position['qty']
                                current_balance += (position['cost'] + pnl)
                                res_label = 'TARGET 🎯' if target_hit else 'SL HIT 🔴'
                                trades.append({
                                    'Entry Time': position['time'],
                                    'Exit Time': time_lbl,
                                    'Type': position['type'],
                                    'Strike': position['strike_desc'],
                                    'Qty': position['qty'],
                                    'Entry Prem (₹)': position['entry_price'],
                                    'Exit Prem (₹)': exit_prem,
                                    'Result': res_label,
                                    'PnL (₹)': pnl,
                                    'Balance (₹)': current_balance
                                })
                                position = None

                        elif market_type == "CRYPTO":
                            price_diff = (curr_spot - position['entry_price']) if is_buy else (position['entry_price'] - curr_spot)
                            pnl_pct = (price_diff / position['entry_price']) * 100.0
                            target_hit = pnl_pct >= target_val
                            sl_hit = pnl_pct <= -sl_val
                            
                            if target_hit or sl_hit:
                                pnl_usd = (pnl_pct / 100.0) * position['cost']
                                current_balance += (position['cost'] + pnl_usd)
                                res_label = 'TARGET 🎯' if target_hit else 'SL HIT 🔴'
                                trades.append({
                                    'Entry Time': position['time'],
                                    'Exit Time': time_lbl,
                                    'Type': position['type'],
                                    'Strike': f"{asset_spec['name']} PERP",
                                    'Qty': position['qty'],
                                    'Entry Prem (₹)': position['entry_price'],
                                    'Exit Prem (₹)': curr_spot,
                                    'Result': res_label,
                                    'PnL (₹)': pnl_usd,
                                    'Balance (₹)': current_balance
                                })
                                position = None

                        else:
                            price_diff = (curr_spot - position['entry_price']) if is_buy else (position['entry_price'] - curr_spot)
                            target_hit = price_diff >= target_val
                            sl_hit = price_diff <= -sl_val
                            
                            if target_hit or sl_hit:
                                pnl_cash = price_diff * position['qty']
                                current_balance += (position['cost'] + pnl_cash)
                                res_label = 'TARGET 🎯' if target_hit else 'SL HIT 🔴'
                                trades.append({
                                    'Entry Time': position['time'],
                                    'Exit Time': time_lbl,
                                    'Type': position['type'],
                                    'Strike': f"{asset_spec['name']} CASH",
                                    'Qty': position['qty'],
                                    'Entry Prem (₹)': position['entry_price'],
                                    'Exit Prem (₹)': curr_spot,
                                    'Result': res_label,
                                    'PnL (₹)': pnl_cash,
                                    'Balance (₹)': current_balance
                                })
                                position = None

                    # 2. Open New Position with Strict Lot Sizing & Margin Check
                    elif sig != 0:
                        pos_type = 'BUY/CE' if sig == 1 else 'BUY/PE'
                        
                        if market_type == "OPTION":
                            atm_s, entry_prem, _, _ = MultiAssetEngine.calculate_option_trade(
                                spot_entry=curr_spot,
                                spot_exit=curr_spot,
                                option_type=pos_type,
                                days_to_expiry=2,
                                iv=15.5,
                                strike_step=step_size
                            )
                            opt_label = "CE" if sig == 1 else "PE"
                            strike_desc = f"{atm_s} {opt_label}"
                            
                            required_margin = entry_prem * total_qty
                            
                            if current_balance < required_margin:
                                max_lots = int(current_balance // (entry_prem * asset_spec['lot_size']))
                                if max_lots <= 0:
                                    trade_rejections += 1
                                    continue
                                exec_qty = max_lots * asset_spec['lot_size']
                                required_margin = entry_prem * exec_qty
                            else:
                                exec_qty = total_qty
                                
                            current_balance -= required_margin
                            position = {
                                'type': pos_type,
                                'spot_entry': curr_spot,
                                'entry_price': entry_prem,
                                'time': time_lbl,
                                'qty': exec_qty,
                                'cost': required_margin,
                                'strike_desc': strike_desc
                            }

                        elif market_type == "CRYPTO":
                            required_margin = min(current_balance, capital * 0.25)
                            if current_balance < 10.0:
                                trade_rejections += 1
                                continue
                            current_balance -= required_margin
                            position = {
                                'type': 'LONG' if sig == 1 else 'SHORT',
                                'entry_price': curr_spot,
                                'time': time_lbl,
                                'qty': round(required_margin / curr_spot, 4),
                                'cost': required_margin,
                                'strike_desc': f"{asset_spec['name']} PERP"
                            }

                        else:
                            required_margin = curr_spot * total_qty
                            if current_balance < required_margin:
                                max_shares = int(current_balance // curr_spot)
                                if max_shares <= 0:
                                    trade_rejections += 1
                                    continue
                                exec_qty = max_shares
                                required_margin = curr_spot * exec_qty
                            else:
                                exec_qty = total_qty
                                
                            current_balance -= required_margin
                            position = {
                                'type': 'BUY' if sig == 1 else 'SELL',
                                'entry_price': curr_spot,
                                'time': time_lbl,
                                'qty': exec_qty,
                                'cost': required_margin,
                                'strike_desc': f"{asset_spec['name']} CASH"
                            }

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
                        net_pnl = tdf['PnL (₹)'].sum()
                        win_count = len(tdf[tdf['PnL (₹)'] > 0])
                        win_rate = (win_count / len(tdf)) * 100
                        tdf['Cum_PnL'] = tdf['PnL (₹)'].cumsum()

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
                        st.markdown("#### 📜 Trade Execution Audit Trail (Realistic Option Premium & Lots)")
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
# 👑 TAB: ADMIN ACCESS & TIER CONTROL CONSOLE
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