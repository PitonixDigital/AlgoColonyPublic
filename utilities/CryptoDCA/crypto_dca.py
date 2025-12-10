from binance.client import Client
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Binance public client (no API key needed for market data)
client = Client("", "")

# === User Inputs ===
symbols_input = input("Enter trading pairs separated by commas (e.g., BTCUSDT, SOLUSDT, LUNCUSDT, XRPUSDT): ")
symbols = [s.strip().upper() for s in symbols_input.split(",")]

start_date = input("Enter the start date (e.g., 1 Jan, 2023): ")
monthly_investment = float(input("Monthly investment amount per asset (e.g., 20): "))

# Interval: 1-month candles
interval = Client.KLINE_INTERVAL_1MONTH

# Prepare plot
plt.figure(figsize=(12, 7))

print("\n====================================================")
print("               Fetching & Calculating DCA")
print("====================================================\n")

# Store results for summary
results = {}

# Determine the timeline based on the first valid symbol
timeline_dates = []

for symbol in symbols:
    try:
        klines = client.get_historical_klines(symbol, interval, start_date)
    except:
        continue
    if not klines:
        continue
    timeline_dates = [pd.to_datetime(k[6], unit="ms") for k in klines]
    break  # only need the first valid timeline

# Baseline: total invested over time
invested_baseline = [(i + 1) * monthly_investment for i in range(len(timeline_dates))]

# Process each symbol
for symbol in symbols:
    print(f"\nFetching historical data for {symbol}...\n")
    try:
        klines = client.get_historical_klines(symbol, interval, start_date)
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        continue

    if not klines:
        print(f"No data for {symbol}. Skipping.")
        continue

    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["date"] = pd.to_datetime(df["close_time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df = df[["date", "close"]]

    total_tokens = 0
    total_invested = 0
    portfolio_values = []

    for i, row in enumerate(df.itertuples()):
        price = row.close
        total_tokens += monthly_investment / price
        total_invested += monthly_investment
        portfolio_values.append(total_tokens * price)
        print(f"{symbol} | {row.date.date()} - Bought {monthly_investment/price:.4f} @ ${price:.6f}")

    # Current price
    ticker = client.get_symbol_ticker(symbol=symbol)
    current_price = float(ticker["price"])
    current_value = total_tokens * current_price
    profit_loss = current_value - total_invested
    roi = (profit_loss / total_invested) * 100

    results[symbol] = {
        "invested": total_invested,
        "tokens": total_tokens,
        "current_price": current_price,
        "value": current_value,
        "pnl": profit_loss,
        "roi": roi,
        "dates": df["date"],
        "portfolio_values": portfolio_values
    }

    # Plot portfolio value
    plt.plot(df["date"], portfolio_values, label=f"{symbol} Portfolio Value")

# Plot the baseline invested line
plt.plot(timeline_dates, invested_baseline, label="Total Invested (Baseline)", linestyle="--", color="black")

# Finalize plot
plt.title("DCA Growth Curve for Multiple Assets with Invested Baseline")
plt.xlabel("Date")
plt.ylabel("USD Value")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ======================= SUMMARY ==========================
print("\n====================================================")
print("                     DCA RESULTS")
print("====================================================\n")

for symbol, r in results.items():
    print(f"\n===== {symbol} =====")
    print(f"Total invested:          ${r['invested']:.2f}")
    print(f"Total tokens acquired:    {r['tokens']:.6f}")
    print(f"Current price:           ${r['current_price']:.6f}")
    print(f"Portfolio value today:   ${r['value']:.2f}")
    print(f"Net profit/loss:         ${r['pnl']:.2f}")
    print(f"ROI:                      {r['roi']:.2f}%")
