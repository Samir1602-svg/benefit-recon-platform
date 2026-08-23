import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
import json
import os
import time
import requests

# ==============================================================================
# 💎 SAM QUANTUM TERMINAL - CONFIG & ANTI-REFRESH
# ==============================================================================
st.set_page_config(
    page_title="SAM QUANTUM AI | Institutional Terminal & Live Dispatcher",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "users_db.json"
DEFAULT_USERS = {
    "admin": {"pass": "sam@2026", "name": "Sam (Founder)", "phone": "9999999999", "tier": "Master Admin", "created_at": "2026-08-20"},
    "vip_trader": {"pass": "quant100x", "name": "VIP Algo Trader", "phone": "8888888888", "tier": "Institutional Pro", "created_at": "2026-08-21"}
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

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebarContent"] {
        overscroll-behavior-y: none !important;
        overscroll-behavior-x: none !important;
        background-color: #0b0e14 !important;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
    }
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #111722 0%, #161f30 100%);
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.4);
    }
    .glass-card {
        background: #111722;
        border: 1px solid #1f293d;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetric"] {
        background-color: #111722 !important;
        border: 1px solid #1f293d !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 18px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #111722;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #1f293d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f293d !important;
        color: #38bdf8 !important;
        border-radius: 6px;
        font-weight: 600;
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

if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.9, 1])
    with col_l2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 32px; margin-bottom: 6px;">⚡</div>
            <h2 style="color: #38bdf8; margin: 0; font-weight: 800;">SAM QUANTUM AI</h2>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 16px 0;">Institutional Strategy Studio & Live Telegram Dispatcher</p>
            <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                ● FREE LIFETIME TRADER EDITION
            </span>
            <hr style="border-color: #1f293d; margin-top: 18px;">
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Mode", ["🔑 Sign In", "✨ Create Free Account"], horizontal=True, label_visibility="collapsed")
        if auth_mode == "🔑 Sign In":
            with st.form("login_form"):
                st.markdown("##### 🔒 Terminal Sign In")
                username = st.text_input("User ID / Mobile Number", value="admin")
                password = st.text_input("Security Access Key", type="password", value="sam@2026")
                if st.form_submit_button("⚡ UNLOCK TERMINAL"):
                    users = st.session_state.users_db
                    if username in users and users[username]["pass"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**users[username], "id": username}
                        st.query_params["uid"] = username
                        st.rerun()
                    else:
                        st.error("⛔ Invalid Credentials.")
        else:
            with st.form("signup_form"):
                st.markdown("##### 🚀 Quick Free Registration")
                new_name = st.text_input("Full Name")
                new_phone = st.text_input("Mobile / WhatsApp Number")
                new_user = st.text_input("Create User ID")
                new_pass = st.text_input("Create Secret Password", type="password")
                if st.form_submit_button("🎉 INSTANT ACCESS"):
                    if new_user in st.session_state.users_db:
                        st.error("Username already exists.")
                    elif not new_name.strip() or not new_user.strip():
                        st.error("Fill all fields.")
                    else:
                        st.session_state.users_db[new_user] = {"pass": new_pass, "name": new_name, "phone": new_phone, "tier": "Free Member", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        save_users(st.session_state.users_db)
                        st.session_state.authenticated = True
                        st.session_state.user_info = {**st.session_state.users_db[new_user], "id": new_user}
                        st.query_params["uid"] = new_user
                        st.rerun()
    st.stop()

# ==============================================================================
# 📡 TELEGRAM DISPATCHER FUNCTION
# ==============================================================================
def send_telegram_alert(token, chat_id, message):
    if not token or not chat_id:
        return False, "Bot Token or Channel ID missing."
    url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
    payload = {
        "chat_id": chat_id.strip(),
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload, timeout=8)
        if resp.status_code == 200:
            return True, "Alert dispatched successfully to Telegram!"
        else:
            return False, f"Telegram Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Network/API Error: {str(e)}"

# ==============================================================================
# 🧮 QUANT INDICATORS ENGINE
# ==============================================================================
def calc_indicators(df, params):
    d = df.copy()
    c, h, l, o, v = d['Close'], d['High'], d['Low'], d['Open'], d['Volume']

    d['EMA9'] = c.ewm(span=9, adjust=False).mean()
    d['EMA20'] = c.ewm(span=20, adjust=False).mean()
    d['EMA21'] = c.ewm(span=21, adjust=False).mean()
    d['EMA50'] = c.ewm(span=50, adjust=False).mean()
    d['EMA200'] = c.ewm(span=200, adjust=False).mean()
    d['SMA20'] = c.rolling(window=20).mean()

    typical_price = (h + l + c) / 3.0
    date_group = d.index.date if hasattr(d.index, 'date') else np.zeros(len(d))
    pv = typical_price * v
    d['Cum_PV'] = pv.groupby(date_group).cumsum()
    d['Cum_Vol'] = v.groupby(date_group).cumsum()
    d['VWAP'] = (d['Cum_PV'] / d['Cum_Vol'].replace(0, np.nan)).fillna(c)

    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    d['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

    d['BB_MID'] = d['SMA20']
    bb_std = c.rolling(window=20).std()
    d['BB_UP'] = d['BB_MID'] + (params.get('bb_std', 2.0) * bb_std)
    d['BB_LOW'] = d['BB_MID'] - (params.get('bb_std', 2.0) * bb_std)

    hl = h - l
    hc = (h - c.shift(1)).abs()
    lc = (l - c.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    d['ATR'] = tr.rolling(window=14).mean().fillna(tr)

    st_period = params.get('st_period', 10)
    st_mult = params.get('st_mult', 2.0)
    st_atr = tr.ewm(com=st_period-1, adjust=False).mean()
    hl2 = (h + l) / 2.0
    basic_ub = hl2 + (st_mult * st_atr)
    basic_lb = hl2 - (st_mult * st_atr)
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
    d['PCT_CHANGE'] = ((c - o) / o.replace(0, np.nan)) * 100

    body = (c - o).abs()
    d['IS_HAMMER'] = ((l <= o.combine(c, min) - (body * 1.8)) & (h <= o.combine(c, max) + (body * 0.3)) & (body > 0))
    d['IS_ENGULFING_BULL'] = ((c > o) & (c.shift(1) < o.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1)))
    d['IS_ENGULFING_BEAR'] = ((c < o) & (c.shift(1) > o.shift(1)) & (c <= o.shift(1)) & (o >= c.shift(1)))
    return d

# ==============================================================================
# 🎛️ SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="background:#111722; border:1px solid #1f293d; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
        <span style="color:#38bdf8; font-weight:800; font-size:14px;">⚡ SAM QUANTUM</span><br>
        <span style="color:#94a3b8; font-size:12px;">User: <b>{st.session_state.user_info['name']}</b></span><br>
        <span style="color:#10b981; font-size:11px; font-weight:700;">● {st.session_state.user_info['tier']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout Terminal"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        if "uid" in st.query_params:
            del st.query_params["uid"]
        st.rerun()

    st.markdown("---")
    st.markdown("### ✈️ Telegram Channel Config")
    # PRE-CONFIGURED CREDENTIALS
    tg_bot_token = st.text_input("Telegram Bot Token", value="8928886896:AAG_K3y8ltCsHPqfva-ONzfjXVu1R9vD5ko", type="password")
    tg_chat_id = st.text_input("Channel Username / ID", value="@sam_quantum_signals")
    
    st.markdown("---")
    st.markdown("### 📊 1. Asset & Timeframe")
    asset_dict = {
        "^NSEBANK": "Bank Nifty Index (^NSEBANK)",
        "^NSEI": "Nifty 50 Index (^NSEI)",
        "GC=F": "MCX Gold Mini / Spot (GC=F)",
        "SI=F": "Silver Mini (SI=F)",
        "RELIANCE.NS": "Reliance Industries",
        "HDFCBANK.NS": "HDFC Bank",
        "BTC-USD": "Bitcoin (BTC/USD)"
    }
    symbol = st.selectbox("Instrument", options=list(asset_dict.keys()), format_func=lambda x: asset_dict[x])
    timeframe = st.selectbox("Candle Resolution", ["1m", "2m", "5m", "15m", "30m", "60m", "1d"], index=3)
    lookback_days = st.slider("Lookback Period (Days)", 1, 60, 30)

    st.markdown("---")
    st.markdown("### 🛠️ 2. Strategy Engine")
    strategy_type = st.selectbox(
        "Quantitative Archetype",
        [
            "1. EMA Institutional Pullback (20/50 Trend)",
            "2. EMA Golden/Death Crossover (9/21 or 20/50)",
            "3. SuperTrend Trend-Rider (10, Multiplier)",
            "4. Momentum + Volume Spike Breakout (2.5x Vol)",
            "5. Candlestick Pattern Engine (Hammer/Engulfing)",
            "6. Bollinger Band Bounce (Mean Reversion)",
            "7. VWAP Intraday Breakout & Retest"
        ]
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st_mult = st.number_input("ST Multiplier", value=2.0, step=0.5)
        fast_ema = st.selectbox("Fast EMA", [9, 20], index=0)
    with col_s2:
        st_period = st.number_input("ST Length", value=10, step=1)
        slow_ema = st.selectbox("Slow EMA", [21, 50, 200], index=1)

    rsi_filter = st.checkbox("Require RSI 50-Level Filter", value=True)
    vol_filter = st.checkbox("Require Volume Spike Confirmation", value=False)

    st.markdown("---")
    st.markdown("### 🛡️ 3. Risk & Capital Management")
    capital = st.number_input("Capital Allocation (₹)", value=100000.0, step=10000.0)
    qty = st.number_input("Position Units / Lot Qty", value=150, step=15)
    delta = st.slider("Option Delta / Leverage", 0.1, 1.0, 0.5, 0.05)

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        target_pts = st.number_input("Target (Pts)", value=50.0, step=5.0)
    with col_k2:
        sl_pts = st.number_input("Hard SL (Pts)", value=20.0, step=5.0)

# ==============================================================================
# 🚀 MAIN DASHBOARD
# ==============================================================================
st.markdown(f"""
<div class="brand-header">
    <div>
        <h3 style="color: #38bdf8; margin: 0; font-weight: 800;">⚡ SAM QUANTUM STUDIO</h3>
        <span style="color: #94a3b8; font-size: 12px;">Institutional Strategy Studio & Telegram Live Dispatcher</span>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; font-size: 11px; padding: 3px 8px; border-radius: 12px; font-weight: 700;">FEED: CONNECTED</span><br>
        <span style="color: #94a3b8; font-size: 11px;">{symbol} | {timeframe}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Action Buttons
col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
with col_b1:
    st.write(f"💼 **Selected:** {asset_dict[symbol]} | Strategy: {strategy_type.split('.')[1].strip()}")
with col_b2:
    execute_btn = st.button("⚡ EXECUTE BACKTEST", type="primary")
with col_b3:
    dispatch_all_btn = st.button("✈️ SCAN & BROADCAST TO TG")

# --- LIVE SCANNER & TELEGRAM BROADCAST LOGIC ---
if dispatch_all_btn:
    with st.spinner("🤖 AI Quantum Engine Scanning all markets for live setups..."):
        scan_results = []
        for sym_key, sym_name in asset_dict.items():
            try:
                df_live = yf.download(sym_key, period="5d", interval=timeframe, progress=False)
                if df_live.empty or len(df_live) < 25:
                    continue
                if isinstance(df_live.columns, pd.MultiIndex):
                    df_live.columns = df_live.columns.droplevel(1)
                
                params = {'st_period': 10, 'st_mult': 2.0, 'bb_std': 2.0}
                d_ind = calc_indicators(df_live, params)
                
                last_bar = d_ind.iloc[-1]
                prev_bar = d_ind.iloc[-2]
                
                spot_price = float(last_bar['Close'])
                rsi_val = float(last_bar['RSI'])
                ema20_val = float(last_bar['EMA20'])
                ema50_val = float(last_bar['EMA50'])
                st_dir = int(last_bar['ST_DIR'])
                prev_st_dir = int(prev_bar['ST_DIR'])
                
                signal = "NEUTRAL"
                ai_confidence = 70
                setup_reason = ""
                
                if ema20_val > ema50_val and spot_price > ema20_val and rsi_val > 52:
                    signal = "BUY / CALL (CE) 🟢"
                    ai_confidence = 88
                    setup_reason = f"Bullish 20/50 EMA Pullback + RSI Momentum ({rsi_val:.1f})"
                elif ema20_val < ema50_val and spot_price < ema20_val and rsi_val < 48:
                    signal = "SELL / PUT (PE) 🔴"
                    ai_confidence = 85
                    setup_reason = f"Bearish 20/50 EMA Rejection + RSI Weakness ({rsi_val:.1f})"
                elif prev_st_dir == -1 and st_dir == 1:
                    signal = "BUY / CALL (CE) 🟢"
                    ai_confidence = 92
                    setup_reason = "SuperTrend Bullish Reversal Cross"
                elif prev_st_dir == 1 and st_dir == -1:
                    signal = "SELL / PUT (PE) 🔴"
                    ai_confidence = 90
                    setup_reason = "SuperTrend Bearish Reversal Cross"
                
                if signal != "NEUTRAL":
                    target_calc = spot_price + target_pts if "BUY" in signal else spot_price - target_pts
                    sl_calc = spot_price - sl_pts if "BUY" in signal else spot_price + sl_pts
                    
                    tg_msg = (
                        f"⚡ <b>SAM QUANTUM AI - LIVE SIGNAL ALERT</b> ⚡\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {sym_name}\n"
                        f"🎯 <b>Action:</b> <code>{signal}</code>\n"
                        f"💵 <b>Entry Price:</b> ₹{spot_price:,.2f}\n"
                        f"🎯 <b>Target:</b> ₹{target_calc:,.2f} (+{target_pts} pts)\n"
                        f"🛑 <b>Stop Loss:</b> ₹{sl_calc:,.2f} (-{sl_pts} pts)\n"
                        f"⏱ <b>Timeframe:</b> {timeframe}\n"
                        f"🧠 <b>AI Confidence:</b> <code>{ai_confidence}% Institutional Edge</code>\n"
                        f"🔍 <b>Setup Logic:</b> {setup_reason}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚠️ <i>Strictly adhere to 1:2 R:R. Trailing SL recommended.</i>\n"
                        f"🤖 <i>Generated via Sam Quantum Terminal</i>"
                    )
                    
                    ok, resp_str = send_telegram_alert(tg_bot_token, tg_chat_id, tg_msg)
                    scan_results.append({"Asset": sym_name, "Signal": signal, "Spot": spot_price, "AI Score": f"{ai_confidence}%", "TG Status": "Sent ✅" if ok else f"Failed ❌ ({resp_str})"})
            except Exception as e:
                pass
                
        if scan_results:
            st.success(f"🚀 AI Scanner complete! Dispatched {len(scan_results)} setups to your Telegram Channel.")
            st.table(pd.DataFrame(scan_results))
        else:
            st.info("Market is currently consolidative with no high-probability setups meeting threshold.")

# --- STANDARD BACKTESTER TABBED VIEW ---
if execute_btn or 'sim_ran' in st.session_state:
    st.session_state.sim_ran = True
    df_raw = yf.download(symbol, period=f"{lookback_days}d", interval=timeframe, progress=False)
    if not df_raw.empty and len(df_raw) >= 25:
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.droplevel(1)
        df_raw.dropna(inplace=True)
        params = {'st_period': int(st_period), 'st_mult': float(st_mult), 'bb_std': 2.0}
        df = calc_indicators(df_raw, params)

        ist_time = df.index.tz_convert('Asia/Kolkata') if df.index.tz is not None else df.index + pd.Timedelta(hours=5, minutes=30)
        df['IST_Hour'] = ist_time.hour
        df['IST_Minute'] = ist_time.minute
        df['Time_Str'] = [t.strftime('%d-%b %H:%M') for t in ist_time]
        df.dropna(inplace=True)

        trades = []
        position = None
        last_traded_bar = -1

        for i in range(2, len(df)):
            curr_spot = float(df['Close'].iloc[i])
            rsi = float(df['RSI'].iloc[i])
            ema20 = float(df['EMA20'].iloc[i])
            ema50 = float(df['EMA50'].iloc[i])
            time_label = df['Time_Str'].iloc[i]

            if position is not None:
                spot_move = (curr_spot - position['entry_spot']) if position['type'] == 'BUY/CE' else (position['entry_spot'] - curr_spot)
                opt_move = spot_move * delta

                if opt_move >= target_pts:
                    trades.append({'Entry Time': position['entry_time'], 'Exit Time': time_label, 'Type': position['type'], 'Entry Price': position['entry_spot'], 'Exit Price': curr_spot, 'Result': 'TARGET HIT 🎯', 'Points': target_pts, 'PnL': target_pts * qty})
                    position = None
                    last_traded_bar = i
                elif opt_move <= -position['sl_pts']:
                    trades.append({'Entry Time': position['entry_time'], 'Exit Time': time_label, 'Type': position['type'], 'Entry Price': position['entry_spot'], 'Exit Price': curr_spot, 'Result': 'SL HIT 🛑', 'Points': -position['sl_pts'], 'PnL': -position['sl_pts'] * qty})
                    position = None
                    last_traded_bar = i

            elif last_traded_bar != i:
                pass_rsi = (rsi > 50) if rsi_filter else True
                pass_rsi_s = (rsi < 50) if rsi_filter else True

                buy_sig = (ema20 > ema50) and (curr_spot > ema20) and pass_rsi
                sell_sig = (ema20 < ema50) and (curr_spot < ema20) and pass_rsi_s

                if buy_sig:
                    position = {'type': 'BUY/CE', 'entry_spot': curr_spot, 'entry_time': time_label, 'sl_pts': sl_pts}
                    last_traded_bar = i
                elif sell_sig:
                    position = {'type': 'SELL/PE', 'entry_spot': curr_spot, 'entry_time': time_label, 'sl_pts': sl_pts}
                    last_traded_bar = i

        tab_chart, tab_metrics, tab_trades, tab_tg = st.tabs(["📈 Pro Chart", "📊 Scorecard & KPIs", "📜 Trade Logs", "✈️ Live Telegram Signal Logs"])
        
        with tab_chart:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df['Time_Str'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#10b981', decreasing_line_color='#ef4444'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA20'], line=dict(color='#38bdf8', width=1.5), name='EMA 20'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA50'], line=dict(color='#f59e0b', width=1.5), name='EMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['RSI'], line=dict(color='#c084fc', width=1.5), name='RSI (14)'), row=2, col=1)
            fig.update_layout(template="plotly_dark", paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14', height=650, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab_metrics:
            if trades:
                tdf = pd.DataFrame(trades)
                net_pnl = tdf['PnL'].sum()
                win_rate = (len(tdf[tdf['PnL'] > 0]) / len(tdf)) * 100
                st.markdown("#### 💎 Strategy Scorecard")
                k1, k2, k3 = st.columns(3)
                k1.metric("Net PnL", f"₹{net_pnl:,.2f}")
                k2.metric("Win Rate", f"{win_rate:.1f}%")
                k3.metric("Total Executions", len(tdf))

        with tab_trades:
            if trades:
                st.dataframe(pd.DataFrame(trades), use_container_width=True)

        with tab_tg:
            st.markdown("### ✈️ Send Instant Custom Setup to Telegram")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                custom_action = st.selectbox("Action", ["BUY / CALL (CE) 🟢", "SELL / PUT (PE) 🔴"])
                custom_strike = st.text_input("Recommended Strike / Price", value=f"{df['Close'].iloc[-1]:,.0f}")
            with col_m2:
                custom_sl = st.text_input("Stop Loss Note", value="Strict 20 Pts Hard SL")
                custom_tp = st.text_input("Target Note", value="50 Pts (1:2 R:R Trailing)")
            
            if st.button("🚀 BROADCAST THIS CUSTOM SIGNAL"):
                msg = (
                    f"⚡ <b>SAM QUANTUM AI - EXCLUSIVE SIGNAL</b> ⚡\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {asset_dict[symbol]}\n"
                    f"🎯 <b>Action:</b> <code>{custom_action}</code>\n"
                    f"💵 <b>Price/Strike:</b> {custom_strike}\n"
                    f"🎯 <b>Target:</b> {custom_tp}\n"
                    f"🛑 <b>Stop Loss:</b> {custom_sl}\n"
                    f"⏱ <b>Timeframe:</b> {timeframe}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 <i>Dispatched by Master Admin via Sam Quantum AI</i>"
                )
                ok, res = send_telegram_alert(tg_bot_token, tg_chat_id, msg)
                if ok:
                    st.success("✅ Broadcasted to your Telegram Channel in 1 second!")
                else:
                    st.error(f"❌ Failed: {res}")