import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
import time

# ==============================================================================
# 💎 SAM QUANTUM TERMINAL - UI THEME & AUTHENTICATION CONFIG
# ==============================================================================
st.set_page_config(
    page_title="SAM QUANTUM AI | Institutional Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authorized Access Registry (Admin can add/remove clients)
AUTHORIZED_USERS = {
    "admin": {"pass": "sam@2026", "name": "Sam (Founder / Master)", "tier": "Master Admin"},
    "vip_trader": {"pass": "quant100x", "name": "VIP Algo Trader", "tier": "Institutional Pro"},
    "guest": {"pass": "welcome123", "name": "Trial Client", "tier": "Standard Beta"}
}

# Custom CSS for Sleek Institutional Dark / Glassmorphism Interface
st.markdown("""
<style>
    /* Dark Terminal Theme */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Sleek Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Login & Glass Containers */
    .glass-card {
        background: rgba(22, 27, 34, 0.85);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        backdrop-filter: blur(10px);
    }
    
    /* Top Banner */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #161b22 0%, #1f2937 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 24px;
        margin-bottom: 20px;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    
    /* Neon Action Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        font-weight: 600;
        border: 1px solid #3fb950;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
        box-shadow: 0 0 16px rgba(46, 160, 67, 0.5);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 6px;
        border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d !important;
        color: #58a6ff !important;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔐 AUTHENTICATION GATEWAY
# ==============================================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

def login_portal():
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <h1 style="color: #58a6ff; margin-bottom: 2px;">⚡ SAM QUANTUM AI</h1>
            <p style="color: #8b949e; font-size: 14px; margin-bottom: 24px;">Institutional Strategy Studio & Execution Engine</p>
            <hr style="border-color: #30363d;">
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("#### 🔒 Terminal Access Verification")
            username = st.text_input("User ID / Access Identity", placeholder="Enter assigned username")
            password = st.text_input("Security Access Key", type="password", placeholder="Enter your secret token")
            submit = st.form_submit_button("⚡ UNLOCK TERMINAL")
            
            if submit:
                if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username]["pass"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user_info = AUTHORIZED_USERS[username]
                    st.success(f"Access Granted! Welcome, {AUTHORIZED_USERS[username]['name']}.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("⛔ Unauthorized Access Key. Contact Sam to obtain an institutional license.")

if not st.session_state.authenticated:
    login_portal()
    st.stop()

# ==============================================================================
# 🧮 PRODUCTION QUANT INDICATORS ENGINE
# ==============================================================================
def calc_indicators(df, params):
    d = df.copy()
    c, h, l, o, v = d['Close'], d['High'], d['Low'], d['Open'], d['Volume']

    # Moving Averages
    d['EMA9'] = c.ewm(span=9, adjust=False).mean()
    d['EMA20'] = c.ewm(span=20, adjust=False).mean()
    d['EMA21'] = c.ewm(span=21, adjust=False).mean()
    d['EMA50'] = c.ewm(span=50, adjust=False).mean()
    d['EMA100'] = c.ewm(span=100, adjust=False).mean()
    d['EMA200'] = c.ewm(span=200, adjust=False).mean()
    d['SMA20'] = c.rolling(window=20).mean()

    # Intraday VWAP
    typical_price = (h + l + c) / 3.0
    date_group = d.index.date if hasattr(d.index, 'date') else np.zeros(len(d))
    pv = typical_price * v
    d['Cum_PV'] = pv.groupby(date_group).cumsum()
    d['Cum_Vol'] = v.groupby(date_group).cumsum()
    d['VWAP'] = d['Cum_PV'] / d['Cum_Vol'].replace(0, np.nan)
    d['VWAP'] = d['VWAP'].fillna(c)

    # RSI (14)
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    d['RSI'] = 100 - (100 / (1 + rs))
    d['RSI'] = d['RSI'].fillna(50)

    # Bollinger Bands
    d['BB_MID'] = d['SMA20']
    bb_std = c.rolling(window=20).std()
    d['BB_UP'] = d['BB_MID'] + (params.get('bb_std', 2.0) * bb_std)
    d['BB_LOW'] = d['BB_MID'] - (params.get('bb_std', 2.0) * bb_std)

    # ATR
    hl = h - l
    hc = (h - c.shift(1)).abs()
    lc = (l - c.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    d['ATR'] = tr.rolling(window=14).mean().fillna(tr)

    # SuperTrend
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
    
    return d

# ==============================================================================
# 🎛️ SIDEBAR: QUANT CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="background:#21262d; border:1px solid #30363d; border-radius:8px; padding:10px 14px; margin-bottom:12px;">
        <span style="color:#58a6ff; font-weight:700;">⚡ SAM QUANTUM</span><br>
        <span style="color:#8b949e; font-size:12px;">User: {st.session_state.user_info['name']}</span><br>
        <span style="color:#3fb950; font-size:11px; font-weight:600;">● {st.session_state.user_info['tier']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout Session"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 1. Market Asset & Horizon")
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
    lookback_days = st.slider("Lookback Window (Days)", 1, 60, 30)

    st.markdown("---")
    st.markdown("### 🛠️ 2. Strategy Engine")
    strategy_type = st.selectbox(
        "Quantitative Archetype",
        [
            "1. EMA Institutional Pullback (20/50 Trend)",
            "2. EMA Golden/Death Crossover (9/21 or 20/50)",
            "3. SuperTrend Trend-Rider (10, Multiplier)",
            "4. Momentum + Volume Spike Breakout (2.5x Vol)",
            "5. Bollinger Band Bounce (Mean Reversion)",
            "6. VWAP Intraday Breakout & Retest",
            "7. Master Multi-Indicator Confluence"
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
    st.markdown("### 🛡️ 3. Risk & Trailing Architecture")
    capital = st.number_input("Capital Allocation (₹)", value=100000.0, step=10000.0)
    qty = st.number_input("Position Units / Qty", value=150, step=15)
    delta = st.slider("Option Delta / Leverage", 0.1, 1.0, 0.5, 0.05)

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        target_pts = st.number_input("Target (Pts)", value=50.0, step=5.0)
    with col_k2:
        sl_pts = st.number_input("Hard SL (Pts)", value=20.0, step=5.0)

    trailing_mode = st.selectbox(
        "Dynamic Trailing Stop",
        [
            "Breakeven Lock (+pts shift SL to Cost)",
            "Dynamic ATR Ratchet Trail",
            "9-EMA Trend-Rider (Exit on Candle Close)",
            "None (Fixed Target & SL)"
        ],
        index=0
    )
    be_trigger = st.number_input("Breakeven Trigger (+pts gain)", value=25.0, step=5.0) if "Breakeven" in trailing_mode else 0.0

    session_filter = st.selectbox(
        "Institutional Timing Filter",
        [
            "All Market Hours (24/7 or Standard Open)",
            "Indian Cash/Options (09:15 - 15:15 IST)",
            "London + NY Session (13:30 - 22:30 IST)",
            "Prime Breakout Windows Only"
        ],
        index=0
    )

# ==============================================================================
# 🚀 MAIN DASHBOARD
# ==============================================================================
st.markdown(f"""
<div class="brand-header">
    <div>
        <h2 style="color: #58a6ff; margin: 0;">⚡ SAM QUANTUM STUDIO</h2>
        <span style="color: #8b949e; font-size: 13px;">Enterprise Strategy Validation & Multi-Asset Quantitative Terminal</span>
    </div>
    <div style="text-align: right;">
        <span style="background: #238636; color: #fff; font-size: 11px; padding: 4px 10px; border-radius: 20px; font-weight: 700;">LIVE FEED: CONNECTED</span><br>
        <span style="color: #8b949e; font-size: 12px;">Target: {symbol} | {timeframe}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_run1, col_run2 = st.columns([3, 1])
with col_run1:
    st.write(f"💼 **Strategy:** {strategy_type.split('.')[1].strip()} | 🎯 **R:R Profile:** Risk ₹{sl_pts*qty:,.0f} to Gain ₹{target_pts*qty:,.0f}")
with col_run2:
    execute_btn = st.button("⚡ EXECUTE BACKTEST", type="primary")

if execute_btn or 'sim_ran' in st.session_state:
    st.session_state.sim_ran = True
    with st.spinner("⏳ Compiling multi-timeframe candle stream and executing institutional matrix..."):
        df_raw = yf.download(symbol, period=f"{lookback_days}d", interval=timeframe, progress=False)
        
        if df_raw.empty or len(df_raw) < 25:
            st.error("❌ Insufficient tick history. Please adjust lookback days or candle timeframe.")
            st.stop()

        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.droplevel(1)
        df_raw.dropna(inplace=True)

        params = {'st_period': int(st_period), 'st_mult': float(st_mult), 'bb_std': 2.0}
        df = calc_indicators(df_raw, params)

        ist_time = df.index.tz_convert('Asia/Kolkata') if df.index.tz is not None else df.index + pd.Timedelta(hours=5, minutes=30)
        df['IST_Hour'] = ist_time.hour
        df['IST_Minute'] = ist_time.minute
        df.dropna(inplace=True)

        # Simulation Loop
        trades = []
        position = None
        last_traded_bar = -1

        for i in range(2, len(df)):
            curr_spot = float(df['Close'].iloc[i])
            curr_open = float(df['Open'].iloc[i])
            low_spot = float(df['Low'].iloc[i])
            high_spot = float(df['High'].iloc[i])
            vol = float(df['Volume'].iloc[i])
            vol_sma = float(df['VOL_SMA20'].iloc[i])
            pct = float(df['PCT_CHANGE'].iloc[i])
            rsi = float(df['RSI'].iloc[i])
            atr = float(df['ATR'].iloc[i])
            
            ema9 = float(df['EMA9'].iloc[i])
            ema20 = float(df['EMA20'].iloc[i])
            ema50 = float(df['EMA50'].iloc[i])
            fast_val = float(df[f'EMA{fast_ema}'].iloc[i])
            prev_fast_val = float(df[f'EMA{fast_ema}'].iloc[i-1])
            slow_val = float(df[f'EMA{slow_ema}'].iloc[i])
            prev_slow_val = float(df[f'EMA{slow_ema}'].iloc[i-1])

            st_dir = int(df['ST_DIR'].iloc[i])
            prev_st_dir = int(df['ST_DIR'].iloc[i-1])
            bb_u = float(df['BB_UP'].iloc[i])
            bb_l = float(df['BB_LOW'].iloc[i])
            vwap = float(df['VWAP'].iloc[i])

            hr = int(df['IST_Hour'].iloc[i])
            mn = int(df['IST_Minute'].iloc[i])
            candle_time = df.index[i]

            # Timing Filters
            in_session = True
            if session_filter == "Indian Cash/Options (09:15 - 15:15 IST)":
                in_session = (hr == 9 and mn >= 15) or (10 <= hr < 15) or (hr == 15 and mn <= 15)
            elif session_filter == "London + NY Session (13:30 - 22:30 IST)":
                in_session = (hr == 13 and mn >= 30) or (14 <= hr < 22) or (hr == 22 and mn <= 30)

            # 1. Manage Active Position
            if position is not None:
                spot_move = (curr_spot - position['entry_spot']) if position['type'] == 'BUY/CE' else (position['entry_spot'] - curr_spot)
                opt_move = spot_move * delta

                # Breakeven Trail
                if "Breakeven" in trailing_mode and opt_move >= be_trigger and not position['trailed']:
                    position['sl_pts'] = 0.0
                    position['trailed'] = True

                # Dynamic ATR Ratchet
                if "ATR" in trailing_mode:
                    if opt_move > position['max_gain']:
                        position['max_gain'] = opt_move
                        ratchet = -(position['max_gain'] - (atr * 1.5 * delta))
                        if ratchet < position['sl_pts']:
                            position['sl_pts'] = ratchet

                # 9-EMA Dynamic Trend-Rider Exit
                if "9-EMA" in trailing_mode:
                    ema_break = (position['type'] == 'BUY/CE' and curr_spot < ema9) or (position['type'] == 'SELL/PE' and curr_spot > ema9)
                    if ema_break and opt_move > 5.0:
                        pnl = opt_move * qty
                        trades.append({
                            'Entry Time': position['entry_time'], 'Exit Time': candle_time,
                            'Type': position['type'], 'Entry Price': position['entry_spot'], 'Exit Price': curr_spot,
                            'Result': 'EMA TRAIL EXIT 🏃', 'Points': round(opt_move, 1), 'PnL': pnl,
                            'Entry_Idx': position['entry_idx']
                        })
                        position = None
                        last_traded_bar = i
                        continue

                # Target Hit
                if opt_move >= target_pts:
                    pnl = target_pts * qty
                    trades.append({
                        'Entry Time': position['entry_time'], 'Exit Time': candle_time,
                        'Type': position['type'], 'Entry Price': position['entry_spot'], 'Exit Price': curr_spot,
                        'Result': 'TARGET HIT 🎯', 'Points': target_pts, 'PnL': pnl,
                        'Entry_Idx': position['entry_idx']
                    })
                    position = None
                    last_traded_bar = i

                # Stop-Loss Hit
                elif opt_move <= -position['sl_pts']:
                    pnl = -position['sl_pts'] * qty
                    res_tag = "BREAKEVEN 🛡️" if position['trailed'] else "SL HIT 🛑"
                    trades.append({
                        'Entry Time': position['entry_time'], 'Exit Time': candle_time,
                        'Type': position['type'], 'Entry Price': position['entry_spot'], 'Exit Price': curr_spot,
                        'Result': res_tag, 'Points': -position['sl_pts'], 'PnL': pnl,
                        'Entry_Idx': position['entry_idx']
                    })
                    position = None
                    last_traded_bar = i

            # 2. Trigger Next Valid Setup
            elif in_session and last_traded_bar != i:
                pass_rsi_buy = (rsi > 50) if rsi_filter else True
                pass_rsi_sell = (rsi < 50) if rsi_filter else True
                pass_vol = (vol >= vol_sma * 1.5) if vol_filter else True

                buy_sig = False
                sell_sig = False

                if "1. EMA Institutional Pullback" in strategy_type:
                    buy_sig = (ema20 > ema50) and (low_spot <= ema20 * 1.002) and (curr_spot > ema20) and pass_rsi_buy and pass_vol
                    sell_sig = (ema20 < ema50) and (high_spot >= ema20 * 0.998) and (curr_spot < ema20) and pass_rsi_sell and pass_vol

                elif "2. EMA Golden/Death Crossover" in strategy_type:
                    buy_sig = (prev_fast_val <= prev_slow_val and fast_val > slow_val) and pass_rsi_buy and pass_vol
                    sell_sig = (prev_fast_val >= prev_slow_val and fast_val < slow_val) and pass_rsi_sell and pass_vol

                elif "3. SuperTrend Trend-Rider" in strategy_type:
                    buy_sig = (prev_st_dir == -1 and st_dir == 1) and pass_rsi_buy and pass_vol
                    sell_sig = (prev_st_dir == 1 and st_dir == -1) and pass_rsi_sell and pass_vol

                elif "4. Momentum + Volume Spike" in strategy_type:
                    buy_sig = (vol >= vol_sma * 2.5) and (pct >= 0.30) and (curr_spot > ema9) and pass_rsi_buy
                    sell_sig = (vol >= vol_sma * 2.5) and (pct <= -0.30) and (curr_spot < ema9) and pass_rsi_sell

                elif "5. Bollinger Band Bounce" in strategy_type:
                    buy_sig = (low_spot <= bb_l) and (rsi < 35) and (curr_spot > bb_l)
                    sell_sig = (high_spot >= bb_u) and (rsi > 65) and (curr_spot < bb_u)

                elif "6. VWAP Intraday Breakout" in strategy_type:
                    buy_sig = (curr_spot > vwap) and (curr_open <= vwap) and (curr_spot > ema20) and pass_rsi_buy and pass_vol
                    sell_sig = (curr_spot < vwap) and (curr_open >= vwap) and (curr_spot < ema20) and pass_rsi_sell and pass_vol

                elif "7. Master Multi-Indicator Confluence" in strategy_type:
                    buy_sig = (st_dir == 1) and (curr_spot > ema50) and (curr_spot > vwap) and (rsi > 54) and pass_vol
                    sell_sig = (st_dir == -1) and (curr_spot < ema50) and (curr_spot < vwap) and (rsi < 46) and pass_vol

                if buy_sig:
                    position = {'type': 'BUY/CE', 'entry_spot': curr_spot, 'entry_time': candle_time, 'sl_pts': sl_pts, 'trailed': False, 'max_gain': 0.0, 'entry_idx': i}
                    last_traded_bar = i
                elif sell_sig:
                    position = {'type': 'SELL/PE', 'entry_spot': curr_spot, 'entry_time': candle_time, 'sl_pts': sl_pts, 'trailed': False, 'max_gain': 0.0, 'entry_idx': i}
                    last_traded_bar = i

        # ==============================================================================
        # 📊 INSTITUTIONAL VISUAL WORKSPACE
        # ==============================================================================
        tab_chart, tab_metrics, tab_trades, tab_admin = st.tabs([
            "📈 Candlestick Pro Chart", 
            "📊 Executive KPIs & Scorecard", 
            "📜 Execution Logs", 
            "👥 Client Access Manager"
        ])

        with tab_chart:
            st.markdown("#### 🕯️ Multi-Pane Institutional Price Chart with Execution Overlays")
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                subplot_titles=(f"{symbol} ({timeframe}) Price & Indicators", "Volume & Activity", "RSI Momentum (14)"),
                row_heights=[0.65, 0.15, 0.20]
            )

            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name="Candles", increasing_line_color='#238636', decreasing_line_color='#da3633',
                increasing_fillcolor='#238636', decreasing_fillcolor='#da3633'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='#58a6ff', width=1.5), name='EMA 20'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='#f0883e', width=1.5), name='EMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], line=dict(color='#d2a8ff', width=1.5, dash='dot'), name='VWAP'), row=1, col=1)

            if trades:
                tdf = pd.DataFrame(trades)
                b_df = tdf[tdf['Type'] == 'BUY/CE']
                if not b_df.empty:
                    fig.add_trace(go.Scatter(
                        x=b_df['Entry Time'], y=b_df['Entry Price'],
                        mode='markers', marker=dict(symbol='triangle-up', size=12, color='#3fb950'),
                        name='BUY / CE Entry'
                    ), row=1, col=1)

                s_df = tdf[tdf['Type'] == 'SELL/PE']
                if not s_df.empty:
                    fig.add_trace(go.Scatter(
                        x=s_df['Entry Time'], y=s_df['Entry Price'],
                        mode='markers', marker=dict(symbol='triangle-down', size=12, color='#f85149'),
                        name='SELL / PE Entry'
                    ), row=1, col=1)

            colors_v = ['#238636' if df['Close'].iloc[k] >= df['Open'].iloc[k] else '#da3633' for k in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_v, name='Volume'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['VOL_SMA20'], line=dict(color='#e3b341', width=1.2), name='Vol SMA 20'), row=2, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#a371f7', width=1.5), name='RSI (14)'), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(248, 81, 73, 0.4)", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(63, 185, 80, 0.4)", row=3, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(139, 148, 158, 0.4)", row=3, col=1)

            fig.update_layout(
                template="plotly_dark", paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
                height=720, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_metrics:
            if not trades:
                st.warning("⚠️ No trades were triggered with current parameter constraints.")
            else:
                tdf = pd.DataFrame(trades)
                net_pnl = tdf['PnL'].sum()
                total_trades = len(tdf)
                win_df = tdf[tdf['PnL'] > 0]
                loss_df = tdf[tdf['PnL'] < 0]
                win_count = len(win_df)
                loss_count = len(loss_df)
                win_rate = (win_count / total_trades) * 100
                roi = (net_pnl / capital) * 100

                total_gain = win_df['PnL'].sum()
                total_loss = abs(loss_df['PnL'].sum())
                profit_factor = round(total_gain / total_loss, 2) if total_loss > 0 else 99.9

                tdf['Cum_PnL'] = tdf['PnL'].cumsum()
                tdf['Peak'] = tdf['Cum_PnL'].cummax()
                tdf['Drawdown'] = tdf['Cum_PnL'] - tdf['Peak']
                max_dd = tdf['Drawdown'].min()
                max_dd_pct = (abs(max_dd) / capital) * 100

                avg_win = win_df['PnL'].mean() if not win_df.empty else 0.0
                avg_loss = abs(loss_df['PnL'].mean()) if not loss_df.empty else 0.0
                expectancy = ((win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss))

                st.markdown("#### 💎 Strategy Scorecard & Edge KPIs")
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("Net PnL", f"{'+₹' if net_pnl >= 0 else '-₹'}{abs(net_pnl):,.2f}", f"{roi:.1f}% ROI")
                k2.metric("Win Rate", f"{win_rate:.1f}%", f"{win_count}W / {loss_count}L")
                k3.metric("Profit Factor", f"{profit_factor}", "Ratio")
                k4.metric("Max Drawdown", f"-₹{abs(max_dd):,.2f}", f"{max_dd_pct:.1f}% DD")
                k5.metric("Avg Trade Expectancy", f"₹{expectancy:,.1f}", "Per Trade")
                k6.metric("Total Executions", total_trades, f"{timeframe} Stream")

                st.markdown("---")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    fig_e = go.Figure()
                    fig_e.add_trace(go.Scatter(
                        x=tdf['Exit Time'], y=tdf['Cum_PnL'],
                        mode='lines+markers', line=dict(color='#3fb950', width=2.5),
                        fill='tozeroy', fillcolor='rgba(63, 185, 80, 0.05)',
                        name='Net Growth'
                    ))
                    fig_e.update_layout(title="📈 Cumulative Equity Growth (₹)", template="plotly_dark", paper_bgcolor='#161b22', plot_bgcolor='#161b22', height=350)
                    st.plotly_chart(fig_e, use_container_width=True)

                with col_e2:
                    fig_d = go.Figure()
                    fig_d.add_trace(go.Scatter(
                        x=tdf['Exit Time'], y=tdf['Drawdown'],
                        mode='lines', line=dict(color='#f85149', width=2),
                        fill='tozeroy', fillcolor='rgba(248, 81, 73, 0.1)',
                        name='Drawdown'
                    ))
                    fig_d.update_layout(title="📉 Underwater Drawdown Curve (₹)", template="plotly_dark", paper_bgcolor='#161b22', plot_bgcolor='#161b22', height=350)
                    st.plotly_chart(fig_d, use_container_width=True)

        with tab_trades:
            if trades:
                st.markdown("#### 📜 Institutional Trade Execution Audit Logs")
                tdf_clean = tdf[['Entry Time', 'Exit Time', 'Type', 'Entry Price', 'Exit Price', 'Result', 'Points', 'PnL']].copy()
                st.dataframe(
                    tdf_clean.style.map(
                        lambda v: 'color: #3fb950; font-weight: bold;' if isinstance(v, (int, float)) and v > 0 else ('color: #f85149; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else ''),
                        subset=['PnL', 'Points']
                    ),
                    use_container_width=True, height=450
                )
                csv_buf = io.StringIO()
                tdf.to_csv(csv_buf, index=False)
                st.download_button(
                    label="📥 Export Trade Logs (CSV)",
                    data=csv_buf.getvalue(),
                    file_name=f"sam_quantum_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with tab_admin:
            st.markdown("#### 👥 Enterprise Access & License Controller")
            st.caption("Sam (Master Admin) can issue or revoke access keys for client accounts.")
            
            users_df = pd.DataFrame([
                {"User ID": u, "Client Name": d["name"], "Access Key": "••••••••", "License Tier": d["tier"]}
                for u, d in AUTHORIZED_USERS.items()
            ])
            st.table(users_df)
            st.info("💡 To grant access to a new user, simply add their credentials inside `AUTHORIZED_USERS` dictionary in `app_backtester.py`.")
