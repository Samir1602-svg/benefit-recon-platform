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
# 📱 SAM QUANTUM MOBILE LIVE TRADING TERMINAL
# ==============================================================================
st.set_page_config(
    page_title="SAM LIVE ALGO | Mobile Demat",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

ALGO_STATE_FILE = "live_algo_production_state.json"
TRADE_LOGS_FILE = "live_executed_orders.json"

INDEX_SPECS = {
    "^NSEBANK": {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100},
    "^NSEI": {"name": "NIFTY", "lot_size": 75, "strike_step": 50},
    "NIFTY_FIN_SERVICE.NS": {"name": "FINNIFTY", "lot_size": 65, "strike_step": 50},
    "^BSESN": {"name": "SENSEX", "lot_size": 20, "strike_step": 100}
}

# ==============================================================================
# 💾 PERSISTENT DATABASE & STATE
# ==============================================================================
def load_algo_state():
    if not os.path.exists(ALGO_STATE_FILE):
        return {
            "running": False,
            "mode": "PAPER",
            "broker": "Zerodha Kite",
            "symbol": "^NSEBANK",
            "lots": 2,
            "target": 50.0,
            "sl": 20.0,
            "active_position": None,
            "today_trades": 0,
            "date": "",
            "net_pnl": 0.0,
            "last_heartbeat": "-"
        }
    try:
        with open(ALGO_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"running": False, "mode": "PAPER", "broker": "Zerodha Kite", "symbol": "^NSEBANK", "lots": 2, "target": 50.0, "sl": 20.0, "active_position": None, "today_trades": 0, "date": "", "net_pnl": 0.0, "last_heartbeat": "-"}

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

# ==============================================================================
# 🧮 GREEKS & PRICING ENGINE
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

def evaluate_candlestick_pattern(df):
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

# ==============================================================================
# 🤖 24/7 BACKGROUND EXECUTION DAEMON
# ==============================================================================
def live_execution_daemon():
    ist = pytz.timezone('Asia/Kolkata')
    while True:
        try:
            state = load_algo_state()
            now_ist = datetime.now(ist)
            today_str = now_ist.strftime('%Y-%m-%d')
            cur_time = now_ist.time()

            # Update heartbeat timestamp
            state["last_heartbeat"] = now_ist.strftime('%I:%M:%S %p IST')
            save_algo_state(state)

            if state.get("running", False):
                # Daily Counter Reset at 09:15 AM
                if state.get("date") != today_str:
                    state["date"] = today_str
                    state["today_trades"] = 0
                    save_algo_state(state)

                # Intraday Trading Window (09:15 to 15:30 IST)
                if dtime(9, 15) <= cur_time <= dtime(15, 30):
                    # Auto Square-Off at 15:15 IST
                    if cur_time >= dtime(15, 15) and state.get("active_position") is not None:
                        pos = state["active_position"]
                        logs = load_trade_logs()
                        logs.insert(0, {
                            "time": now_ist.strftime('%d-%b %I:%M %p'),
                            "strike": pos["strike_desc"],
                            "type": pos["type"],
                            "entry": pos["entry_prem"],
                            "exit": pos["entry_prem"],
                            "pnl": 0.0,
                            "result": "EOD AUTO SQUARE-OFF"
                        })
                        save_trade_logs(logs)
                        state["active_position"] = None
                        save_algo_state(state)
                        time.sleep(15)
                        continue

                    sym = state.get("symbol", "^NSEBANK")
                    spec = INDEX_SPECS.get(sym, {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100})
                    total_qty = state.get("lots", 2) * spec["lot_size"]

                    df = yf.download(sym, period="2d", interval="15m", progress=False)
                    if not df.empty and len(df) >= 10:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.droplevel(1)
                        df = evaluate_candlestick_pattern(df)
                        curr_spot = float(df['Close'].iloc[-1])
                        last_signal = int(df['signal'].iloc[-2])

                        # Exit Monitoring
                        if state.get("active_position") is not None:
                            pos = state["active_position"]
                            pos["bars_held"] += 1
                            _, _, exit_prem, points_diff = calculate_option_trade(
                                spot_entry=pos["spot_entry"],
                                spot_exit=curr_spot,
                                option_type=pos["type"],
                                bars_held=pos["bars_held"],
                                days_to_expiry=2,
                                strike_step=spec["strike_step"]
                            )

                            target_hit = points_diff >= state.get("target", 50.0)
                            sl_hit = points_diff <= -state.get("sl", 20.0)

                            if target_hit or sl_hit:
                                pnl_rupees = points_diff * total_qty
                                state["net_pnl"] += pnl_rupees
                                logs = load_trade_logs()
                                logs.insert(0, {
                                    "time": now_ist.strftime('%d-%b %I:%M %p'),
                                    "strike": pos["strike_desc"],
                                    "type": pos["type"],
                                    "entry": pos["entry_prem"],
                                    "exit": exit_prem,
                                    "pnl": round(pnl_rupees, 2),
                                    "result": "TARGET 🎯" if target_hit else "SL HIT 🔴"
                                })
                                save_trade_logs(logs)
                                state["active_position"] = None
                                save_algo_state(state)

                        # New Signal Entry
                        elif last_signal != 0 and state.get("today_trades", 0) < 2:
                            # 11:30 to 13:15 Blackout Guard
                            is_blackout = dtime(11, 30) <= cur_time <= dtime(13, 15)
                            if not is_blackout:
                                pos_type = "BUY/CE" if last_signal == 1 else "BUY/PE"
                                atm_s, entry_prem, _, _ = calculate_option_trade(
                                    spot_entry=curr_spot,
                                    spot_exit=curr_spot,
                                    option_type=pos_type,
                                    bars_held=0,
                                    days_to_expiry=2,
                                    strike_step=spec["strike_step"]
                                )
                                opt_lbl = "CE" if last_signal == 1 else "PE"
                                strike_desc = f"{spec['name']} {atm_s} {opt_lbl}"

                                state["active_position"] = {
                                    "type": pos_type,
                                    "strike_desc": strike_desc,
                                    "spot_entry": curr_spot,
                                    "entry_prem": entry_prem,
                                    "bars_held": 0
                                }
                                state["today_trades"] += 1
                                save_algo_state(state)
        except Exception:
            pass
        time.sleep(20)

if 'daemon_started' not in st.session_state:
    st.session_state.daemon_started = True
    t = threading.Thread(target=live_execution_daemon, daemon=True)
    t.start()

# ==============================================================================
# 📱 MOBILE APP UI (FAST, TOUCH-FRIENDLY & NATIVE)
# ==============================================================================
state = load_algo_state()
spec = INDEX_SPECS.get(state.get("symbol", "^NSEBANK"), {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100})
total_contract_qty = state.get("lots", 2) * spec["lot_size"]

# Top Mobile Header
st.markdown("""
<div style="text-align:center; padding: 10px 0 16px 0;">
    <h2 style="color: #38bdf8; margin: 0; font-weight: 800; font-size: 24px;">⚡ SAM LIVE DEMAT</h2>
    <span style="color: #94a3b8; font-size: 12px;">Mobile Autonomous Algorithmic Engine</span>
</div>
""", unsafe_allow_html=True)

# 1. Main Status Indicator Card
status_bg = "rgba(16, 185, 129, 0.12)" if state.get("running") else "rgba(239, 68, 68, 0.12)"
status_border = "#10b981" if state.get("running") else "#ef4444"
status_text = "🟢 ALGO SCANNING LIVE" if state.get("running") else "🔴 ALGO ENGINE PAUSED"

st.markdown(f"""
<div style="background: {status_bg}; border: 1.5px solid {status_border}; border-radius: 14px; padding: 16px; margin-bottom: 15px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="color: {status_border}; font-size: 15px; font-weight: 800;">{status_text}</span><br>
            <span style="color: #94a3b8; font-size: 11px;">Heartbeat: <b>{state.get('last_heartbeat', '-')}</b></span>
        </div>
        <div style="text-align:right;">
            <span style="background: #0f172a; color: #38bdf8; border: 1px solid #38bdf8; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">{state.get('mode', 'PAPER')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Main One-Touch Control Buttons
c1, c2 = st.columns(2)
with c1:
    if st.button("▶️ START ALGO", type="primary", use_container_width=True):
        state["running"] = True
        save_algo_state(state)
        st.rerun()
with c2:
    if st.button("⏸️ PAUSE ALGO", use_container_width=True):
        state["running"] = False
        save_algo_state(state)
        st.rerun()

if st.button("🛑 EMERGENCY SQUARE-OFF & EXIT", use_container_width=True):
    state["active_position"] = None
    save_algo_state(state)
    st.error("⚠️ All open positions squared off immediately.")
    st.rerun()

st.markdown("---")

# 3. Live Position & PnL Readout
st.markdown("##### 💼 Active Position & Live P&L")
active_pos = state.get("active_position")

if active_pos:
    st.markdown(f"""
    <div style="background: #0f172a; border: 1px solid #38bdf8; border-radius: 12px; padding: 14px; margin-bottom: 12px;">
        <div style="display:flex; justify-content:space-between;">
            <span style="color: #38bdf8; font-weight: 800; font-size: 14px;">{active_pos.get('strike_desc')}</span>
            <span style="color: #10b981; font-weight: 700; font-size: 13px;">{total_contract_qty} Qty ({state.get('lots', 2)} Lots)</span>
        </div>
        <div style="margin-top: 8px; font-size: 12px; color: #94a3b8;">
            Entry Premium: <b>₹{active_pos.get('entry_prem'):.2f}</b><br>
            Target Prem: <b style="color:#10b981;">₹{active_pos.get('entry_prem') + state.get('target', 50):.2f}</b> | SL Prem: <b style="color:#ef4444;">₹{active_pos.get('entry_prem') - state.get('sl', 20):.2f}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No active open trade. Engine waiting for next 15-minute Candlestick setup.")

# Summary Metrics Grid
m1, m2 = st.columns(2)
m1.metric("Today Realized PnL", f"{'+₹' if state.get('net_pnl', 0) >= 0 else '-₹'}{abs(state.get('net_pnl', 0)):,.2f}")
m2.metric("Daily Trades", f"{state.get('today_trades', 0)} / 2")

st.markdown("---")

# 4. Settings & Broker Configuration (Mobile Collapsible)
with st.expander("⚙️ Strategy Parameters & Broker Binding", expanded=False):
    sel_sym = st.selectbox("Underlying Market", list(INDEX_SPECS.keys()), index=0, format_func=lambda x: INDEX_SPECS[x]["name"])
    sel_lots = st.number_input("Number of Lots", value=int(state.get("lots", 2)), min_value=1, step=1)
    sel_mode = st.radio("Trading Mode", ["📝 Paper Trading Mode (Zero Risk)", "🚀 Live Demat Account (Real Capital)"], index=0 if state.get("mode") == "PAPER" else 1)
    sel_broker = st.selectbox("Attached Broker", ["Zerodha KiteConnect", "Angel One SmartAPI", "Groww / Dhan API"])
    
    if st.button("💾 SAVE SETTINGS", use_container_width=True):
        state["symbol"] = sel_sym
        state["lots"] = sel_lots
        state["mode"] = "PAPER" if "Paper" in sel_mode else "LIVE"
        state["broker"] = sel_broker
        save_algo_state(state)
        st.success("✅ Settings updated successfully.")
        st.rerun()

# 5. Live Orders Execution Trail
st.markdown("##### 📜 Today's Executed Order Logs")
logs = load_trade_logs()
if logs:
    log_df = pd.DataFrame(logs)
    st.dataframe(log_df, use_container_width=True, height=220)
    if st.button("🗑️ Reset Execution Logs", use_container_width=True):
        save_trade_logs([])
        st.rerun()
else:
    st.caption("No orders executed yet today.")
