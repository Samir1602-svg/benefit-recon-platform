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
import time
import requests

# ==============================================================================
# 💎 SAM QUANTUM TERMINAL - HIGH-RES PRO TYPOGRAPHY & TOUCH CONFIG
# ==============================================================================
st.set_page_config(
    page_title="SAM QUANTUM AI | Institutional Trading Terminal",
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

# 🛡️ High-Resolution Mobile Dark UI & Anti-Swipe Reload Lock
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebarContent"] {
        overscroll-behavior-y: none !important;
        overscroll-behavior-x: none !important;
        -webkit-overflow-scrolling: touch;
        background-color: #080b11 !important;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
    .glass-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    }

    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        letter-spacing: 0.5px;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #0f172a;
        border-radius: 12px;
        padding: 5px;
        border: 1px solid #1e293b;
        gap: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border-radius: 8px;
        font-weight: 700;
    }

    .js-plotly-plot .plotly .modebar {
        orientation: h;
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 8px;
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
            <div style="font-size: 36px; margin-bottom: 6px;">⚡</div>
            <h2 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: -0.5px;">SAM QUANTUM AI</h2>
            <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 16px 0;">Institutional Strategy Terminal & Autonomous Pilot</p>
            <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                ● FREE LIFETIME TRADER ACCESS
            </span>
            <hr style="border-color: #1e293b; margin-top: 18px;">
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
# ⏰ STRICT MARKET GATEKEEPER
# ==============================================================================
def is_market_open(symbol_key):
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    weekday = now_ist.weekday()
    current_time = now_ist.time()

    if symbol_key == "BTC-USD":
        return True, "Crypto (24/7 Live)"

    if weekday in [5, 6]:
        return False, "Market Closed (Weekend)"

    if symbol_key in ["^NSEBANK", "^NSEI", "RELIANCE.NS", "HDFCBANK.NS"]:
        market_start = dtime(9, 15)
        market_end = dtime(15, 30)
        if market_start <= current_time <= market_end:
            return True, "NSE Live (09:15 - 15:30 IST)"
        return False, "NSE Closed (Opens 09:15 AM Mon-Fri)"

    if symbol_key in ["GC=F", "SI=F"]:
        mcx_start = dtime(9, 0)
        mcx_end = dtime(23, 30)
        if mcx_start <= current_time <= mcx_end:
            return True, "MCX Live (09:00 - 23:30 IST)"
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
# 🎛️ SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
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
    lookback_days = st.slider("Lookback (Days)", 1, 60, 30)

# ==============================================================================
# 🚀 MAIN DASHBOARD
# ==============================================================================
st.markdown(f"""
<div class="brand-header">
    <div>
        <h3 style="color: #38bdf8; margin: 0; font-weight: 800;">⚡ SAM QUANTUM TERMINAL</h3>
        <span style="color: #94a3b8; font-size: 12px;">Institutional Quant Studio & Real-Time Touch Engine</span>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; font-size: 11px; padding: 3px 10px; border-radius: 12px; font-weight: 700;">PRO ENGINE LIVE</span><br>
        <span style="color: #94a3b8; font-size: 11px;">{symbol} | {timeframe}</span>
    </div>
</div>
""", unsafe_allow_html=True)

is_admin = st.session_state.user_info.get("tier") == "Master Admin" or st.session_state.user_info.get("id") == "admin"

tab_chart, tab_metrics, tab_trades, tab_reports, tab_auto_pilot = st.tabs([
    "📈 Pro Touch Chart", 
    "📊 KPIs & Curve", 
    "📜 Trade Logs", 
    "📥 Download Reports", 
    "👑 1-Click AI Auto-Pilot"
])

# --- ADMIN AUTONOMOUS SCANNER TAB ---
with tab_auto_pilot:
    if not is_admin:
        st.warning("🔒 Access Restricted to Master Admin / Founder.")
    else:
        st.markdown("### 🤖 Autonomous Live Multi-Market Pilot")
        st.caption("Validates market hours before dispatching real-time signals to Telegram.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            auto_scan_active = st.toggle("⚡ ACTIVATE AUTO PILOT LOOP", value=False)
            target_pts = st.number_input("Index Target Pts", value=50.0, step=5.0)
        with col_p2:
            min_confidence = st.slider("Minimum AI Confidence Threshold", 75, 95, 85)
            sl_pts = st.number_input("Index Hard SL Pts", value=20.0, step=5.0)

        st.markdown("#### 🌐 Real-Time Market Gates")
        status_data = []
        for s_sym, s_name in asset_dict.items():
            is_open, reason = is_market_open(s_sym)
            status_data.append({
                "Instrument": s_name,
                "Status": "🟢 LIVE OPEN" if is_open else "🔴 CLOSED",
                "Gatekeeper Info": reason
            })
        st.table(pd.DataFrame(status_data))

        if auto_scan_active or st.button("🚀 SCAN CURRENTLY OPEN MARKETS"):
            with st.spinner("🔍 Auditing open markets for real-time confluences..."):
                dispatched_count = 0
                for s_sym, s_name in asset_dict.items():
                    is_open, gate_reason = is_market_open(s_sym)
                    if not is_open:
                        continue

                    try:
                        df_live = yf.download(s_sym, period="3d", interval="5m", progress=False)
                        if df_live.empty or len(df_live) < 20:
                            continue
                        if isinstance(df_live.columns, pd.MultiIndex):
                            df_live.columns = df_live.columns.droplevel(1)

                        df_live = calc_indicators(df_live, {})
                        curr_bar = df_live.iloc[-1]
                        prev_bar = df_live.iloc[-2]

                        spot = float(curr_bar['Close'])
                        rsi = float(curr_bar['RSI'])
                        ema20 = float(curr_bar['EMA20'])
                        ema50 = float(curr_bar['EMA50'])
                        st_now = int(curr_bar['ST_DIR'])
                        st_prev = int(prev_bar['ST_DIR'])

                        sig = "NEUTRAL"
                        conf = 70
                        logic = ""

                        if ema20 > ema50 and spot > ema20 and rsi > 54:
                            sig = "BUY / CALL (CE) 🟢"
                            conf = 88
                            logic = f"EMA 20/50 Trend + RSI Momentum ({rsi:.1f})"
                        elif ema20 < ema50 and spot < ema20 and rsi < 46:
                            sig = "SELL / PUT (PE) 🔴"
                            conf = 88
                            logic = f"EMA 20/50 Bearish Structure + RSI Drop ({rsi:.1f})"
                        elif st_prev == -1 and st_now == 1:
                            sig = "BUY / CALL (CE) 🟢"
                            conf = 92
                            logic = "SuperTrend 10,2 Bullish Reversal"
                        elif st_prev == 1 and st_now == -1:
                            sig = "SELL / PUT (PE) 🔴"
                            conf = 92
                            logic = "SuperTrend 10,2 Bearish Reversal"

                        if sig != "NEUTRAL" and conf >= min_confidence:
                            tp = spot + target_pts if "BUY" in sig else spot - target_pts
                            sl = spot - sl_pts if "BUY" in sig else spot + sl_pts
                            ist_now_str = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
                            tg_text = (
                                f"⚡ <b>SAM QUANTUM AI - LIVE SIGNAL ALERT</b> ⚡\n"
                                f"━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 <b>Asset:</b> {s_name}\n"
                                f"🎯 <b>Action:</b> <code>{sig}</code>\n"
                                f"💵 <b>Current Live Spot:</b> ₹{spot:,.2f}\n"
                                f"🎯 <b>Target:</b> ₹{tp:,.2f} (+{target_pts} pts)\n"
                                f"🛑 <b>Stop Loss:</b> ₹{sl:,.2f} (-{sl_pts} pts)\n"
                                f"⏱ <b>Trigger Time:</b> {ist_now_str}\n"
                                f"🧠 <b>AI Confidence:</b> <code>{conf}% Institutional Edge</code>\n"
                                f"🔍 <b>Logic:</b> {logic}\n"
                                f"━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🤖 <i>Dispatched via Autonomous Quantum Pilot</i>"
                            )
                            send_telegram_alert(tg_text)
                            dispatched_count += 1
                    except Exception:
                        pass

                if dispatched_count > 0:
                    st.success(f"✅ Dispatched {dispatched_count} live signals to @sam_quantum_signals.")
                else:
                    st.info("Scanner complete. Currently active markets have no setups meeting strict AI confidence threshold.")

# --- PRO BACKTESTER ENGINE ---
df_raw = yf.download(symbol, period=f"{lookback_days}d", interval=timeframe, progress=False)

if df_raw.empty or len(df_raw) < 25:
    st.error("Insufficient market data. Try adjusting lookback or resolution.")
    st.stop()

if isinstance(df_raw.columns, pd.MultiIndex):
    df_raw.columns = df_raw.columns.droplevel(1)
df_raw.dropna(inplace=True)
df = calc_indicators(df_raw, {})
ist_time = df.index.tz_convert('Asia/Kolkata') if df.index.tz is not None else df.index + pd.Timedelta(hours=5, minutes=30)
df['Time_Str'] = [t.strftime('%d-%b %H:%M') for t in ist_time]

# Simulate trades
trades = []
position = None
last_bar = -1
target_pts_sim = 50.0
sl_pts_sim = 20.0
qty_sim = 150

for i in range(2, len(df)):
    curr_spot = float(df['Close'].iloc[i])
    rsi = float(df['RSI'].iloc[i])
    ema20 = float(df['EMA20'].iloc[i])
    ema50 = float(df['EMA50'].iloc[i])
    time_lbl = df['Time_Str'].iloc[i]

    if position is not None:
        move = (curr_spot - position['entry']) if position['type'] == 'BUY/CE' else (position['entry'] - curr_spot)
        opt_move = move * 0.5

        if opt_move >= target_pts_sim:
            trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'TARGET HIT 🎯', 'Points': target_pts_sim, 'PnL': target_pts_sim * qty_sim})
            position = None
            last_bar = i
        elif opt_move <= -sl_pts_sim:
            trades.append({'Entry Time': position['time'], 'Exit Time': time_lbl, 'Type': position['type'], 'Entry Price': position['entry'], 'Exit Price': curr_spot, 'Result': 'SL HIT 🛑', 'Points': -sl_pts_sim, 'PnL': -sl_pts_sim * qty_sim})
            position = None
            last_bar = i
    elif last_bar != i:
        if ema20 > ema50 and curr_spot > ema20 and rsi > 50:
            position = {'type': 'BUY/CE', 'entry': curr_spot, 'time': time_lbl}
            last_bar = i
        elif ema20 < ema50 and curr_spot < ema20 and rsi < 50:
            position = {'type': 'SELL/PE', 'entry': curr_spot, 'time': time_lbl}
            last_bar = i

# --- 1. PRO TOUCH CHART TAB ---
with tab_chart:
    st.markdown("#### 🕯️ Institutional Price Action (Mobile Touch & Pinch-to-Zoom Enabled)")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.04)

    fig.add_trace(go.Candlestick(
        x=df['Time_Str'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#10b981', decreasing_line_color='#ef4444',
        name="Candles"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA20'], line=dict(color='#38bdf8', width=1.5), name='EMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['EMA50'], line=dict(color='#f59e0b', width=1.5), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time_Str'], y=df['RSI'], line=dict(color='#c084fc', width=1.5), name='RSI 14'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.4)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(16, 185, 129, 0.4)", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#080b11',
        plot_bgcolor='#080b11',
        height=580,
        xaxis_rangeslider_visible=False,
        dragmode='pan',
        margin=dict(l=5, r=5, t=10, b=5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 📱 Mobile Touch Controls & HD PNG Download Button inside Toolbar
    config_mobile = {
        'scrollZoom': True,
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'sam_quantum_{symbol}_{datetime.now().strftime("%Y%m%d")}',
            'height': 1080,
            'width': 1920,
            'scale': 2
        }
    }
    st.plotly_chart(fig, use_container_width=True, config=config_mobile)

# --- 2. KPIS & EQUITY CURVE TAB ---
with tab_metrics:
    if trades:
        tdf = pd.DataFrame(trades)
        net_pnl = tdf['PnL'].sum()
        win_count = len(tdf[tdf['PnL'] > 0])
        win_rate = (win_count / len(tdf)) * 100
        tdf['Cum_PnL'] = tdf['PnL'].cumsum()

        st.markdown("#### 💎 Strategy Scorecard")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Net PnL", f"{'+₹' if net_pnl >= 0 else '-₹'}{abs(net_pnl):,.2f}")
        k2.metric("Win Rate", f"{win_rate:.1f}%", f"{win_count}W / {len(tdf)-win_count}L")
        k3.metric("Total Trades", len(tdf))
        k4.metric("Avg R:R", "1 : 2.5")

        st.markdown("---")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=tdf['Exit Time'], y=tdf['Cum_PnL'],
            mode='lines+markers', line=dict(color='#10b981', width=2.5),
            fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.08)',
            name='Equity Growth'
        ))
        fig_equity.update_layout(template="plotly_dark", paper_bgcolor='#0f172a', plot_bgcolor='#0f172a', height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_equity, use_container_width=True, config=config_mobile)

# --- 3. TRADE LOGS TAB ---
with tab_trades:
    if trades:
        st.markdown("#### 📜 Institutional Trade Execution Audit Logs")
        st.dataframe(pd.DataFrame(trades), use_container_width=True, height=450)

# --- 4. DOWNLOAD REPORTS (PNG / CSV / HTML AUDIT) ---
with tab_reports:
    st.markdown("### 📥 Instant Mobile Audit & Report Export")
    st.write("Generate high-res trading audits to share on WhatsApp or save on your mobile device.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("##### 📄 1. Full Strategy Audit Sheet (CSV)")
        if trades:
            csv_buf = io.StringIO()
            pd.DataFrame(trades).to_csv(csv_buf, index=False)
            st.download_button(
                label="📥 DOWNLOAD CSV AUDIT",
                data=csv_buf.getvalue(),
                file_name=f"sam_quantum_audit_{symbol}.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades to export.")

    with col_r2:
        st.markdown("##### 📑 2. Formatted HTML Executive Summary")
        if trades:
            html_report = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #080b11; color: #f1f5f9; padding: 25px; }}
                    .card {{ background: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 12px; }}
                    h1 {{ color: #38bdf8; margin: 0; }}
                    .tag {{ background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 4px 10px; border-radius: 6px; font-weight: bold; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #1e293b; padding: 10px; text-align: left; }}
                    th {{ background-color: #1e293b; color: #38bdf8; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>⚡ SAM QUANTUM AI - AUDIT REPORT</h1>
                    <p>Asset: <b>{symbol}</b> | Resolution: <b>{timeframe}</b> | Generated On: <b>{datetime.now().strftime('%d-%b-%Y %H:%M')}</b></p>
                    <span class="tag">NET PnL: ₹{net_pnl:,.2f}</span> | <span class="tag">WIN RATE: {win_rate:.1f}%</span>
                    <hr style="border-color: #1e293b; margin: 20px 0;">
                    <h3>Trade Log Records</h3>
                    {pd.DataFrame(trades).to_html(classes='table', index=False)}
                </div>
            </body>
            </html>
            """
            st.download_button(
                label="📥 DOWNLOAD HTML SUMMARY",
                data=html_report,
                file_name=f"sam_quantum_report_{symbol}.html",
                mime="text/html"
            )