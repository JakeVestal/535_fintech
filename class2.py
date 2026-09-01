import math
from datetime import datetime
import lseg.data as ld
import numpy as np
import pandas as pd

ld.open_session()

# Target Parameters
trade_date = "2026-08-17"
expiry_str = "21AUG26"
expiry_dt = datetime.strptime(expiry_str, "%d%b%y")

stock_ric = "UUUU.K"
root_symbol = "UUUU"
strike_step = 0.5
min_delta = 0.15

CALL_MONTH_CODES = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E",
    6: "F",
    7: "G",
    8: "H",
    9: "I",
    10: "J",
    11: "K",
    12: "L",
}
month_code = CALL_MONTH_CODES[expiry_dt.month]
day_str = f"{expiry_dt.day:02d}"
year_str = f"{expiry_dt.year % 100:02d}"

# 1. Pull Stock Bars
stock_prices = ld.get_history(
    universe=[stock_ric],
    fields=["TRDPRC_1", "ACVOL_1"],
    start=f"{trade_date}T13:30:00Z",
    end=f"{trade_date}T20:00:00Z",
    interval="1min",
)

stock_prices = stock_prices.dropna(how="all").reset_index()
stock_prices.rename(
    columns={"Date": "Timestamp", "TRDPRC_1": "Price", "ACVOL_1": "Volume"},
    inplace=True,
)

daily_low = stock_prices["Price"].min()
daily_high = stock_prices["Price"].max()
max_allowed_strike = daily_high * 1.50

current_strike = math.ceil(daily_low / strike_step) * strike_step
all_prices = []

# 2. Loop through option strikes
while True:
  if current_strike > max_allowed_strike:
    print(
        f"\nERROR: Safety limit triggered at strike ${current_strike:.2f}."
        " Aborting."
    )
    break

  # Standard 8-digit OPRA strike padding (e.g., 14.50 -> 00014500)
  strike_formatted = f"{int(round(current_strike * 1000)):08d}"

  # For TS.Intraday (1min bars), use the BASE OPRA RIC WITHOUT the ^ suffix
  option_ric = (
      f"{root_symbol}{month_code}{day_str}{year_str}{strike_formatted}.U"
  )

  print(f"Querying Intraday RIC: {option_ric} (Strike: ${current_strike:.2f})")

  try:
    # Query intraday tick/bar pricing fields
    opt_df = ld.get_history(
        universe=[option_ric],
        fields=["BID", "ASK", "MID_PRICE"],
        start=trade_date,
        end=trade_date,
        interval="daily"
    )

    if opt_df is not None and not opt_df.empty:
      opt_df = opt_df.dropna(how="all")
      if not opt_df.empty:
        opt_df = opt_df.reset_index()
        opt_df.rename(
            columns={
                "Date": "Timestamp",
                "BID": "Bid",
                "ASK": "Ask",
                "MID_PRICE": "Mid",
            },
            inplace=True,
        )
        opt_df["RIC"] = option_ric
        opt_df["Delta"] = np.nan

        opt_df = opt_df[["Timestamp", "RIC", "Bid", "Ask", "Mid", "Delta"]]
        all_prices.append(opt_df)
        print(f" -> Success: Fetched {len(opt_df)} intraday rows.")

        if opt_df["Mid"].max() < 0.05:
          print(f"Stopping loop: Mid price fell below $0.05.")
          break
  except Exception as e:
    print(f" -> Failed to fetch {option_ric}: {e}")

  current_strike += strike_step

if all_prices:
  options_prices = pd.concat(all_prices, ignore_index=True)
else:
  options_prices = pd.DataFrame(
      columns=["Timestamp", "RIC", "Bid", "Ask", "Mid", "Delta"]
  )

print("\n--- Final Intraday Options DataFrame ---")
print(options_prices.head())