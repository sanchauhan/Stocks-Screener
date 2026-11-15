from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
import yfinance as yf

DEFAULT_TICKERS = [
    "ABB.NS", "ACC.NS", "AUBANK.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS",
    "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS",
    "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS",
    "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS",
    "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS",
    "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS",
    "CANFINHOME.NS", "CANBK.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS",
    "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS",
    "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS",
    "DEEPAKNITR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS",
    "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS",
    "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS",
    "HAVELLS.NS", "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", "IDFCFIRSTB.NS",
    "IDFC.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS",
    "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS",
    "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS",
    "JSWSTEEL.NS", "JUBLFOOD.NS", "KFINTECH.NS", "KOTAKBANK.NS", "L&TFH.NS",
    "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS",
    "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS",
    "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS",
    "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS",
    "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "OFSS.NS", "ONGC.NS",
    "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS",
    "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS",
    "PVRINOX.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RELIANCE.NS", "SAIL.NS",
    "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SHRIRAMFIN.NS",
    "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS",
    "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS",
    "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS",
    "TORNTPOWER.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS",
    "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS",
]

def get_stock_data(ticker, period="6mo", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        return None if df.empty else df
    except Exception:
        return None

def get_cpr_details(df_resampled):
    if len(df_resampled) < 2:
        return None, None, "N/A"
    prev_session = df_resampled.iloc[-2]
    h, l, c = float(prev_session["High"]), float(prev_session["Low"]), float(prev_session["Close"])
    p = (h + l + c) / 3
    bc = (h + l) / 2
    tc = (p - bc) + p
    return max(tc, bc, p), p, f"P:{round(p, 1)} [BC:{round(bc, 1)}-TC:{round(tc, 1)}]"

@st.cache_data(ttl=25)
def screen_stocks_live(tickers, min_price=None, max_price=None, min_volume=None):
    if not tickers:
        return pd.DataFrame()

    results = []
    try:
        bulk_df = yf.download(tickers, period="6mo", group_by="ticker", progress=False)
        for t in tickers:
            try:
                df = bulk_df[t] if len(tickers) > 1 else bulk_df
                df = df.dropna(subset=["Close"])
                if len(df) < 5:
                    continue

                latest_price = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2])
                price_change_pct = ((latest_price - prev_close) / prev_close) * 100
                latest_volume = float(df["Volume"].iloc[-1])

                if not ((min_price is None or latest_price >= min_price) and
                        (max_price is None or latest_price <= max_price) and
                        (min_volume is None or latest_volume >= min_volume)):
                    continue

                daily_high, daily_low = float(df["High"].iloc[-2]), float(df["Low"].iloc[-2])
                d_p = (daily_high + daily_low + prev_close) / 3
                d_bc = (daily_high + daily_low) / 2
                d_tc = (d_p - d_bc) + d_p
                daily_top = max(d_tc, d_bc, d_p)
                daily_cpr_str = f"P:{round(d_p, 1)} [BC:{round(d_bc, 1)}-TC:{round(d_tc, 1)}]"

                df_weekly = df.resample("W").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"})
                weekly_top, _, weekly_cpr_str = get_cpr_details(df_weekly)

                df_monthly = df.resample("ME").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"})
                monthly_top, _, monthly_cpr_str = get_cpr_details(df_monthly)

                result_signal, trend_status = "HOLD ⏳", "Sideways ➡️"
                is_above_daily = latest_price > daily_top
                is_above_weekly = (weekly_top is not None) and (latest_price > weekly_top)
                is_above_monthly = (monthly_top is not None) and (latest_price > monthly_top)

                if is_above_daily and is_above_weekly and is_above_monthly:
                    result_signal, trend_status = "Strong Buy 🔥", "Super Bullish 🚀"
                elif is_above_weekly and is_above_monthly:
                    result_signal, trend_status = "mod Buy 📈", "Macro Bullish 🛰️"
                elif is_above_daily:
                    result_signal, trend_status = "Buy 👍", "Intraday Bullish ⚡"
                elif latest_price < daily_top and (weekly_top is not None and latest_price < weekly_top):
                    trend_status = "Bearish 📉"

                results.append({
                    "Ticker": t,
                    "Live Price (₹)": round(latest_price, 2),
                    "Change (%)": round(price_change_pct, 2),
                    "Volume": int(latest_volume),
                    "Daily CPR": daily_cpr_str,
                    "Weekly CPR": weekly_cpr_str,
                    "Monthly CPR": monthly_cpr_str,
                    "Trend": trend_status,
                    "Result": result_signal,
                })
            except Exception:
                continue
    except Exception as e:
        st.error(f"Data fetch error: {e}")

    return pd.DataFrame(results)
st.set_page_config(page_title="Live Stock CPR Screener", layout="wide")
st.title("📈 Live Stock CPR Matrix & Screener")

st.sidebar.header("⚡ Live Auto-Refresh Settings")
auto_refresh = st.sidebar.toggle("Enable Live Auto-Refresh", value=True)
refresh_interval = st.sidebar.selectbox(
    "Refresh Interval (Seconds):",
    options=(30, 60, 120, 300),
    index=0,
    disabled=not auto_refresh,
)

if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.header("Filter Panels")
tickers_input = st.sidebar.text_area("Symbols list:", value=",".join(DEFAULT_TICKERS), height=100)
min_price = st.sidebar.number_input("Min Price", min_value=0.0, value=100.0)
max_price = st.sidebar.number_input("Max Price", min_value=0.0, value=15000.0)
min_volume = st.sidebar.number_input("Min Volume", min_value=0, value=50000)

filter_mode = st.sidebar.selectbox(
    "Filter by Signals:",
    ("All Actions", "Strong Buy Only", "Strong / Mod / Buy", "HOLD Only"),
)

tickers_list = list(set([t.strip().upper() for t in tickers_input.split(",") if t.strip()]))
run_every_sec = refresh_interval if auto_refresh else None

@st.fragment(run_every=run_every_sec)
def render_live_screener():
    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist).strftime("%I:%M:%S %p IST")

    col_head, col_time = st.columns((3, 1))
    with col_head:
        st.subheader("CPR Screener Live Analytics Board")
    with col_time:
        status_badge = "🟢 LIVE" if auto_refresh else "⏸️ PAUSED"
        st.markdown(f"**Status:** {status_badge} | **Updated:** `{current_time}`")

    screener_df = screen_stocks_live(tickers_list, min_price, max_price, min_volume)

    if not screener_df.empty:
        if filter_mode == "Strong Buy Only":
            rendered_df = screener_df[screener_df["Result"] == "Strong Buy 🔥"]
        elif filter_mode == "Strong / Mod / Buy":
            rendered_df = screener_df[screener_df["Result"].isin(["Strong Buy 🔥", "mod Buy 📈", "Buy 👍"])]
        elif filter_mode == "HOLD Only":
            rendered_df = screener_df[screener_df["Result"] == "HOLD ⏳"]
        else:
            rendered_df = screener_df

        if not rendered_df.empty:
            st.dataframe(rendered_df.sort_values(by="Volume", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Selected actions match karne wale tickers abhi available nahi hain.")
    else:
        st.info("No records found.")

render_live_screener()

st.markdown("---")
st.subheader("Technical Candle Profile Viewer")

col1, col2, col3, col4 = st.columns(4)
with col1:
    selected_ticker = st.selectbox("Select chart view focus:", tickers_list)
with col2:
    period = st.selectbox("Timeline Range", ("1mo", "3mo", "6mo", "1y", "2y"), index=2)
with col3:
    interval = st.selectbox("Bar Type", ("1d", "15m", "5m", "1wk", "1mo"), index=0)
with col4:
    show_cpr_lines = st.checkbox("Overlay Daily CPR layers", value=True)

if selected_ticker:
    df_chart = get_stock_data(selected_ticker, period=period, interval=interval)

    if df_chart is not None and len(df_chart) > 1:
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df_chart.index,
                open=df_chart["Open"],
                high=df_chart["High"],
                low=df_chart["Low"],
                close=df_chart["Close"],
                name=selected_ticker,
            )
        )

        if show_cpr_lines and interval == "1d":
            df_chart["Prev_High"] = df_chart["High"].shift(1)
            df_chart["Prev_Low"] = df_chart["Low"].shift(1)
            df_chart["Prev_Close"] = df_chart["Close"].shift(1)
            df_chart["P"] = (df_chart["Prev_High"] + df_chart["Prev_Low"] + df_chart["Prev_Close"]) / 3
            df_chart["BC"] = (df_chart["Prev_High"] + df_chart["Prev_Low"]) / 2
            df_chart["TC"] = (df_chart["P"] - df_chart["BC"]) + df_chart["P"]

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["P"], mode="lines", name="Daily Pivot", line=dict(color="blue", width=1.5)))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["TC"], mode="lines", name="Daily TC", line=dict(color="cyan", width=1, dash="dash")))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["BC"], mode="lines", name="Daily BC", line=dict(color="cyan", width=1, dash="dash")))

        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=550)
        st.plotly_chart(fig, use_container_width=True)
