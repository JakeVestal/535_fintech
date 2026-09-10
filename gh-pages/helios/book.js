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
      "notes": "Combo stock leg. Limit at the open print. 100 shares."
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
      "notes": "Combo call leg. Friday weekly, ~0.5\u20131 strike OTM. Limit = option mid."
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
      "notes": "Friday close OTM. Short call off. Keep the 1.82."
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
      "notes": "Monday open rewrite. Limit at mid."
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
      "notes": "Expires OTM."
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
      "notes": "Expires OTM."
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
      "notes": "Expires OTM."
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
      "notes": "Monday open, Friday weekly."
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
      "notes": "Expires OTM."
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
      "notes": "Expires OTM."
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
      "ts": "2026-07-17 15:45",
      "side": "BTC",
      "qty": 1,
      "instrument": "AAPL 7/17 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-17",
      "price": 2.46,
      "multiplier": 100,
      "notes": "ITM into the close. Limit BTC at mid \u2014 do not take assignment. Roll rule fired."
    },
    {
      "id": "t16",
      "ts": "2026-07-20 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "price": 1.41,
      "multiplier": 100,
      "notes": "Roll out and up. New Friday weekly. Limit at mid."
    },
    {
      "id": "t17",
      "ts": "2026-07-24 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "price": 0,
      "multiplier": 100,
      "notes": "Expires OTM."
    },
    {
      "id": "t18",
      "ts": "2026-07-27 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-31",
      "price": 1.66,
      "multiplier": 100,
      "notes": "Monday rewrite."
    },
    {
      "id": "t19",
      "ts": "2026-07-31 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200.0,
      "expiry": "2026-07-31",
      "price": 0,
      "multiplier": 100,
      "notes": "Expires OTM."
    },
    {
      "id": "t20",
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
      "id": "t21",
      "ts": "2026-08-07 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPL 8/7 205.0 C",
      "asset": "CALL",
      "strike": 205.0,
      "expiry": "2026-08-07",
      "price": 0,
      "multiplier": 100,
      "notes": "Expires OTM. Sample window ends."
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
      "cash": 7064.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 201.2,
      "optPx": 0.0,
      "lmv": 20120.0,
      "optMv": 0.0,
      "nav": 27184.0,
      "init": 10060.0,
      "maint": 5030.0,
      "available": 17124.0,
      "excess": 22154.0
    },
    {
      "date": "2026-07-20",
      "cash": 7205.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/24 202.5C",
      "stockPx": 201.2,
      "optPx": 1.41,
      "lmv": 20120.0,
      "optMv": -141.0,
      "nav": 27184.0,
      "init": 10060.0,
      "maint": 5030.0,
      "available": 17124.0,
      "excess": 22154.0
    },
    {
      "date": "2026-07-24",
      "cash": 7205.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 199.8,
      "optPx": 0.0,
      "lmv": 19980.0,
      "optMv": 0.0,
      "nav": 27185.0,
      "init": 9990.0,
      "maint": 4995.0,
      "available": 17195.0,
      "excess": 22190.0
    },
    {
      "date": "2026-07-27",
      "cash": 7371.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "7/31 200C",
      "stockPx": 199.4,
      "optPx": 1.66,
      "lmv": 19940.0,
      "optMv": -166.0,
      "nav": 27145.0,
      "init": 9970.0,
      "maint": 4985.0,
      "available": 17175.0,
      "excess": 22160.0
    },
    {
      "date": "2026-07-31",
      "cash": 7371.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 198.75,
      "optPx": 0.0,
      "lmv": 19875.0,
      "optMv": 0.0,
      "nav": 27246.0,
      "init": 9937.5,
      "maint": 4968.75,
      "available": 17308.5,
      "excess": 22277.25
    },
    {
      "date": "2026-08-03",
      "cash": 7523.0,
      "shares": 100,
      "shortCalls": -1,
      "callLabel": "8/7 205C",
      "stockPx": 204.1,
      "optPx": 1.52,
      "lmv": 20410.0,
      "optMv": -152.0,
      "nav": 27781.0,
      "init": 10205.0,
      "maint": 5102.5,
      "available": 17576.0,
      "excess": 22678.5
    },
    {
      "date": "2026-08-07",
      "cash": 7523.0,
      "shares": 100,
      "shortCalls": 0,
      "callLabel": "\u2014",
      "stockPx": 203.4,
      "optPx": 0.0,
      "lmv": 20340.0,
      "optMv": 0.0,
      "nav": 27863.0,
      "init": 10170.0,
      "maint": 5085.0,
      "available": 17693.0,
      "excess": 22778.0
    }
  ],
  "writeup": {
    "title": "Worked example \u2014 AAPL Friday weeklies (baseline + one roll)",
    "fill": "Limit orders only. Stock leg fills at the 09:30 print. Call leg limit = (BID+ASK)/2 at that timestamp. If no bid/ask, skip the week. We do not use last (TRDPRC_1) as the fill \u2014 last is for the mid-vs-trade diagnostic only.",
    "roll": "Baseline: enter Monday 09:30 a 100-share + 1 Friday-expiry call combo, strike nearest OTM (or ATM if spot is on a strike). Exit: do nothing until Friday 16:00 if OTM (expire, premium kept). If the call is ITM at 15:45 Friday, BTC at mid (limit) \u2014 do not take assignment \u2014 and rewrite the next Monday. That is the only roll in this sample (17 Jul 200s).",
    "pin": "ITM into expiration Friday is treated as a failed hold. BTC before the print. No pin / lottery on the strike.",
    "regT": "Covered call: long 100 AAPL, short 1 call. Initial = 50% of stock LMV. Maintenance = 25% of LMV. The short call adds $0 margin because it is covered. NAV = cash + stock MV + option MV (short option is negative). Available funds = NAV \u2212 initial. Excess = NAV \u2212 maintenance. A book that lives in Reg T lives in portfolio margin; the converse is false."
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
        "mid": 0.421,
        "trade": 0.348
      },
      {
        "mid": 0.542,
        "trade": 0.583
      },
      {
        "mid": 0.612,
        "trade": 0.641
      },
      {
        "mid": 0.674,
        "trade": 0.702
      },
      {
        "mid": 0.817,
        "trade": 0.743
      },
      {
        "mid": 0.85,
        "trade": 0.866
      },
      {
        "mid": 0.96,
        "trade": 1.05
      },
      {
        "mid": 1.062,
        "trade": 1.011
      },
      {
        "mid": 1.155,
        "trade": 1.165
      },
      {
        "mid": 1.215,
        "trade": 1.21
      },
      {
        "mid": 1.295,
        "trade": 1.275
      },
      {
        "mid": 1.408,
        "trade": 1.386
      },
      {
        "mid": 1.487,
        "trade": 1.489
      },
      {
        "mid": 1.555,
        "trade": 1.542
      },
      {
        "mid": 1.626,
        "trade": 1.652
      },
      {
        "mid": 1.7,
        "trade": 1.757
      },
      {
        "mid": 1.814,
        "trade": 1.826
      },
      {
        "mid": 1.882,
        "trade": 1.88
      },
      {
        "mid": 2.01,
        "trade": 2.001
      },
      {
        "mid": 2.097,
        "trade": 2.033
      },
      {
        "mid": 2.19,
        "trade": 2.155
      },
      {
        "mid": 2.266,
        "trade": 2.328
      },
      {
        "mid": 2.354,
        "trade": 2.333
      },
      {
        "mid": 2.408,
        "trade": 2.459
      },
      {
        "mid": 2.474,
        "trade": 2.457
      },
      {
        "mid": 2.596,
        "trade": 2.516
      },
      {
        "mid": 2.632,
        "trade": 2.622
      },
      {
        "mid": 2.75,
        "trade": 2.817
      },
      {
        "mid": 2.861,
        "trade": 2.881
      },
      {
        "mid": 2.951,
        "trade": 2.999
      },
      {
        "mid": 2.995,
        "trade": 3.048
      },
      {
        "mid": 3.122,
        "trade": 3.156
      },
      {
        "mid": 3.203,
        "trade": 3.215
      },
      {
        "mid": 3.245,
        "trade": 3.228
      },
      {
        "mid": 3.353,
        "trade": 3.298
      },
      {
        "mid": 3.463,
        "trade": 3.562
      },
      {
        "mid": 3.52,
        "trade": 3.463
      },
      {
        "mid": 3.62,
        "trade": 3.624
      },
      {
        "mid": 3.654,
        "trade": 3.677
      },
      {
        "mid": 3.726,
        "trade": 3.729
      },
      {
        "mid": 3.888,
        "trade": 3.803
      },
      {
        "mid": 3.932,
        "trade": 3.882
      },
      {
        "mid": 4.019,
        "trade": 4.011
      },
      {
        "mid": 4.099,
        "trade": 4.12
      },
      {
        "mid": 4.158,
        "trade": 4.206
      },
      {
        "mid": 4.265,
        "trade": 4.407
      },
      {
        "mid": 4.363,
        "trade": 4.439
      },
      {
        "mid": 4.411,
        "trade": 4.407
      }
    ],
    "slope": 1.0062,
    "intercept": -0.009,
    "r2": 0.9983,
    "note": "Near-the-money AAPL weeklies in the window. Y = TRDPRC_1, X = (BID+ASK)/2. Sample illustration \u2014 replace with your LSEG pull."
  }
};
