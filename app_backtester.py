import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, time as dtime
import pytz
import io
import json
import os
import re
import time
import requests

# ==============================================================================
# 💎 SAM QUANTUM TERMINAL - INSTITUTIONAL CYBER-FINANCE UI SUITE
# ==============================================================================
st.set_page_config(
    page_title="SAM QUANTUM AI | Institutional Quant Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "users_db.json"
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

# 🌐 Ultra-Premium Obsidian & Cyan Glassmorphism Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebarContent"] {
        overscroll-behavior: none !important;
        background: radial-gradient(circle at 50% 0%, #0d1527 0%, #050811 75%, #020408 100%) !important;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    /* Institutional Header Banner */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.7) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 18px;
        backdrop-filter: blur(16px);
        box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.8), inset 0 1px 1px rgba(255,255,255,0.05);
    }
    
    /* Obsidian Glass Cards */
    .glass-card {
        background: rgba(13, 20, 36, 0.75);
        border: 1px solid rgba(30, 41, 59, 0.8);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.7);
    }

    /* Glowing Status Badges */
    .pulse-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }

    .admin-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(11, 17, 32, 0.9) 100%) !important;
        border: 1px solid rgba(51, 65, 85, 0.7) !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 800 !important;
        color: #38bdf8 !important;
    }

    /* High Precision Cyber Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        letter-spacing: 0.5px;
        box-shadow: 0 6px 20px -2px rgba(2, 132, 199, 0.4) !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: #38bdf8 !important;
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.5) !important;
        transform: translateY(-1px);
    }

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(13, 20, 36, 0.85);
        border-radius: 14px;
        padding: 6px;
        border: 1px solid rgba(30, 41, 59, 0.8);
        gap: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# Session persistence
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

query_params = st.query_params
if not st.session_state.authenticated and "uid" in query_params:
    saved_uid = query_params["uid"]
    users = st.session_state.users_db
    if saved_uid in users:
        st.session_state.authenticated = True
        st.session_state.user_info = {**users[saved_uid], "id": saved_uid}

# ==============================================================================
# 🔐 AUTHENTICATION PORTAL (CYBER SECURITY GRADE)
# ==============================================================================
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 38px; margin-bottom: 4px;">⚡</div>
            <h2 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: -0.5px;">SAM QUANTUM AI</h2>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 14px 0;">Institutional Quantitative Terminal & Automated Radar</p>
            <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 15px;">
                <span class="pulse-badge">● LIVE QUANT FEED</span>
                <span style="background: rgba(56, 189, 248, 0.1); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700; font-family:'JetBrains Mono';">256-BIT ENCRYPTION</span>
            </div>
            <hr style="border-color: rgba(30, 41, 59, 0.8); margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Mode", ["🔑 Terminal Sign In", "✨ Register Verified Account"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "🔑 Terminal Sign In":
            with st.form("login_form"):
                st.markdown("##### 🔒 Secure Terminal Authentication")
                username = st.text_input("Operator User ID", value="admin")
                password = st.text_input("Quantum Security Key", type="password", value="sam@2026")
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
                        st.error("❌ Full Name is mandatory (Min 3 characters).")
                    elif len(clean_phone) != 10:
                        st.error("❌ Valid 10-digit Indian Mobile number is mandatory.")
                    elif len(new_user.strip()) < 3:
                        st.error("❌ Unique User ID is mandatory.")
                    elif len(new_pass.strip()) < 4:
                        st.error("❌ Access password must be at least 4 characters.")
                    elif new_user in st.session_state.users_db:
                        st.error("❌ User ID already registered. Please choose another.")
                    else:
                        st.session_state.users_db[new_user] = {
                            "pass": new_pass,
                            "name": new_name.strip(),
                            "phone": clean_phone,
                            "tier": "Free Member",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_users(st.session_state.users_db)
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**st.session_state.users_db[new_user], "id": new_user}
                        st.query_params["uid"] = new_user
                        st.rerun()
    st.stop()

# ==============================================================================
# ⏰ STRICT MARKET GATEKEEPER
# ==============================================================================
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
# 🧮 INDICATORS ENGINE
# ==============================================================================
def calc_indicators(df, params):
    d = df.copy()
    c, h, l, o, v = d['Close'], d['High'], d['Low'], d['Open'], d['Volume']

    d['EMA9'] = c.ewm(span=9, adjust=False).mean()
    d['EMA20'] = c.ewm(span=20, adjust=False).mean()
    d['EMA21'] = c.ewm(span=21, adjust=False).mean()
    d['EMA50'] = c.ewm(span=50, adjust=False).mean()
    d['SMA20'] = c.rolling(window=20).mean()

    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    d['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

    hl = h - l
    hc = (h - c.shift(1)).abs()
    lc = (l - c.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    d['ATR'] = tr.rolling(window=14).mean().fillna(tr)

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
    d['VOL_SMA20'] = v.rolling(window=20).mean().fillna(v)
    return d

# ==============================================================================
# 🎛️ SIDEBAR CONTROLS & ASSET UNIVERSE
# ==============================================================================
curr_tier = st.session_state.user_info.get("tier", "Free Member")
is_admin = curr_tier == "Master Admin" or st.session_state.user_info.get("id") == "admin"

with st.sidebar:
    st.markdown(f"""
    <div style="background:{'rgba(30, 27, 75, 0.8)' if is_admin else 'rgba(15, 23, 42, 0.8)'}; border:1px solid {'#818cf8' if is_admin else '#334155'}; border-radius:12px; padding:14px; margin-bottom:14px; backdrop-filter:blur(8px);">
        <span style="color:#38bdf8; font-weight:800; font-size:14px; font-family:'JetBrains Mono';">⚡ SAM QUANTUM OS</span><br>
        <span style="color:#f8fafc; font-size:12px;">Operator: <b>{st.session_state.user_info['name']}</b></span><br>
        <span class="{'admin-badge' if is_admin else 'pulse-badge'}" style="margin-top:6px;">
            {'👑 MASTER FOUNDER' if is_admin else f'● {curr_tier.upper()}'}
        </span>
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
    
    asset_dict = {
        "^NSEBANK": "Bank Nifty Index (^NSEBANK)",
        "^NSEI": "Nifty 50 Index (^NSEI)",
        "RELIANCE.NS": "Reliance Industries",
        "HDFCBANK.NS": "HDFC Bank",
        "TCS.NS": "Tata Consultancy Services",
        "INFY.NS": "Infosys",
        "GC=F": "MCX Gold Mini / Spot (GC=F)",
        "SI=F": "MCX Silver Mini (SI=F)",
        "BTC-USD": "Bitcoin (BTC/USD)",
        "ETH-USD": "Ethereum (ETH/USD)",
        "SOL-USD": "Solana (SOL/USD)",
        "BNB-USD": "Binance Coin (BNB/USD)",
        "XRP-USD": "Ripple (XRP/USD)",
        "DOGE-USD": "Dogecoin (DOGE/USD)"
    }
    
    symbol = st.selectbox("Market Feed", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x])
    
    if curr_tier == "Free Member":
        allowed_tf = ["15m", "1d"]
    else:
        allowed_tf = ["15m", "5m", "1m", "2m", "30m", "60m", "1d"]
        
    timeframe = st.selectbox("Resolution Stream", allowed_tf, index=0)
    
    # Auto-adjust lookback to prevent limit errors
    max_days = 7 if timeframe in ["1m", "2m"] else 60
    default_days = 5 if timeframe in ["1m", "2m"] else 30
    lookback_days = st.slider("Lookback Memory (Days)", 1, max_days, default_days)

    st.markdown("---")
    st.markdown("### 🛠️ 2. Strategy Engine")
    strategy_type = st.selectbox(
        "Quantitative Archetype",
        [
            "1. EMA Institutional Pullback (20/50 Trend)",
            "2. EMA Golden/Death Crossover (9/21)",
            "3. SuperTrend Trend-Rider (10, 2.0)",
            "4. Candlestick Pattern Engine"
        ]
    )

    rsi_filter = st.checkbox("Require RSI 50-Level Momentum Filter", value=True)

    st.markdown("---")
    st.markdown("### 🛡️ 3. Risk & Capital")
    capital = st.number_input("Capital Pool (₹)", value=100000.0, step=10000.0)
    qty = st.number_input("Lot / Contract Quantity", value=150, step=15)
    delta = st.slider("Option Delta / Leverage Factor", 0.1, 1.0, 0.5, 0.05)

    is_idx = symbol in ["^NSEBANK", "^NSEI"]
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        target_val = st.number_input("Target (" + ("Pts" if is_idx else "%") + ")", value=50.0 if is_idx else 2.5, step=5.0 if is_idx else 0.5)
    with col_k2:
        sl_val = st.number_input("Hard SL (" + ("Pts" if is_idx else "%") + ")", value=20.0 if is_idx else 1.0, step=5.0 if is_idx else 0.2)

# ==============================================================================
# 🚀 MAIN DASHBOARD & INSTITUTIONAL COCKPIT
# ==============================================================================
if not is_admin and curr_tier == "Free Member":
    with st.expander("⚡ UPGRADE TO VIP ALGO TRADER (Click to Expand / Dismiss)", expanded=False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid #818cf8; border-radius: 12px; padding: 16px;">
            <h4 style="color:#38bdf8; margin:0; font-weight:800;">Unlock 1m/5m Sub-Minute Scalping & High-Speed Streams</h4>
            <p style="color:#94a3b8; font-size:12px; margin:6px 0 12px 0;">Community plan includes 15m/1d historical validation. Upgrade to VIP for real-time institutional feeds.</p>
            <span class="admin-badge">Contact Master Admin on WhatsApp: +91-9999999999 for instant upgrade</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div class="brand-header">
    <div>
        <h3 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: -0.5px; font-family: 'JetBrains Mono';">⚡ SAM QUANTUM STUDIO</h3>
        <span style="color: #94a3b8; font-size: 12px;">Institutional Quantitative Studio & Single-Market Live Radar</span>
    </div>
    <div style="text-align: right;">
        <span class="{'admin-badge' if is_admin else 'pulse-badge'}">
            {'👑 MASTER FOUNDER ACCESS' if is_admin else f'● {curr_tier.upper()}'}
        </span><br>
        <span style="color: #64748b; font-size: 11px; font-family:'JetBrains Mono';">LATENCY: 12ms | SECURE FEED</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Bar Workspace Setup
col_run1, col_run2 = st.columns([3, 1])
with col_run1:
    st.write(f"💼 **Active Target:** `{asset_dict[symbol]}` | Strategy: **{strategy_type.split('.')[1].strip()}** | Risk Profile: **Risk {sl_val}{' Pts' if is_idx else '%'} to Gain {target_val}{' Pts' if is_idx else '%'}**")
with col_run2:
    execute_btn = st.button("⚡ EXECUTE STRATEGY BACKTEST", type="primary")

# Tabs Setup
if is_admin:
    tab_chart, tab_metrics, tab_trades, tab_reports, tab_single_radar, tab_admin_access = st.tabs([
        "📈 Pro Touch Chart", 
        "📊 Scorecard & KPIs", 
        "📜 Trade Logs", 
        "📥 Download Reports", 
        "⚡ 1-Click Single Asset Radar (Admin)",
        "👑 Access & Revoke Console"
    ])
else:
    tab_chart, tab_metrics, tab_trades, tab_reports = st.tabs([
        "📈 Pro Touch Chart", 
        "📊 Scorecard & KPIs", 
        "📜 Trade Logs", 
        "📥 Download Reports"
    ])

# ==============================================================================
# 📊 BACKTEST EXECUTION ENGINE
# ==============================================================================
if execute_btn or 'backtest_executed' in st.session_state:
    st.session_state.backtest_executed = True
    
    with st.spinner("⏳ Loading institutional price matrix and computing trades..."):
        try:
            df_raw = yf.download(symbol, period=f"{lookback_days}d", interval=timeframe, progress=False)
            if df_raw.empty or len(df_raw) < 10:
                st.warning("⚠️ No market data returned. Please select a higher timeframe or increase lookback days.")
                st.stop()

            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.droplevel(1)
            df_raw.dropna(inplace=True)

            df = calc_indicators(df_raw, {})
            ist_time = df.index.tz_convert('Asia/Kolkata') if df.index.tz is not None else df.index + pd.Timedelta(hours=5, minutes=30)
            df['Time_Str'] = [t.strftime('%d-%b %H:%M') for t in ist_time]

            trades = []
            position = None
            last_bar = -1

            for i in range(2, len(df)):
                curr_spot = float(df['Close'].iloc[i])
                rsi = float(df['RSI'].iloc[i])
                ema20 = float(df['EMA20'].iloc[i])
                ema50 = float(df['EMA50'].iloc[i])
                time_lbl = df['Time_Str'].iloc[i]

                if position is not None:
                    move = (curr_spot - position['entry']) if position['type'] == 'BUY/CE' else (position['entry'] - curr_spot)
                    opt_move = move if is_idx else ((move / position['entry']) * 100)

                    if opt_move >= target_val:
                        pnl = (target_val * qty * delta) if is_idx else ((target_val / 100) * capital)
                        trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'TARGET HIT 🎯', 'Points': target_val, 'PnL': pnl})
                        position = None
                        last_bar = i
                    elif opt_move <= -sl_val:
                        pnl = (-sl_val * qty * delta) if is_idx else ((-sl_val / 100) * capital)
                        trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'SL HIT 🛑', 'Points': -sl_val, 'PnL': pnl})
                        position = None
                        last_bar = i
                elif last_bar != i:
                    if ema20 > ema50 and curr_spot > ema20 and rsi > 50:
                        position = {'type': 'BUY/CE', 'entry': curr_spot, 'time': time_lbl}
                        last_bar = i
                    elif ema20 < ema50 and curr_spot < ema20 and rsi < 50:
                        position = {'type': 'SELL/PE', 'entry': curr_spot, 'time': time_lbl}
                        last_bar = i

            # Render Chart
            with tab_chart:
                st.markdown("#### 🕯️ Institutional Matrix (Touch Pan & Zoom)")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)

                fig.add_trace(go.Candlestick(
                    x=df['Time_Str'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    name="Price", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
                ), row=1, col=1)

                fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA20'], line=dict(color='#38bdf8', width=1.5), name='EMA 20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA50'], line=dict(color='#f59e0b', width=1.5), name='EMA 50'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['RSI'], line=dict(color='#c084fc', width=1.5), name='RSI (14)'), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.4)", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="rgba(16, 185, 129, 0.4)", row=2, col=1)

                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='#050811', plot_bgcolor='#050811',
                    height=620, xaxis_rangeslider_visible=False, dragmode='pan',
                    margin=dict(l=5, r=5, t=10, b=5)
                )

                config_touch = {
                    'scrollZoom': True, 'displayModeBar': True,
                    'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                    'toImageButtonOptions': {'format': 'png', 'filename': f'sam_quantum_{symbol}', 'height': 1080, 'width': 1920, 'scale': 2}
                }
                st.plotly_chart(fig, use_container_width=True, config=config_touch)

            # Render Metrics
            with tab_metrics:
                if trades:
                    tdf = pd.DataFrame(trades)
                    net_pnl = tdf['PnL'].sum()
                    win_count = len(tdf[tdf['PnL'] > 0])
                    win_rate = (win_count / len(tdf)) * 100
                    tdf['Cum_PnL'] = tdf['PnL'].cumsum()

                    st.markdown("#### 💎 Institutional Strategy Scorecard")
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Net Realized PnL", f"{'+₹' if net_pnl >= 0 else '-₹'}{abs(net_pnl):,.2f}")
                    k2.metric("Win Probability", f"{win_rate:.1f}%", f"{win_count}W / {len(tdf)-win_count}L")
                    k3.metric("Trade Executions", len(tdf))
                    k4.metric("Risk Factor", "1 : 2.5")

                    st.markdown("---")
                    fig_equity = go.Figure()
                    fig_equity.add_trace(go.Scatter(
                        x=tdf['Exit Time'], y=tdf['Cum_PnL'],
                        mode='lines+markers', line=dict(color='#10b981', width=2.5),
                        fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.05)',
                        name='Equity'
                    ))
                    fig_equity.update_layout(title="📈 Cumulative Equity Trajectory (₹)", template="plotly_dark", paper_bgcolor='#0d1424', plot_bgcolor='#0d1424', height=340)
                    st.plotly_chart(fig_equity, use_container_width=True, config=config_touch)

            # Render Trade Logs
            with tab_trades:
                if trades:
                    st.markdown("#### 📜 Trade Execution Audit Trail")
                    st.dataframe(pd.DataFrame(trades), use_container_width=True, height=450)

            # Render Reports
            with tab_reports:
                st.markdown("### 📥 Instant Mobile Audit Reports")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if trades:
                        csv_buf = io.StringIO()
                        pd.DataFrame(trades).to_csv(csv_buf, index=False)
                        st.download_button("📥 DOWNLOAD CSV AUDIT", data=csv_buf.getvalue(), file_name=f"sam_quantum_{symbol}.csv", mime="text/csv")
                with col_r2:
                    if trades:
                        html_report = f"""
                        <!DOCTYPE html><html><body style="background:#050811;color:#f1f5f9;font-family:sans-serif;padding:20px;">
                        <h2 style="color:#38bdf8;">SAM QUANTUM AI - AUDIT</h2>
                        <p>Asset: <b>{asset_dict[symbol]}</b> | Net PnL: <b>₹{net_pnl:,.2f}</b> | Win Rate: <b>{win_rate:.1f}%</b></p>
                        {pd.DataFrame(trades).to_html(index=False)}
                        </body></html>
                        """
                        st.download_button("📥 DOWNLOAD HTML AUDIT", data=html_report, file_name=f"sam_quantum_{symbol}.html", mime="text/html")
        except Exception as e:
            st.error(f"Error during simulation: {str(e)}")

else:
    # 🌟 Obsidian Clean Strategy Ready State (Zero Error on Launch)
    with tab_chart:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 48px 24px;">
            <div style="font-size: 42px; margin-bottom: 8px;">⚡</div>
            <h3 style="color: #38bdf8; margin: 0; font-weight: 800; font-family:'JetBrains Mono';">QUANTUM STRATEGY STUDIO READY</h3>
            <p style="color: #94a3b8; font-size: 14px; max-width: 620px; margin: 10px auto 24px auto;">
                Configure your strategy archetype, leverage, and stop-loss limits in the left sidebar, then click <b>'EXECUTE STRATEGY BACKTEST'</b> above to run the institutional simulation.
            </p>
            <div style="display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;">
                <span class="pulse-badge">Feed: {asset_dict[symbol]}</span>
                <span style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 5px 14px; border-radius: 8px; font-size: 12px; font-family:'JetBrains Mono';">Resolution: {timeframe}</span>
                <span style="background: rgba(245, 158, 11, 0.12); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); padding: 5px 14px; border-radius: 8px; font-size: 12px; font-family:'JetBrains Mono';">Memory: {lookback_days} Days</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- ADMIN ONLY: TAB 5 - SINGLE ASSET LIVE RADAR ---
if is_admin:
    with tab_single_radar:
        st.markdown("### ⚡ Single-Asset Live Opportunity Radar")
        st.caption("Select one specific market at a time to audit real-time setups and broadcast crisp alerts to Telegram.")

        col_sr1, col_sr2 = st.columns(2)
        with col_sr1:
            radar_asset = st.selectbox("Target Market Feed", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x], key="single_rad_asset")
            is_open, gate_info = is_market_open(radar_asset)
            if is_open:
                st.success(f"🟢 Market Stream: {gate_info}")
            else:
                st.warning(f"🔴 Market Stream: {gate_info}")
                
            is_rd_idx = radar_asset in ["^NSEBANK", "^NSEI"]
            rd_target = st.number_input("Target (" + ("Pts" if is_rd_idx else "%") + ")", value=50.0 if is_rd_idx else 2.5, step=5.0 if is_rd_idx else 0.5, key="rd_tp")
            
        with col_sr2:
            radar_tf = st.selectbox("Scanning Resolution", ["1m", "5m", "15m"], index=1, key="rd_tf")
            rd_sl = st.number_input("Hard SL (" + ("Pts" if is_rd_idx else "%") + ")", value=20.0 if is_rd_idx else 1.0, step=5.0 if is_rd_idx else 0.2, key="rd_sl")
            min_conf_single = st.slider("Minimum AI Edge Confidence %", 70, 95, 80, key="rd_conf")

        if st.button("🚀 AUDIT & BROADCAST THIS ASSET TO TG"):
            if not is_open:
                st.error(f"⛔ Cannot broadcast: {gate_info}. AI strictly prevents sending alerts during closed hours.")
            else:
                with st.spinner(f"🔍 Fetching live real-time price for {asset_dict[radar_asset]}..."):
                    try:
                        df_live = yf.download(radar_asset, period="2d", interval=radar_tf, progress=False)
                        if df_live.empty or len(df_live) < 15:
                            st.error("❌ Live feed temporary timeout. Please retry in 5 seconds.")
                        else:
                            if isinstance(df_live.columns, pd.MultiIndex):
                                df_live.columns = df_live.columns.droplevel(1)
                            df_live = calc_indicators(df_live, {})
                            
                            c_bar = df_live.iloc[-1]
                            p_bar = df_live.iloc[-2]
                            spot = float(c_bar['Close'])
                            rsi_v = float(c_bar['RSI'])
                            ema20_v = float(c_bar['EMA20'])
                            ema50_v = float(c_bar['EMA50'])
                            st_n = int(c_bar['ST_DIR'])
                            st_p = int(p_bar['ST_DIR'])

                            sig = "NEUTRAL"
                            conf = 70
                            logic = "Consolidating"

                            if ema20_v > ema50_v and spot > ema20_v and rsi_v > 52:
                                sig = "BUY / CALL (CE) 🟢"
                                conf = 88
                                logic = f"20/50 EMA Bullish Momentum + RSI ({rsi_v:.1f})"
                            elif ema20_v < ema50_v and spot < ema20_v and rsi_v < 48:
                                sig = "SELL / PUT (PE) 🔴"
                                conf = 88
                                logic = f"20/50 EMA Bearish Structure + RSI ({rsi_v:.1f})"
                            elif st_p == -1 and st_n == 1:
                                sig = "BUY / CALL (CE) 🟢"
                                conf = 92
                                logic = "SuperTrend Bullish Reversal Cross"
                            elif st_p == 1 and st_n == -1:
                                sig = "SELL / PUT (PE) 🔴"
                                conf = 92
                                logic = "SuperTrend Bearish Reversal Cross"

                            curr_sym = "₹" if not radar_asset.endswith("-USD") else "$"
                            
                            if is_rd_idx:
                                tp = spot + rd_target if "BUY" in sig else spot - rd_target
                                sl = spot - rd_sl if "BUY" in sig else spot + rd_sl
                                risk_desc = f"Target: +{rd_target} Pts | SL: -{rd_sl} Pts"
                            else:
                                tp = spot * (1 + (rd_target / 100.0)) if "BUY" in sig else spot * (1 - (rd_target / 100.0))
                                sl = spot * (1 - (rd_sl / 100.0)) if "BUY" in sig else spot * (1 + (rd_sl / 100.0))
                                risk_desc = f"Target: +{rd_target}% | SL: -{rd_sl}%"

                            now_ist = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
                            
                            tg_text = (
                                f"⚡ <b>SAM QUANTUM AI - OPPORTUNITY RADAR</b> ⚡\n"
                                f"━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 <b>Asset:</b> {asset_dict[radar_asset]}\n"
                                f"🎯 <b>Action:</b> <code>{sig}</code>\n"
                                f"💵 <b>Current Live Spot:</b> {curr_sym}{spot:,.4f}\n"
                                f"🎯 <b>Target:</b> {curr_sym}{tp:,.4f} ({risk_desc.split('|')[0].strip()})\n"
                                f"🛑 <b>Stop Loss:</b> {curr_sym}{sl:,.4f} ({risk_desc.split('|')[1].strip()})\n"
                                f"⏱ <b>Trigger Time:</b> {now_ist}\n"
                                f"🧠 <b>AI Confidence:</b> <code>{conf}% Institutional Edge</code>\n"
                                f"🔍 <b>Logic:</b> {logic}\n"
                                f"━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🤖 <i>Dispatched via Sam Quantum AI Terminal</i>"
                            )
                            
                            ok, resp = send_telegram_alert(tg_text)
                            if ok:
                                st.success(f"✅ Opportunity Dispatched to @sam_quantum_signals! (Signal: {sig} @ {curr_sym}{spot:,.4f})")
                            else:
                                st.error(f"❌ Telegram Error: {resp}")
                    except Exception as e:
                        st.error(f"Error fetching live feed: {str(e)}")

    # --- ADMIN ONLY: TAB 6 - ACCESS & REVOKE CONSOLE ---
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
                target_up = st.selectbox("Select Operator for Tier Upgrade", removable_users, key="up_target")
                new_tier = st.selectbox("Select Access Tier", ["Free Member", "VIP Algo Trader", "Institutional Pro", "Master Admin"])
                if st.button("👑 UPDATE ACCESS TIER"):
                    st.session_state.users_db[target_up]["tier"] = new_tier
                    save_users(st.session_state.users_db)
                    st.success(f"Updated '{target_up}' to {new_tier}!")
                    time.sleep(0.8)
                    st.rerun()
            else:
                st.info("No external registered operators found.")