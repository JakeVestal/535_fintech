window.HELIOS_BOOK = {
  "underlying": "AAPL",
  "startCash": 25000,
  "initPct": 0.5,
  "maintPct": 0.25,
  "blotter": [
    {
      "id": "t1",
      "ts": "2026-06-01 09:30",
      "side": "BUY",
      "qty": 100,
      "instrument": "AAPL",
      "asset": "STK",
      "strike": null,
      "expiry": null,
      "price": 188.4,
      "multiplier": 1,
      "notes": "Combo stock leg. Limit at the open print. 100 shares. Decrease cash."
    },
    {
      "id": "t2",
      "ts": "2026-06-01 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 6/5 190.0 C",
      "asset": "CALL",
      "strike": 190.0,
      "expiry": "2026-06-05",
      "price": 1.82,
      "multiplier": 100,
      "notes": "Friday weekly, nearest OTM. Limit = option mid. Increase cash by 100\u00d7mid."
    },
    {
      "id": "t3",
      "ts": "2026-06-05 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 6/5 190.0 C",
      "asset": "CALL",
      "strike": 190.0,
      "expiry": "2026-06-05",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM. Keep shares, keep premium. Next Monday write the next call."
    },
    {
      "id": "t4",
      "ts": "2026-06-08 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 6/12 192.5 C",
      "asset": "CALL",
      "strike": 192.5,
      "expiry": "2026-06-12",
      "price": 1.64,
      "multiplier": 100,
      "notes": "Still long stock. Write next Friday weekly. Limit at mid."
    },
    {
      "id": "t5",
      "ts": "2026-06-12 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 6/12 192.5 C",
      "asset": "CALL",
      "strike": 192.5,
      "expiry": "2026-06-12",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t6",
      "ts": "2026-06-15 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 6/19 190.0 C",
      "asset": "CALL",
      "strike": 190.0,
      "expiry": "2026-06-19",
      "price": 1.91,
      "multiplier": 100,
      "notes": "Spot dipped; ATM-ish 190s. Limit at mid."
    },
    {
      "id": "t7",
      "ts": "2026-06-19 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 6/19 190.0 C",
      "asset": "CALL",
      "strike": 190.0,
      "expiry": "2026-06-19",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t8",
      "ts": "2026-06-22 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 6/26 195.0 C",
      "asset": "CALL",
      "strike": 195.0,
      "expiry": "2026-06-26",
      "price": 1.55,
      "multiplier": 100,
      "notes": "Spot 192.4 \u2192 write 195s."
    },
    {
      "id": "t9",
      "ts": "2026-06-26 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 6/26 195.0 C",
      "asset": "CALL",
      "strike": 195.0,
      "expiry": "2026-06-26",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t10",
      "ts": "2026-06-29 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/3 197.5 C",
      "asset": "CALL",
      "strike": 197.5,
      "expiry": "2026-07-03",
      "price": 1.48,
      "multiplier": 100,
      "notes": "Monday rewrite."
    },
    {
      "id": "t11",
      "ts": "2026-07-03 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/3 197.5 C",
      "asset": "CALL",
      "strike": 197.5,
      "expiry": "2026-07-03",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t12",
      "ts": "2026-07-06 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/10 195.0 C",
      "asset": "CALL",
      "strike": 195.0,
      "expiry": "2026-07-10",
      "price": 1.72,
      "multiplier": 100,
      "notes": "Rewrite 195s."
    },
    {
      "id": "t13",
      "ts": "2026-07-10 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/10 195.0 C",
      "asset": "CALL",
      "strike": 195.0,
      "expiry": "2026-07-10",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t14",
      "ts": "2026-07-13 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/17 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-17",
      "price": 1.38,
      "multiplier": 100,
      "notes": "Spot 198.6, write 200s."
    },
    {
      "id": "t15",
      "ts": "2026-07-17 16:00",
      "side": "ASSIGN",
      "qty": 1,
      "instrument": "AAPL 7/17 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-17",
      "price": 0,
      "multiplier": 100,
      "notes": "ITM at expiry. Assigned the short call against the long stock."
    },
    {
      "id": "t16",
      "ts": "2026-07-17 16:00",
      "side": "SELL",
      "qty": 100,
      "instrument": "AAPL",
      "asset": "STK",
      "strike": null,
      "expiry": null,
      "price": 200.0,
      "multiplier": 1,
      "notes": "Deliver 100 shares at strike. Increase cash 100\u00d7200. Now flat."
    },
    {
      "id": "t17",
      "ts": "2026-07-20 09:30",
      "side": "BUY",
      "qty": 100,
      "instrument": "AAPL",
      "asset": "STK",
      "strike": null,
      "expiry": null,
      "price": 201.2,
      "multiplier": 1,
      "notes": "Flat after assignment. Combo stock leg. Decrease cash."
    },
    {
      "id": "t18",
      "ts": "2026-07-20 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "price": 1.41,
      "multiplier": 100,
      "notes": "Combo call leg. Next Friday weekly. Limit at mid."
    },
    {
      "id": "t19",
      "ts": "2026-07-24 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t20",
      "ts": "2026-07-27 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-31",
      "price": 1.66,
      "multiplier": 100,
      "notes": "Still long. Monday rewrite."
    },
    {
      "id": "t21",
      "ts": "2026-07-31 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-31",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire."
    },
    {
      "id": "t22",
      "ts": "2026-08-03 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 8/7 205.0 C",
      "asset": "CALL",
      "strike": 205.0,
      "expiry": "2026-08-07",
      "price": 1.52,
      "multiplier": 100,
      "notes": "Spot 204.1, write 205s."
    },
    {
      "id": "t23",
      "ts": "2026-08-07 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 8/7 205.0 C",
      "asset": "CALL",
      "strike": 205.0,
      "expiry": "2026-08-07",
      "price": 0,
      "multiplier": 100,
      "notes": "OTM expire. Sample window ends."
    }
  ],
  "ledger": [
    {
      "date": "2026-06-01",
      "cash": 6342.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "6/5 190C",
      "stockPx": 188.4,
      "optPx": 1.82,
      "lmv": 18840.0,
      "optMv": -182.0,
      "nav": 25000.0,
      "init": 9420.0,
      "maint": 4710.0,
      "available": 15580.0,
      "excess": 20290.0
    },
    {
      "date": "2026-06-05",
      "cash": 6342.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 187.2,
      "optPx": 0.0,
      "lmv": 18720.0,
      "optMv": 0.0,
      "nav": 25062.0,
      "init": 9360.0,
      "maint": 4680.0,
      "available": 15702.0,
      "excess": 20382.0
    },
    {
      "date": "2026-06-08",
      "cash": 6506.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "6/12 192.5C",
      "stockPx": 190.1,
      "optPx": 1.64,
      "lmv": 19010.0,
      "optMv": -164.0,
      "nav": 25352.0,
      "init": 9505.0,
      "maint": 4752.5,
      "available": 15847.0,
      "excess": 20599.5
    },
    {
      "date": "2026-06-12",
      "cash": 6506.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 189.55,
      "optPx": 0.0,
      "lmv": 18955.0,
      "optMv": 0.0,
      "nav": 25461.0,
      "init": 9477.5,
      "maint": 4738.75,
      "available": 15983.5,
      "excess": 20722.25
    },
    {
      "date": "2026-06-15",
      "cash": 6697.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "6/19 190C",
      "stockPx": 187.8,
      "optPx": 1.91,
      "lmv": 18780.0,
      "optMv": -191.0,
      "nav": 25286.0,
      "init": 9390.0,
      "maint": 4695.0,
      "available": 15896.0,
      "excess": 20591.0
    },
    {
      "date": "2026-06-19",
      "cash": 6697.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 188.9,
      "optPx": 0.0,
      "lmv": 18890.0,
      "optMv": 0.0,
      "nav": 25587.0,
      "init": 9445.0,
      "maint": 4722.5,
      "available": 16142.0,
      "excess": 20864.5
    },
    {
      "date": "2026-06-22",
      "cash": 6852.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "6/26 195C",
      "stockPx": 192.4,
      "optPx": 1.55,
      "lmv": 19240.0,
      "optMv": -155.0,
      "nav": 25937.0,
      "init": 9620.0,
      "maint": 4810.0,
      "available": 16317.0,
      "excess": 21127.0
    },
    {
      "date": "2026-06-26",
      "cash": 6852.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 193.1,
      "optPx": 0.0,
      "lmv": 19310.0,
      "optMv": 0.0,
      "nav": 26162.0,
      "init": 9655.0,
      "maint": 4827.5,
      "available": 16507.0,
      "excess": 21334.5
    },
    {
      "date": "2026-06-29",
      "cash": 7000.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/3 197.5C",
      "stockPx": 195.2,
      "optPx": 1.48,
      "lmv": 19520.0,
      "optMv": -148.0,
      "nav": 26372.0,
      "init": 9760.0,
      "maint": 4880.0,
      "available": 16612.0,
      "excess": 21492.0
    },
    {
      "date": "2026-07-03",
      "cash": 7000.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 194.05,
      "optPx": 0.0,
      "lmv": 19405.0,
      "optMv": 0.0,
      "nav": 26405.0,
      "init": 9702.5,
      "maint": 4851.25,
      "available": 16702.5,
      "excess": 21553.75
    },
    {
      "date": "2026-07-06",
      "cash": 7172.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/10 195C",
      "stockPx": 193.5,
      "optPx": 1.72,
      "lmv": 19350.0,
      "optMv": -172.0,
      "nav": 26350.0,
      "init": 9675.0,
      "maint": 4837.5,
      "available": 16675.0,
      "excess": 21512.5
    },
    {
      "date": "2026-07-10",
      "cash": 7172.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 194.8,
      "optPx": 0.0,
      "lmv": 19480.0,
      "optMv": 0.0,
      "nav": 26652.0,
      "init": 9740.0,
      "maint": 4870.0,
      "available": 16912.0,
      "excess": 21782.0
    },
    {
      "date": "2026-07-13",
      "cash": 7310.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/17 200C",
      "stockPx": 198.6,
      "optPx": 1.38,
      "lmv": 19860.0,
      "optMv": -138.0,
      "nav": 27032.0,
      "init": 9930.0,
      "maint": 4965.0,
      "available": 17102.0,
      "excess": 22067.0
    },
    {
      "date": "2026-07-17",
      "cash": 27310.0,
      "shares": 0,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 201.2,
      "optPx": 0.0,
      "lmv": 0.0,
      "optMv": 0.0,
      "nav": 27310.0,
      "init": 0.0,
      "maint": 0.0,
      "available": 27310.0,
      "excess": 27310.0
    },
    {
      "date": "2026-07-20",
      "cash": 7331.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/24 202.5C",
      "stockPx": 201.2,
      "optPx": 1.41,
      "lmv": 20120.0,
      "optMv": -141.0,
      "nav": 27310.0,
      "init": 10060.0,
      "maint": 5030.0,
      "available": 17250.0,
      "excess": 22280.0
    },
    {
      "date": "2026-07-24",
      "cash": 7331.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 199.8,
      "optPx": 0.0,
      "lmv": 19980.0,
      "optMv": 0.0,
      "nav": 27311.0,
      "init": 9990.0,
      "maint": 4995.0,
      "available": 17321.0,
      "excess": 22316.0
    },
    {
      "date": "2026-07-27",
      "cash": 7497.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/31 200C",
      "stockPx": 199.4,
      "optPx": 1.66,
      "lmv": 19940.0,
      "optMv": -166.0,
      "nav": 27271.0,
      "init": 9970.0,
      "maint": 4985.0,
      "available": 17301.0,
      "excess": 22286.0
    },
    {
      "date": "2026-07-31",
      "cash": 7497.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 198.75,
      "optPx": 0.0,
      "lmv": 19875.0,
      "optMv": 0.0,
      "nav": 27372.0,
      "init": 9937.5,
      "maint": 4968.75,
      "available": 17434.5,
      "excess": 22403.25
    },
    {
      "date": "2026-08-03",
      "cash": 7649.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "8/7 205C",
      "stockPx": 204.1,
      "optPx": 1.52,
      "lmv": 20410.0,
      "optMv": -152.0,
      "nav": 27907.0,
      "init": 10205.0,
      "maint": 5102.5,
      "available": 17702.0,
      "excess": 22804.5
    },
    {
      "date": "2026-08-07",
      "cash": 7649.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 203.4,
      "optPx": 0.0,
      "lmv": 20340.0,
      "optMv": 0.0,
      "nav": 27989.0,
      "init": 10170.0,
      "maint": 5085.0,
      "available": 17819.0,
      "excess": 22904.0
    }
  ],
  "writeup": {
    "title": "Worked example \u2014 AAPL Friday weeklies (wait through expiry)",
    "fill": "Illustrative book, not a live LSEG pull. Limit at mid = (BID+ASK)/2. Stock at the 09:30 print. No bid/ask \u2192 skip. TRDPRC_1 is for the scatter only, not the fill.",
    "roll": "No roll. Exit is wait until Friday 16:00. OTM: expire, keep shares, next Monday write the next weekly. ITM: assigned \u2014 you own stock, you are assigned a short, you are flat. Next Monday start the combo again (buy 100 + write the new Friday call).",
    "pin": "We do not BTC. Assignment is the ITM exit. Pin is accepted; the blotter shows ASSIGN + deliver shares at strike.",
    "regT": "Covered call: long 100 AAPL, short 1 call. Initial = 50% of stock LMV. Maintenance = 25% of LMV. Covered short call adds $0. NAV = cash + stock MV + option MV (short option negative). Available = NAV \u2212 initial. Excess = NAV \u2212 maintenance. After assignment LMV is 0 until the next Monday buy."
  },
  "rics": [
    {
      "label": "AAPL 6/5 190 C (expired)",
      "ric": "AAPLF52619000.U^F26"
    },
    {
      "label": "AAPL 7/17 200 C (expired)",
      "ric": "AAPLG172620000.U^G26"
    },
    {
      "label": "AAPL 8/7 205 C (expired)",
      "ric": "AAPLH72620500.U^H26"
    }
  ],
  "midVsTrade": {
    "points": [
      {
        "mid": 0.841,
        "trade": 0.796
      },
      {
        "mid": 1.29,
        "trade": 1.043
      },
      {
        "mid": 1.284,
        "trade": 1.364
      },
      {
        "mid": 1.108,
        "trade": 0.956
      },
      {
        "mid": 1.476,
        "trade": 1.568
      },
      {
        "mid": 1.077,
        "trade": 1.877
      },
      {
        "mid": 3.761,
        "trade": 3.62
      },
      {
        "mid": 1.985,
        "trade": 2.332
      },
      {
        "mid": 0.12,
        "trade": 0.05
      },
      {
        "mid": 1.494,
        "trade": 1.27
      },
      {
        "mid": 0.941,
        "trade": 0.81
      },
      {
        "mid": 3.01,
        "trade": 2.31
      },
      {
        "mid": 1.28,
        "trade": 1.158
      },
      {
        "mid": 0.12,
        "trade": 0.05
      },
      {
        "mid": 1.27,
        "trade": 1.311
      },
      {
        "mid": 2.108,
        "trade": 1.408
      },
      {
        "mid": 2.438,
        "trade": 1.738
      },
      {
        "mid": 2.401,
        "trade": 2.698
      },
      {
        "mid": 2.645,
        "trade": 2.511
      },
      {
        "mid": 3.753,
        "trade": 3.822
      },
      {
        "mid": 3.625,
        "trade": 3.737
      },
      {
        "mid": 0.893,
        "trade": 0.892
      },
      {
        "mid": 0.876,
        "trade": 1.676
      },
      {
        "mid": 1.123,
        "trade": 1.584
      },
      {
        "mid": 1.093,
        "trade": 1.921
      },
      {
        "mid": 0.198,
        "trade": 0.358
      },
      {
        "mid": 3.82,
        "trade": 3.997
      },
      {
        "mid": 1.694,
        "trade": 1.953
      },
      {
        "mid": 1.152,
        "trade": 0.951
      },
      {
        "mid": 0.168,
        "trade": 0.68
      },
      {
        "mid": 0.311,
        "trade": 0.217
      },
      {
        "mid": 0.989,
        "trade": 1.789
      },
      {
        "mid": 0.369,
        "trade": 0.395
      },
      {
        "mid": 0.799,
        "trade": 0.585
      },
      {
        "mid": 2.625,
        "trade": 2.542
      },
      {
        "mid": 1.232,
        "trade": 0.532
      },
      {
        "mid": 1.301,
        "trade": 1.345
      },
      {
        "mid": 1.167,
        "trade": 1.085
      },
      {
        "mid": 0.284,
        "trade": 0.05
      },
      {
        "mid": 2.37,
        "trade": 2.055
      },
      {
        "mid": 2.477,
        "trade": 2.517
      },
      {
        "mid": 2.608,
        "trade": 2.481
      },
      {
        "mid": 0.452,
        "trade": 0.347
      },
      {
        "mid": 2.973,
        "trade": 3.228
      },
      {
        "mid": 0.98,
        "trade": 0.888
      },
      {
        "mid": 3.224,
        "trade": 3.196
      },
      {
        "mid": 3.186,
        "trade": 3.006
      },
      {
        "mid": 1.49,
        "trade": 1.335
      },
      {
        "mid": 3.603,
        "trade": 3.776
      },
      {
        "mid": 0.273,
        "trade": 0.15
      },
      {
        "mid": 1.548,
        "trade": 1.533
      },
      {
        "mid": 0.49,
        "trade": 0.536
      },
      {
        "mid": 2.548,
        "trade": 2.636
      },
      {
        "mid": 0.935,
        "trade": 0.931
      },
      {
        "mid": 2.114,
        "trade": 2.134
      },
      {
        "mid": 1.611,
        "trade": 1.866
      },
      {
        "mid": 2.002,
        "trade": 1.302
      },
      {
        "mid": 3.088,
        "trade": 3.051
      },
      {
        "mid": 2.037,
        "trade": 2.083
      },
      {
        "mid": 1.323,
        "trade": 1.392
      },
      {
        "mid": 2.618,
        "trade": 2.64
      },
      {
        "mid": 0.12,
        "trade": 0.05
      },
      {
        "mid": 3.029,
        "trade": 2.901
      },
      {
        "mid": 0.287,
        "trade": 0.267
      },
      {
        "mid": 3.817,
        "trade": 3.711
      },
      {
        "mid": 0.418,
        "trade": 0.05
      },
      {
        "mid": 0.601,
        "trade": 0.841
      },
      {
        "mid": 0.712,
        "trade": 1.062
      },
      {
        "mid": 1.308,
        "trade": 1.206
      },
      {
        "mid": 0.141,
        "trade": 0.333
      }
    ],
    "slope": 0.9578,
    "intercept": 0.0676,
    "r2": 0.9161,
    "note": "Illustrative near-the-money prints vs mid \u2014 not a live LSEG pull. Replace with your chain. Y = TRDPRC_1, X = (BID+ASK)/2."
  }
};
