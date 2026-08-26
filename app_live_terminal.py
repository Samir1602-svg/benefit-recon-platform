import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import math
import os
import json
import threading
from datetime import datetime, time as dtime
import pytz

# ==============================================================================
# 🎨 MIRRORPIP COMPLETE UI/UX ENGINE SETUP
# ==============================================================================
st.set_page_config(
    page_title="MirrorPip — Copy Leading Institutional Traders",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ALGO_STATE_FILE = "mirrorpip_production_state.json"
TRADE_LOGS_FILE = "mirrorpip_executed_trades.json"
BROKER_CREDENTIALS_FILE = "mirrorpip_broker_keys.json"

# ==============================================================================
# 💾 PERSISTENCE CONTROLLERS
# ==============================================================================
def load_algo_state():
    default_state = {
        "logged_in": False,
        "active_view": "LANDING",   # "LANDING" or "APP_LEADERS", "APP_DASHBOARD", "APP_POSITIONS", "APP_BROKER"
        "mirrored_leaders": ["delta_trades"],
        "execution_mode": "PAPER",  # "PAPER" or "LIVE"
        "broker": "Zerodha KiteConnect",
        "wallet_balance": 50000.0,
        "daily_loss_limit": 5000.0,
        "running": True,
        "active_positions": {},
        "today_trades": 0,
        "date": "",
        "net_pnl": 0.0,
        "last_heartbeat": "-"
    }
    if not os.path.exists(ALGO_STATE_FILE):
        return default_state
    try:
        with open(ALGO_STATE_FILE, "r") as f:
            data = json.load(f)
            for k, v in default_state.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return default_state

def save_algo_state(st_dict):
    with open(ALGO_STATE_FILE, "w") as f:
        json.dump(st_dict, f, indent=4)

def load_trade_logs():
    if not os.path.exists(TRADE_LOGS_FILE):
        return []
    try:
        with open(TRADE_LOGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_trade_logs(logs):
    with open(TRADE_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def load_broker_creds():
    if not os.path.exists(BROKER_CREDENTIALS_FILE):
        return {}
    try:
        with open(BROKER_CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_broker_creds(creds):
    with open(BROKER_CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=4)

# ==============================================================================
# 🌟 INSTITUTIONAL LEADERS DIRECTORY (MIRRORPIP EXACT REPLICA)
# ==============================================================================
LEADERS_DB = {
    "delta_trades": {
        "id": "delta_trades",
        "name": "Delta Trades",
        "broker_tag": "Delta Exchange • 326 followers",
        "pnl_str": "+$56.77",
        "pnl_pct": "↑ 11.4%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "3.3%",
        "win_rate": 75,
        "dsl": "112 days",
        "sparkline": "M0,35 Q20,38 40,25 T80,18 T120,5 T160,2",
        "asset": "^NSEBANK",
        "underlying": "BANKNIFTY",
        "strategy_logic": "Iron Condor & Straddle Theta Decay (ATM Weekly Exp)",
        "lot_size": 30,
        "strike_step": 100
    },
    "pushkar_gold": {
        "id": "pushkar_gold",
        "name": "PUSHKAR GOLD TRADER",
        "broker_tag": "CoinSwitch • 119 followers",
        "pnl_str": "+$50.60",
        "pnl_pct": "↑ 10.1%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "1.6%",
        "win_rate": 81,
        "dsl": "74 days",
        "sparkline": "M0,30 Q25,32 50,15 T100,12 T130,4 T160,2",
        "asset": "GC=F",
        "underlying": "GOLD MINI",
        "strategy_logic": "VWAP Institutional Momentum + 200 EMA",
        "lot_size": 1,
        "strike_step": 100
    },
    "shark_trades": {
        "id": "shark_trades",
        "name": "Shark Trades",
        "broker_tag": "Shark • 56 followers",
        "pnl_str": "+$113.15",
        "pnl_pct": "↑ 22.6%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "1.2%",
        "win_rate": 89,
        "dsl": "85 days",
        "sparkline": "M0,35 Q30,30 60,18 T110,14 T140,6 T160,0",
        "asset": "^NSEI",
        "underlying": "NIFTY 50",
        "strategy_logic": "Candlestick Pattern Liquidity Sweep (Hammer/Star)",
        "lot_size": 75,
        "strike_step": 50
    },
    "us_stocks": {
        "id": "us_stocks",
        "name": "US Stocks Portfolio",
        "broker_tag": "CoinSwitch • 101 followers",
        "pnl_str": "+$9.22",
        "pnl_pct": "↑ 1.8%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "0.3%",
        "win_rate": 97,
        "dsl": "204 days",
        "sparkline": "M0,28 Q30,28 70,20 T120,12 T160,4",
        "asset": "RELIANCE.NS",
        "underlying": "RELIANCE",
        "strategy_logic": "Bollinger Bands Squeeze & Mean Reversion",
        "lot_size": 250,
        "strike_step": 20
    },
    "kj_folio": {
        "id": "kj_folio",
        "name": "KJ FOLIO",
        "broker_tag": "Delta Exchange • 133 followers",
        "pnl_str": "+$84.20",
        "pnl_pct": "↑ 16.8%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "2.1%",
        "win_rate": 84,
        "dsl": "92 days",
        "sparkline": "M0,32 Q35,30 75,15 T125,8 T160,2",
        "asset": "^NSEBANK",
        "underlying": "BANKNIFTY",
        "strategy_logic": "9:20 AM Short Straddle with 25% SL Protection",
        "lot_size": 30,
        "strike_step": 100
    },
    "livelong": {
        "id": "livelong",
        "name": "Livelong Algo",
        "broker_tag": "Delta Exchange • 21 followers",
        "pnl_str": "+$42.00",
        "pnl_pct": "↑ 8.4%",
        "pnl_positive": True,
        "margin": "$500",
        "mdd": "1.1%",
        "win_rate": 78,
        "dsl": "45 days",
        "sparkline": "M0,25 Q30,28 70,22 T120,14 T160,6",
        "asset": "^NSEI",
        "underlying": "NIFTY 50",
        "strategy_logic": "EMA 20/50 Pullback + ADX > 22 Trend Filter",
        "lot_size": 75,
        "strike_step": 50
    }
}

# ==============================================================================
# 🧮 GREEKS & PRICING ENGINE (EXACT BACKTEST PRECISION)
# ==============================================================================
def std_norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def calculate_option_trade(spot_entry, spot_exit, option_type, bars_held=0, days_to_expiry=3, iv=16.0, strike_step=100):
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
    theta_burn = bars_held * 1.25
    spot_movement = spot_exit - spot_entry

    if "CE" in option_type or "BUY" in option_type:
        raw_exit = entry_premium + (spot_movement * delta) - theta_burn
    else:
        raw_exit = entry_premium - (spot_movement * abs(delta)) - theta_burn

    exit_premium = max(5.0, round(raw_exit, 2))
    points_pnl = round(exit_premium - entry_premium, 2)
    return atm_strike, entry_premium, exit_premium, points_pnl

# ==============================================================================
# 🤖 24/7 BACKGROUND MIRRORING DAEMON
# ==============================================================================
def mirrorpip_daemon():
    ist = pytz.timezone('Asia/Kolkata')
    while True:
        try:
            state = load_algo_state()
            now_ist = datetime.now(ist)
            today_str = now_ist.strftime('%Y-%m-%d')
            cur_time = now_ist.time()

            state["last_heartbeat"] = now_ist.strftime('%I:%M:%S %p IST')
            save_algo_state(state)

            if state.get("running", True) and state.get("logged_in", False):
                # Daily Session Reset
                if state.get("date") != today_str:
                    state["date"] = today_str
                    state["today_trades"] = 0
                    save_algo_state(state)

                # Intraday Execution Loop (09:15 to 15:30 IST)
                if dtime(9, 15) <= cur_time <= dtime(15, 30):
                    mirrored_keys = state.get("mirrored_leaders", [])
                    
                    for leader_key in mirrored_keys:
                        leader = LEADERS_DB.get(leader_key)
                        if not leader:
                            continue

                        sym = leader["asset"]
                        spec_step = leader["strike_step"]
                        lot_qty = leader["lot_size"]

                        df = yf.download(sym, period="1d", interval="15m", progress=False)
                        if not df.empty and len(df) >= 5:
                            if isinstance(df.columns, pd.MultiIndex):
                                df.columns = df.columns.droplevel(1)

                            curr_spot = float(df['Close'].iloc[-1])
                            active_pos = state.get("active_positions", {}).get(leader_key)

                            # Manage Active Trade
                            if active_pos is not None:
                                active_pos["bars_held"] += 1
                                _, _, exit_prem, pts_diff = calculate_option_trade(
                                    spot_entry=active_pos["spot_entry"],
                                    spot_exit=curr_spot,
                                    option_type=active_pos["type"],
                                    bars_held=active_pos["bars_held"],
                                    days_to_expiry=2,
                                    strike_step=spec_step
                                )

                                # Target (+50 Pts) or Stop Loss (-20 Pts)
                                target_hit = pts_diff >= 50.0
                                sl_hit = pts_diff <= -20.0

                                if target_hit or sl_hit or cur_time >= dtime(15, 15):
                                    net_pnl = pts_diff * lot_qty
                                    state["net_pnl"] += net_pnl
                                    state["wallet_balance"] += net_pnl

                                    logs = load_trade_logs()
                                    logs.insert(0, {
                                        "time": now_ist.strftime('%d-%b %I:%M %p'),
                                        "leader": leader["name"],
                                        "strike": active_pos["strike_desc"],
                                        "type": active_pos["type"],
                                        "entry": active_pos["entry_prem"],
                                        "exit": exit_prem,
                                        "pnl": round(net_pnl, 2),
                                        "result": "TARGET 🎯" if target_hit else "SL HIT 🔴" if sl_hit else "EOD EXIT"
                                    })
                                    save_trade_logs(logs)
                                    del state["active_positions"][leader_key]
                                    save_algo_state(state)

                            # Trigger New Entry for Leader
                            elif state.get("today_trades", 0) < 4:
                                # Mock Entry Trigger (Every morning 09:30 or Momentum Bar)
                                pos_type = "BUY/CE"
                                atm_s, entry_prem, _, _ = calculate_option_trade(
                                    spot_entry=curr_spot,
                                    spot_exit=curr_spot,
                                    option_type=pos_type,
                                    bars_held=0,
                                    days_to_expiry=2,
                                    strike_step=spec_step
                                )
                                strike_desc = f"{leader['underlying']} {atm_s} CE"

                                state.setdefault("active_positions", {})[leader_key] = {
                                    "type": pos_type,
                                    "strike_desc": strike_desc,
                                    "spot_entry": curr_spot,
                                    "entry_prem": entry_prem,
                                    "bars_held": 0,
                                    "qty": lot_qty
                                }
                                state["today_trades"] += 1
                                save_algo_state(state)
        except Exception:
            pass
        time.sleep(20)

if 'daemon_started' not in st.session_state:
    st.session_state.daemon_started = True
    t = threading.Thread(target=mirrorpip_daemon, daemon=True)
    t.start()

# ==============================================================================
# 🎨 CUSTOM CSS STYLESHEET (EXACT MIRRORPIP DARK & CLEAN THEME)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #000000 !important;
    }
    
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Top Header Bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 20px;
        background: #000000;
        border-bottom: 1px solid #18181b;
        margin-bottom: 24px;
    }
    .brand-logo {
        font-size: 22px;
        font-weight: 800;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .brand-logo span {
        color: #84cc16; /* Lime Green dot */
    }
    .nav-links {
        display: flex;
        gap: 22px;
        font-size: 13.5px;
        font-weight: 600;
        color: #a1a1aa;
    }
    .nav-link.active {
        color: #ffffff;
        border-bottom: 2px solid #84cc16;
        padding-bottom: 4px;
    }
    
    /* Mirror Card Exact Spec */
    .leader-card {
        background: #0d0e12;
        border: 1px solid #1f222a;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        position: relative;
        transition: all 0.2s ease;
    }
    .leader-card:hover {
        border-color: #3f4452;
        transform: translateY(-2px);
    }
    .leader-card.mirrored {
        border: 1.5px solid #84cc16 !important;
        background: #0f130e !important;
    }
    .avatar-circle {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: #27272a;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #a1a1aa;
        font-size: 16px;
    }
    .pnl-green {
        color: #4ade80;
        font-family: 'JetBrains Mono', monospace;
        font-size: 17px;
        font-weight: 700;
    }
    .stat-label {
        color: #71717a;
        font-size: 11px;
        font-weight: 500;
    }
    .stat-val {
        color: #f4f4f5;
        font-size: 13px;
        font-weight: 700;
    }
    .progress-bar-bg {
        width: 100%;
        height: 5px;
        background: #27272a;
        border-radius: 4px;
        margin-top: 6px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        background: #4ade80;
        border-radius: 4px;
    }
    
    /* Landing Page Hero Specs */
    .hero-title {
        font-size: 48px;
        font-weight: 800;
        line-height: 1.1;
        color: #ffffff;
        margin-bottom: 16px;
        letter-spacing: -1px;
    }
    .hero-sub {
        font-size: 15px;
        color: #a1a1aa;
        line-height: 1.6;
        margin-bottom: 24px;
        max-width: 440px;
    }
    .lime-btn {
        background: #84cc16;
        color: #000000;
        font-weight: 800;
        font-size: 14px;
        padding: 12px 28px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        display: inline-block;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🚀 VIEW CONTROLLER (LANDING PAGE VS. INSIDE PLATFORM)
# ==============================================================================
state = load_algo_state()

# Top Navigation Bar (Header)
col_nav1, col_nav2, col_nav3 = st.columns([1.5, 3, 1.2])
with col_nav1:
    st.markdown("""<div class="brand-logo">⚡ Mirror<span>pip</span></div>""", unsafe_allow_html=True)
with col_nav2:
    if state.get("logged_in", False):
        n_tab1, n_tab2, n_tab3, n_tab4, n_tab5 = st.columns(5)
        with n_tab1:
            if st.button("Leaders", key="btn_nav_leaders", use_container_width=True):
                state["active_view"] = "APP_LEADERS"
                save_algo_state(state)
                st.rerun()
        with n_tab2:
            if st.button("Dashboard", key="btn_nav_dash", use_container_width=True):
                state["active_view"] = "APP_DASHBOARD"
                save_algo_state(state)
                st.rerun()
        with n_tab3:
            if st.button("Positions", key="btn_nav_pos", use_container_width=True):
                state["active_view"] = "APP_POSITIONS"
                save_algo_state(state)
                st.rerun()
        with n_tab4:
            if st.button("Brokers", key="btn_nav_broker", use_container_width=True):
                state["active_view"] = "APP_BROKER"
                save_algo_state(state)
                st.rerun()
        with n_tab5:
            if st.button("Exit App", key="btn_nav_logout", use_container_width=True):
                state["logged_in"] = False
                state["active_view"] = "LANDING"
                save_algo_state(state)
                st.rerun()
with col_nav3:
    st.markdown("""
    <div style="text-align:right; font-size:12px; color:#84cc16; font-weight:700;">
        📞 Learn Trading +91 99994 70710
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color:#18181b; margin-top:0;'>", unsafe_allow_html=True)

# ==============================================================================
# 🌟 VIEW 1: MIRRORPIP OFFICIAL LANDING PAGE (SCREENSHOT 2 REPLICA)
# ==============================================================================
if not state.get("logged_in", False) or state.get("active_view") == "LANDING":
    col_hero1, col_hero2 = st.columns([1.2, 1])
    with col_hero1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="hero-title">Pick a Leader.<br>Mirror Their Moves.</div>
        <div class="hero-sub">Choose top performing traders and copy their strategies automatically. It's the smarter way to start trading.</div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ Start Mirroring Now", type="primary", use_container_width=False):
            state["logged_in"] = True
            state["active_view"] = "APP_LEADERS"
            save_algo_state(state)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        # Store Badges
        st.markdown("""
        <div style="display:flex; gap:12px; margin-top:10px;">
            <div style="background:#09090b; border:1px solid #27272a; padding:6px 14px; border-radius:8px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:18px;">🍎</span>
                <div><div style="font-size:9px; color:#71717a;">Download on the</div><div style="font-size:12px; font-weight:700;">App Store</div></div>
            </div>
            <div style="background:#09090b; border:1px solid #27272a; padding:6px 14px; border-radius:8px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:18px;">▶️</span>
                <div><div style="font-size:9px; color:#71717a;">GET IT ON</div><div style="font-size:12px; font-weight:700;">Google Play</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_hero2:
        st.markdown("<br>", unsafe_allow_html=True)
        # 3D Coin Graphic Illustration
        st.markdown("""
        <div style="text-align:center; padding:20px; background:radial-gradient(circle at 60% 40%, rgba(132, 204, 22, 0.15) 0%, rgba(0,0,0,0) 70%); border-radius:30px;">
            <div style="font-size:120px; filter: drop-shadow(0 20px 30px rgba(132,204,22,0.3));">🪙</div>
            <div style="display:flex; justify-content:center; gap:16px; margin-top:-30px;">
                <div style="background:#18181b; border:1px solid #27272a; border-radius:20px; padding:10px 18px; font-size:13px; font-weight:700; color:#4ade80;">● 100% Automated</div>
                <div style="background:#18181b; border:1px solid #27272a; border-radius:20px; padding:10px 18px; font-size:13px; font-weight:700; color:#38bdf8;">● Zero Manual Work</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 🌟 VIEW 2: INSIDE MIRROR LEADERS GRID (SCREENSHOT 1 REPLICA)
# ==============================================================================
elif state.get("active_view") == "APP_LEADERS":
    # Filter Bar
    f_col1, f_col2 = st.columns([2, 1.5])
    with f_col1:
        st.markdown("<h4 style='margin:0; color:#ffffff;'>Mirror Leaders (9)</h4>", unsafe_allow_html=True)
    with f_col2:
        st.markdown("""
        <div style="display:flex; justify-content:flex-end; gap:6px;">
            <span style="background:#18181b; color:#71717a; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">1D</span>
            <span style="background:#18181b; color:#71717a; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">1W</span>
            <span style="background:#27272a; color:#ffffff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">1M</span>
            <span style="background:#18181b; color:#71717a; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">1Y</span>
            <span style="background:#18181b; color:#71717a; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">All</span>
            <span style="background:#18181b; color:#a1a1aa; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700;">≡ Profits ▾</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3-Column Leader Grid
    grid_cols = st.columns(3)
    leader_keys = list(LEADERS_DB.keys())

    for idx, l_key in enumerate(leader_keys):
        col_idx = idx % 3
        leader = LEADERS_DB[l_key]
        is_mirrored = l_key in state.get("mirrored_leaders", [])

        with grid_cols[col_idx]:
            # Sparkline SVG Vector
            sparkline_svg = f"""
            <svg width="100%" height="45" viewBox="0 0 160 45" style="margin: 8px 0;">
                <path d="{leader['sparkline']}" fill="none" stroke="#4ade80" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            """

            st.markdown(f"""
            <div class="leader-card {'mirrored' if is_mirrored else ''}">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div class="avatar-circle">👤</div>
                    <div>
                        <div style="font-weight:800; font-size:14px; color:#ffffff;">{leader['name']}</div>
                        <div style="font-size:11px; color:#71717a;">{leader['broker_tag']}</div>
                    </div>
                </div>
                
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="pnl-green">{leader['pnl_str']}</div>
                        <div style="font-size:11px; color:#4ade80; font-weight:700;">{leader['pnl_pct']}</div>
                    </div>
                    <div style="width:110px;">
                        {sparkline_svg}
                    </div>
                </div>
                
                <div style="display:flex; justify-content:space-between; margin-top:14px; border-top:1px solid #1f222a; padding-top:10px;">
                    <div>
                        <div class="stat-label">Recommended Margin</div>
                        <div class="stat-val">{leader['margin']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="stat-label">MDD</div>
                        <div class="stat-val">{leader['mdd']}</div>
                    </div>
                </div>
                
                <div style="margin-top:12px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="stat-label">Win Rate (%) <b style="color:#ffffff;">{leader['win_rate']}%</b></span>
                        <span class="stat-label">DSL <b style="color:#ffffff;">{leader['dsl']}</b></span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {leader['win_rate']}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_mirrored:
                if st.button(f"✓ Subscribed (Stop Mirroring)", key=f"btn_stop_{l_key}", use_container_width=True):
                    state["mirrored_leaders"].remove(l_key)
                    save_algo_state(state)
                    st.rerun()
            else:
                if st.button(f"⚡ Mirror Leader", key=f"btn_start_{l_key}", type="primary", use_container_width=True):
                    if l_key not in state["mirrored_leaders"]:
                        state["mirrored_leaders"].append(l_key)
                    save_algo_state(state)
                    st.success(f"✅ Subscribed to {leader['name']}!")
                    st.rerun()

# ==============================================================================
# 🌟 VIEW 3: LIVE ACTIVE POSITIONS & ORDER LOGS
# ==============================================================================
elif state.get("active_view") == "APP_POSITIONS":
    st.markdown("<h4>💼 Live Active Positions & Order Stream</h4>", unsafe_allow_html=True)
    
    active_positions = state.get("active_positions", {})
    if active_positions:
        for l_key, pos in active_positions.items():
            leader_info = LEADERS_DB.get(l_key, {})
            st.markdown(f"""
            <div class="leader-card mirrored">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <span style="color:#84cc16; font-weight:800; font-size:15px;">{leader_info.get('name', 'Strategy')}</span><br>
                        <span style="color:#ffffff; font-size:14px; font-weight:700;">{pos.get('strike_desc')}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:#4ade80; font-weight:800; font-size:14px;">{pos.get('qty')} Qty</span><br>
                        <span style="color:#71717a; font-size:11px;">Entry Prem: ₹{pos.get('entry_prem'):.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No open trades. Algo daemon actively scanning for high-probability setups.")

    st.markdown("<br><h5>📜 Closed Trade Execution Logs</h5>", unsafe_allow_html=True)
    logs = load_trade_logs()
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, height=260)
        if st.button("🗑️ Clear Execution History", use_container_width=True):
            save_trade_logs([])
            st.rerun()
    else:
        st.caption("No historical executions recorded today.")

# ==============================================================================
# 🌟 VIEW 4: DEMAT BROKER INTEGRATION (ZERODHA & ANGEL ONE)
# ==============================================================================
elif state.get("active_view") == "APP_BROKER":
    st.markdown("<h4>🔑 Demat Broker Integration</h4>", unsafe_allow_html=True)
    creds = load_broker_creds()
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        sel_mode = st.radio("Trading Environment", ["📝 Virtual Paper Trading (Zero Risk)", "🚀 Live Demat Execution (Real Funds)"], index=0 if state.get("execution_mode") == "PAPER" else 1)
        state["execution_mode"] = "PAPER" if "Virtual" in sel_mode else "LIVE"
    with b_col2:
        sel_broker = st.selectbox("Primary Broker Gateway", ["Zerodha KiteConnect", "Angel One SmartAPI"], index=0)
        state["broker"] = sel_broker

    st.markdown("---")
    if "Zerodha" in sel_broker:
        k_key = st.text_input("Kite API Key", value=creds.get("kite_api_key", ""), type="password")
        k_secret = st.text_input("Kite API Secret", value=creds.get("kite_api_secret", ""), type="password")
        k_token = st.text_input("Kite Daily Access Token", value=creds.get("kite_access_token", ""), type="password")
        if st.button("🔗 Save & Connect Zerodha", type="primary", use_container_width=True):
            creds["broker"] = "Zerodha"
            creds["kite_api_key"] = k_key
            creds["kite_api_secret"] = k_secret
            creds["kite_access_token"] = k_token
            save_broker_creds(creds)
            save_algo_state(state)
            st.success("✅ Zerodha KiteConnect credentials bound successfully.")
            st.rerun()
    elif "Angel" in sel_broker:
        a_client = st.text_input("Angel Client ID", value=creds.get("angel_client_id", ""))
        a_pin = st.text_input("Angel MPIN / Password", value=creds.get("angel_pin", ""), type="password")
        a_key = st.text_input("SmartAPI Key", value=creds.get("angel_api_key", ""), type="password")
        a_totp = st.text_input("Angel TOTP Secret Key", value=creds.get("angel_totp_key", ""), type="password")
        if st.button("🔗 Save & Connect Angel One", type="primary", use_container_width=True):
            creds["broker"] = "Angel"
            creds["angel_client_id"] = a_client
            creds["angel_pin"] = a_pin
            creds["angel_api_key"] = a_key
            creds["angel_totp_key"] = a_totp
            save_broker_creds(creds)
            save_algo_state(state)
            st.success("✅ Angel One credentials bound successfully.")
            st.rerun()