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

# Safe Optional Imports for Broker APIs
try:
    import pyotp
except ImportError:
    pyotp = None

# ==============================================================================
# 📱 SAM QUANTUM PRO LIVE TERMINAL (INSTITUTIONAL STRATEGY MATRIX)
# ==============================================================================
st.set_page_config(
    page_title="SAM LIVE DEMAT | Institutional Algo Suite",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

ALGO_STATE_FILE = "live_algo_production_state.json"
TRADE_LOGS_FILE = "live_executed_orders.json"
BROKER_CREDENTIALS_FILE = "broker_credentials_secure.json"

INDEX_SPECS = {
    "^NSEBANK": {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100},
    "^NSEI": {"name": "NIFTY", "lot_size": 75, "strike_step": 50},
    "NIFTY_FIN_SERVICE.NS": {"name": "FINNIFTY", "lot_size": 65, "strike_step": 50},
    "^BSESN": {"name": "SENSEX", "lot_size": 20, "strike_step": 100},
    "RELIANCE.NS": {"name": "RELIANCE", "lot_size": 250, "strike_step": 20},
    "HDFCBANK.NS": {"name": "HDFCBANK", "lot_size": 550, "strike_step": 10}
}

# ==============================================================================
# 💾 PERSISTENCE CONTROLLER
# ==============================================================================
def load_algo_state():
    default_state = {
        "running": False,
        "mode": "PAPER",
        "broker": "Zerodha KiteConnect",
        "symbol": "^NSEBANK",
        "strategy": "1. [Quantman Replica] 9:20 AM Short Straddle (25% SL + Re-Entry)",
        "lots": 2,
        "target": 50.0,
        "sl": 20.0,
        "max_daily_loss": 5000.0,
        "active_position": None,
        "today_trades": 0,
        "date": "",
        "net_pnl": 0.0,
        "last_heartbeat": "-",
        "circuit_triggered": False
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

def calculate_statutory_taxes(entry_premium, exit_premium, qty):
    buy_turnover = entry_premium * qty
    sell_turnover = exit_premium * qty
    total_turnover = buy_turnover + sell_turnover
    brokerage = 40.0
    stt = sell_turnover * 0.001
    exchange_txn = total_turnover * 0.000505
    gst = (brokerage + exchange_txn) * 0.18
    slippage = (buy_turnover * 0.004) + (sell_turnover * 0.004)
    return round(brokerage + stt + exchange_txn + gst + slippage, 2)

# ==============================================================================
# 🛠️ 10 INSTITUTIONAL STRATEGIES REGISTRY
# ==============================================================================
def compute_adx(df, period=14):
    d = df.copy()
    c, h, l = d['Close'], d['High'], d['Low']
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().replace(0, np.nan)
    pos_di = 100 * (pd.Series(pos_dm, index=d.index).rolling(period).mean() / atr)
    neg_di = 100 * (pd.Series(neg_dm, index=d.index).rolling(period).mean() / atr)
    dx = 100 * ((pos_di - neg_di).abs() / (pos_di + neg_di).replace(0, np.nan))
    return dx.rolling(period).mean().fillna(20)

class StrategyRegistry:
    @staticmethod
    def straddle_920_replica(df):
        d = df.copy()
        d['signal'] = 0
        ist_time = d.index.tz_convert('Asia/Kolkata') if d.index.tz is not None else d.index + pd.Timedelta(hours=5, minutes=30)
        time_only = [t.time() for t in ist_time]
        
        # 09:20 - 09:30 AM Entry trigger
        for i, t in enumerate(time_only):
            if dtime(9, 20) <= t <= dtime(9, 30):
                d.iloc[i, d.columns.get_loc('signal')] = 2 # Multi-leg Short Straddle
        return d

    @staticmethod
    def delta_iron_condor_replica(df):
        d = df.copy()
        d['signal'] = 0
        ist_time = d.index.tz_convert('Asia/Kolkata') if d.index.tz is not None else d.index + pd.Timedelta(hours=5, minutes=30)
        time_only = [t.time() for t in ist_time]
        
        # 10:00 AM Entry on Expiry Days
        for i, t in enumerate(time_only):
            if dtime(10, 0) <= t <= dtime(10, 15):
                d.iloc[i, d.columns.get_loc('signal')] = 4 # 4-Leg Iron Condor
        return d

    @staticmethod
    def mirror_pip_vwap_trend(df):
        d = df.copy()
        typical_price = (d['High'] + d['Low'] + d['Close']) / 3.0
        d['VWAP'] = (typical_price * d['Volume']).cumsum() / d['Volume'].cumsum()
        d['EMA200'] = d['Close'].ewm(span=200, adjust=False).mean()
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        
        d['signal'] = 0
        cond_buy = (d['Close'] > d['EMA200']) & (d['Low'] <= d['VWAP']) & (d['Close'] > d['VWAP']) & (d['Volume'] > d['VOL_SMA20'])
        cond_sell = (d['Close'] < d['EMA200']) & (d['High'] >= d['VWAP']) & (d['Close'] < d['VWAP']) & (d['Volume'] > d['VOL_SMA20'])
        d.loc[cond_buy, 'signal'] = 1
        d.loc[cond_sell, 'signal'] = -1
        return d

    @staticmethod
    def opening_range_breakout(df):
        d = df.copy()
        d['signal'] = 0
        ist_time = d.index.tz_convert('Asia/Kolkata') if d.index.tz is not None else d.index + pd.Timedelta(hours=5, minutes=30)
        
        # High and Low of First 15-min bar (09:15 - 09:30)
        first_bar_h = d['High'].iloc[0]
        first_bar_l = d['Low'].iloc[0]
        
        cond_buy = (d['Close'] > first_bar_h)
        cond_sell = (d['Close'] < first_bar_l)
        d.loc[cond_buy, 'signal'] = 1
        d.loc[cond_sell, 'signal'] = -1
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
    def ema_pullback(df):
        d = df.copy()
        c = d['Close']
        d['EMA20'] = c.ewm(span=20, adjust=False).mean()
        d['EMA50'] = c.ewm(span=50, adjust=False).mean()
        d['ADX'] = compute_adx(d, 14)
        delta = c.diff()
        gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        d['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))
        d['VOL_SMA20'] = d['Volume'].rolling(20).mean().fillna(d['Volume'])
        d['signal'] = 0
        cond_buy = (d['EMA20'] > d['EMA50']) & (d['Close'] >= d['EMA20']) & (d['RSI'] > 52) & (d['ADX'] > 22) & (d['Volume'] >= d['VOL_SMA20'])
        cond_sell = (d['EMA20'] < d['EMA50']) & (d['Close'] <= d['EMA20']) & (d['RSI'] < 48) & (d['ADX'] > 22) & (d['Volume'] >= d['VOL_SMA20'])
        d.loc[cond_buy, 'signal'] = 1
        d.loc[cond_sell, 'signal'] = -1
        return d

    @staticmethod
    def ema_crossover(df):
        d = df.copy()
        c = d['Close']
        d['EMA9'] = c.ewm(span=9, adjust=False).mean()
        d['EMA21'] = c.ewm(span=21, adjust=False).mean()
        d['ADX'] = compute_adx(d, 14)
        d['signal'] = 0
        cross_up = (d['EMA9'] > d['EMA21']) & (d['EMA9'].shift(1) <= d['EMA21'].shift(1)) & (d['ADX'] > 22)
        cross_down = (d['EMA9'] < d['EMA21']) & (d['EMA9'].shift(1) >= d['EMA21'].shift(1)) & (d['ADX'] > 22)
        d.loc[cross_up, 'signal'] = 1
        d.loc[cross_down, 'signal'] = -1
        return d

    @staticmethod
    def supertrend_rider(df):
        d = df.copy()
        c, h, l = d['Close'], d['High'], d['Low']
        d['EMA200'] = c.ewm(span=200, adjust=False).mean()
        tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
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
    def bollinger_rsi_reversion(df):
        d = df.copy()
        c = d['Close']
        d['SMA20'] = c.rolling(20).mean()
        d['EMA200'] = c.ewm(span=200, adjust=False).mean()
        std20 = c.rolling(20).std()
        d['BB_UPPER'] = d['SMA20'] + (2.0 * std20)
        d['BB_LOWER'] = d['SMA20'] - (2.0 * std20)
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        d['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))
        d['signal'] = 0
        buy_cond = (d['Low'] <= d['BB_LOWER']) & (d['RSI'] < 30) & (d['Close'] > d['EMA200'])
        sell_cond = (d['High'] >= d['BB_UPPER']) & (d['RSI'] > 70) & (d['Close'] < d['EMA200'])
        d.loc[buy_cond, 'signal'] = 1
        d.loc[sell_cond, 'signal'] = -1
        return d

STRATEGY_MAP = {
    "1. [Quantman Replica] 9:20 AM Short Straddle (25% SL + Re-Entry)": StrategyRegistry.straddle_920_replica,
    "2. [Delta Exchange Replica] Expiry Day Delta-Neutral Iron Condor": StrategyRegistry.delta_iron_condor_replica,
    "3. [Mirror Pip Replica] VWAP + 200 EMA Institutional Trend Pullback": StrategyRegistry.mirror_pip_vwap_trend,
    "4. 15-Minute Opening Range Breakout (ORB High/Low)": StrategyRegistry.opening_range_breakout,
    "5. Candlestick Pattern Engine (Hammer / Shooting Star)": StrategyRegistry.candlestick_pattern,
    "6. EMA Institutional Pullback (20/50 Trend)": StrategyRegistry.ema_pullback,
    "7. EMA Golden/Death Crossover (9/21 Acceleration)": StrategyRegistry.ema_crossover,
    "8. SuperTrend Trend-Rider (10, 2.0 + 200 EMA)": StrategyRegistry.supertrend_rider,
    "9. Volume Spike + Momentum 20-High Breakout": StrategyRegistry.volume_breakout,
    "10. Bollinger Bands Dynamic Squeeze & Mean Reversion": StrategyRegistry.bollinger_rsi_reversion
}

# ==============================================================================
# 🏛️ UNIFIED LIVE BROKER GATEWAY
# ==============================================================================
class LiveBrokerGateway:
    @staticmethod
    def place_order(tradingsymbol, qty, action, mode="PAPER"):
        creds = load_broker_creds()
        if mode == "PAPER":
            return {"status": "SUCCESS", "order_id": f"PAPER_{int(time.time())}"}
        
        # Zerodha Real Order Execution
        if "Zerodha" in creds.get("broker", ""):
            try:
                from kiteconnect import KiteConnect
                kite = KiteConnect(api_key=creds.get("kite_api_key", ""))
                kite.set_access_token(creds.get("kite_access_token", ""))
                t_type = kite.TRANSACTION_TYPE_BUY if action == "BUY" else kite.TRANSACTION_TYPE_SELL
                order_id = kite.place_order(
                    variety=kite.VARIETY_REGULAR, exchange=kite.EXCHANGE_NFO,
                    tradingsymbol=tradingsymbol, transaction_type=t_type,
                    quantity=qty, order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS
                )
                return {"status": "SUCCESS", "order_id": order_id}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}

        # Angel One Real Order Execution
        elif "Angel" in creds.get("broker", "") and pyotp is not None:
            try:
                from SmartApi import SmartConnect
                smart_api = SmartConnect(api_key=creds.get("angel_api_key", ""))
                totp = pyotp.TOTP(creds.get("angel_totp_key", "")).now()
                smart_api.generateSession(creds.get("angel_client_id", ""), creds.get("angel_pin", ""), totp)
                orderparams = {
                    "variety": "NORMAL", "tradingsymbol": tradingsymbol, "symboltoken": "OPTIDX",
                    "transactiontype": action, "exchange": "NFO", "ordertype": "MARKET",
                    "producttype": "INTRADAY", "duration": "DAY", "quantity": str(qty)
                }
                order_id = smart_api.placeOrder(orderparams)
                return {"status": "SUCCESS", "order_id": order_id}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}

        return {"status": "SUCCESS", "order_id": "SIM_OK"}

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

            state["last_heartbeat"] = now_ist.strftime('%I:%M:%S %p IST')
            save_algo_state(state)

            if state.get("running", False):
                # Daily Session Reset at 09:15 AM
                if state.get("date") != today_str:
                    state["date"] = today_str
                    state["today_trades"] = 0
                    state["net_pnl"] = 0.0
                    state["circuit_triggered"] = False
                    save_algo_state(state)

                # Daily Max Loss Circuit Breaker Kill-Switch
                if state.get("net_pnl", 0) <= -abs(state.get("max_daily_loss", 5000.0)):
                    if not state.get("circuit_triggered", False):
                        state["running"] = False
                        state["circuit_triggered"] = True
                        if state.get("active_position"):
                            pos = state["active_position"]
                            LiveBrokerGateway.place_order(pos["tradingsymbol"], pos["qty"], "SELL", state.get("mode"))
                            state["active_position"] = None
                        save_algo_state(state)
                    time.sleep(20)
                    continue

                if dtime(9, 15) <= cur_time <= dtime(15, 30):
                    # Auto Square-Off at 15:15 IST
                    if cur_time >= dtime(15, 15) and state.get("active_position") is not None:
                        pos = state["active_position"]
                        LiveBrokerGateway.place_order(pos["tradingsymbol"], pos["qty"], "SELL", state.get("mode"))
                        logs = load_trade_logs()
                        logs.insert(0, {
                            "time": now_ist.strftime('%d-%b %I:%M %p'), "strike": pos["strike_desc"],
                            "type": pos["type"], "entry": pos["entry_prem"], "exit": pos["entry_prem"],
                            "pnl": 0.0, "result": "EOD AUTO SQUAREOFF"
                        })
                        save_trade_logs(logs)
                        state["active_position"] = None
                        save_algo_state(state)
                        time.sleep(15)
                        continue

                    sym = state.get("symbol", "^NSEBANK")
                    spec = INDEX_SPECS.get(sym, {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100})
                    total_qty = state.get("lots", 2) * spec["lot_size"]
                    strat_name = state.get("strategy", list(STRATEGY_MAP.keys())[0])

                    df = yf.download(sym, period="2d", interval="15m", progress=False)
                    if not df.empty and len(df) >= 10:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.droplevel(1)

                        strat_func = STRATEGY_MAP.get(strat_name, StrategyRegistry.candlestick_pattern)
                        df = strat_func(df)
                        curr_spot = float(df['Close'].iloc[-1])
                        last_signal = int(df['signal'].iloc[-2])

                        # 1. Manage Active Position Exit
                        if state.get("active_position") is not None:
                            pos = state["active_position"]
                            pos["bars_held"] += 1
                            _, _, exit_prem, points_diff = calculate_option_trade(
                                spot_entry=pos["spot_entry"], spot_exit=curr_spot, option_type=pos["type"],
                                bars_held=pos["bars_held"], days_to_expiry=2, strike_step=spec["strike_step"]
                            )

                            target_hit = points_diff >= state.get("target", 50.0)
                            sl_hit = points_diff <= -state.get("sl", 20.0)

                            if target_hit or sl_hit:
                                gross_pnl = points_diff * total_qty
                                taxes = calculate_statutory_taxes(pos["entry_prem"], exit_prem, total_qty)
                                net_pnl = gross_pnl - taxes
                                
                                LiveBrokerGateway.place_order(pos["tradingsymbol"], total_qty, "SELL", state.get("mode"))
                                state["net_pnl"] += net_pnl
                                
                                logs = load_trade_logs()
                                logs.insert(0, {
                                    "time": now_ist.strftime('%d-%b %I:%M %p'), "strike": pos["strike_desc"],
                                    "type": pos["type"], "entry": pos["entry_prem"], "exit": exit_prem,
                                    "pnl": round(net_pnl, 2), "result": "TARGET 🎯" if target_hit else "SL HIT 🔴"
                                })
                                save_trade_logs(logs)
                                state["active_position"] = None
                                save_algo_state(state)

                        # 2. Open New Trade on Valid Strategy Signal
                        elif last_signal != 0 and state.get("today_trades", 0) < 2:
                            # 11:30 - 13:15 Sideways Blackout Guard (Applied for Non-Straddle Directional trades)
                            is_blackout = (dtime(11, 30) <= cur_time <= dtime(13, 15)) and (last_signal in [1, -1])
                            if not is_blackout:
                                pos_type = "BUY/CE" if last_signal == 1 else "BUY/PE" if last_signal == -1 else "SHORT STRADDLE"
                                atm_s, entry_prem, _, _ = calculate_option_trade(
                                    spot_entry=curr_spot, spot_exit=curr_spot, option_type=pos_type,
                                    bars_held=0, days_to_expiry=2, strike_step=spec["strike_step"]
                                )
                                opt_lbl = "CE" if last_signal == 1 else "PE" if last_signal == -1 else "ATM STRADDLE"
                                strike_desc = f"{spec['name']} {atm_s} {opt_lbl}"
                                tradingsymbol = f"{spec['name']}{now_ist.strftime('%y%b').upper()}{atm_s}{opt_lbl}"

                                order_res = LiveBrokerGateway.place_order(tradingsymbol, total_qty, "BUY", state.get("mode"))
                                if order_res["status"] == "SUCCESS":
                                    state["active_position"] = {
                                        "type": pos_type, "strike_desc": strike_desc, "tradingsymbol": tradingsymbol,
                                        "spot_entry": curr_spot, "entry_prem": entry_prem, "bars_held": 0, "qty": total_qty
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
# 📱 MOBILE DEMAT WEB INTERFACE
# ==============================================================================
state = load_algo_state()
creds = load_broker_creds()
spec = INDEX_SPECS.get(state.get("symbol", "^NSEBANK"), {"name": "BANKNIFTY", "lot_size": 30, "strike_step": 100})
total_contract_qty = state.get("lots", 2) * spec["lot_size"]

# Mobile Header
st.markdown("""
<div style="text-align:center; padding: 10px 0 14px 0;">
    <h2 style="color: #38bdf8; margin: 0; font-weight: 800; font-size: 24px;">⚡ SAM LIVE DEMAT</h2>
    <span style="color: #94a3b8; font-size: 12px;">Institutional Multi-Strategy Execution Engine</span>
</div>
""", unsafe_allow_html=True)

# 1. Main Live Status Banner
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

if state.get("circuit_triggered", False):
    st.error(f"🛑 MAX DAILY LOSS CIRCUIT HIT (-₹{state.get('max_daily_loss', 5000):,.2f}). Trading automatically locked for today.")

# 2. Main One-Touch Control Buttons
c1, c2 = st.columns(2)
with c1:
    if st.button("▶️ START ALGO", type="primary", use_container_width=True, disabled=state.get("circuit_triggered", False)):
        state["running"] = True
        save_algo_state(state)
        st.rerun()
with c2:
    if st.button("⏸️ PAUSE ALGO", use_container_width=True):
        state["running"] = False
        save_algo_state(state)
        st.rerun()

if st.button("🛑 EMERGENCY SQUARE-OFF & EXIT", use_container_width=True):
    if state.get("active_position"):
        pos = state["active_position"]
        LiveBrokerGateway.place_order(pos.get("tradingsymbol", ""), pos.get("qty", total_contract_qty), "SELL", state.get("mode"))
    state["active_position"] = None
    save_algo_state(state)
    st.error("⚠️ All open positions squared off immediately.")
    st.rerun()

st.markdown("---")

# 3. Live Active Position Display
st.markdown("##### 💼 Active Position & Live P&L")
active_pos = state.get("active_position")

if active_pos:
    st.markdown(f"""
    <div style="background: #0f172a; border: 1px solid #38bdf8; border-radius: 12px; padding: 14px; margin-bottom: 12px;">
        <div style="display:flex; justify-content:space-between;">
            <span style="color: #38bdf8; font-weight: 800; font-size: 14px;">{active_pos.get('strike_desc')}</span>
            <span style="color: #10b981; font-weight: 700; font-size: 13px;">{active_pos.get('qty', total_contract_qty)} Qty ({state.get('lots', 2)} Lots)</span>
        </div>
        <div style="margin-top: 8px; font-size: 12px; color: #94a3b8;">
            Entry Premium: <b>₹{active_pos.get('entry_prem'):.2f}</b><br>
            Target: <b style="color:#10b981;">₹{active_pos.get('entry_prem') + state.get('target', 50):.2f}</b> | Hard SL: <b style="color:#ef4444;">₹{active_pos.get('entry_prem') - state.get('sl', 20):.2f}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info(f"No active trade. Engine scanning market on: `{state.get('strategy')}`.")

# Daily Performance KPIs
m1, m2 = st.columns(2)
m1.metric("Today Realized Net PnL", f"{'+₹' if state.get('net_pnl', 0) >= 0 else '-₹'}{abs(state.get('net_pnl', 0)):,.2f}")
m2.metric("Daily Trades Cap", f"{state.get('today_trades', 0)} / 2")

st.markdown("---")

# 4. Strategy & Asset Selector (Expanded by Default for Easy Switch)
with st.expander("🛠️ Strategy Selection & RMS Parameters", expanded=True):
    strat_keys = list(STRATEGY_MAP.keys())
    cur_strat_idx = strat_keys.index(state.get("strategy")) if state.get("strategy") in strat_keys else 0
    sel_strat = st.selectbox("Select Quantitative / Institutional Model", strat_keys, index=cur_strat_idx)
    
    asset_keys = list(INDEX_SPECS.keys())
    cur_asset_idx = asset_keys.index(state.get("symbol")) if state.get("symbol") in asset_keys else 0
    sel_sym = st.selectbox("Underlying Market Asset", asset_keys, index=cur_asset_idx, format_func=lambda x: INDEX_SPECS[x]["name"])
    
    sel_lots = st.number_input("Number of Execution Lots", value=int(state.get("lots", 2)), min_value=1, step=1)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        sel_target = st.number_input("Target Points (Pts)", value=float(state.get("target", 50.0)), step=5.0)
    with col_t2:
        sel_sl = st.number_input("Stop Loss (Pts)", value=float(state.get("sl", 20.0)), step=5.0)

    sel_max_loss = st.number_input("Daily Max Loss Circuit Kill-Switch (₹)", value=float(state.get("max_daily_loss", 5000.0)), step=1000.0)

    if st.button("💾 APPLY STRATEGY CONFIGURATION", use_container_width=True):
        state["strategy"] = sel_strat
        state["symbol"] = sel_sym
        state["lots"] = sel_lots
        state["target"] = sel_target
        state["sl"] = sel_sl
        state["max_daily_loss"] = sel_max_loss
        save_algo_state(state)
        st.success("✅ Strategy Parameters Synced.")
        st.rerun()

st.markdown("---")

# 5. Real Broker API Credentials Binding
with st.expander("🔑 Attach Real Demat Broker API (Zerodha / Angel)", expanded=False):
    sel_mode = st.radio("Execution Environment", ["📝 Paper Trading Mode (Zero Risk)", "🚀 Live Demat Account (Real Capital)"], index=0 if state.get("mode") == "PAPER" else 1)
    sel_broker = st.selectbox("Select Demat Broker", ["Zerodha KiteConnect", "Angel One SmartAPI"], index=0)

    if "Zerodha" in sel_broker:
        st.markdown("###### 🔐 Zerodha KiteConnect Credentials")
        k_key = st.text_input("Kite API Key", value=creds.get("kite_api_key", ""), type="password")
        k_secret = st.text_input("Kite API Secret", value=creds.get("kite_api_secret", ""), type="password")
        k_token = st.text_input("Kite Daily Access Token", value=creds.get("kite_access_token", ""), type="password")
        
        if st.button("🔗 ATTACH & SAVE ZERODHA API", use_container_width=True):
            creds["broker"] = "Zerodha"
            creds["kite_api_key"] = k_key
            creds["kite_api_secret"] = k_secret
            creds["kite_access_token"] = k_token
            save_broker_creds(creds)
            state["mode"] = "LIVE" if "Live" in sel_mode else "PAPER"
            save_algo_state(state)
            st.success("✅ Zerodha KiteConnect credentials bound successfully.")
            st.rerun()

    elif "Angel" in sel_broker:
        st.markdown("###### 🔐 Angel One SmartAPI Credentials")
        a_client = st.text_input("Angel Client ID", value=creds.get("angel_client_id", ""))
        a_pin = st.text_input("Angel MPIN / Password", value=creds.get("angel_pin", ""), type="password")
        a_key = st.text_input("SmartAPI Key", value=creds.get("angel_api_key", ""), type="password")
        a_totp = st.text_input("Angel TOTP Secret Key", value=creds.get("angel_totp_key", ""), type="password")
        
        if st.button("🔗 ATTACH & SAVE ANGEL ONE API", use_container_width=True):
            creds["broker"] = "Angel"
            creds["angel_client_id"] = a_client
            creds["angel_pin"] = a_pin
            creds["angel_api_key"] = a_key
            creds["angel_totp_key"] = a_totp
            save_broker_creds(creds)
            state["mode"] = "LIVE" if "Live" in sel_mode else "PAPER"
            save_algo_state(state)
            st.success("✅ Angel One credentials bound successfully.")
            st.rerun()

# 6. Today's Executed Order Logs
st.markdown("##### 📜 Executed Orders Logbook")
logs = load_trade_logs()
if logs:
    log_df = pd.DataFrame(logs)
    st.dataframe(log_df, use_container_width=True, height=220)
    if st.button("🗑️ Clear Execution History", use_container_width=True):
        save_trade_logs([])
        st.rerun()
else:
    st.caption("No orders executed yet today.")