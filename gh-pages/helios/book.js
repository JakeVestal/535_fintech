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
      "occ": "AAPL",
      "asset": "STK",
      "strike": null,
      "expiry": null,
      "limit": 188.4,
      "fill": 188.4,
      "multiplier": 1,
      "notes": "Monday combo \u00b7 stock leg. Limit = open print. Decrease cash. Rule: if flat, buy 100."
    },
    {
      "id": "t2",
      "ts": "2026-06-01 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLF52619000.U^F26",
      "occ": "AAPL 6/5 190.0 C",
      "asset": "CALL",
      "strike": 190,
      "expiry": "2026-06-05",
      "limit": 1.82,
      "fill": 1.82,
      "multiplier": 100,
      "notes": "Monday combo \u00b7 call leg. Nearest OTM Friday weekly. Limit = mid. Increase cash 100\u00d7mid."
    },
    {
      "id": "t3",
      "ts": "2026-06-05 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLF52619000.U^F26",
      "occ": "AAPL 6/5 190.0 C",
      "asset": "CALL",
      "strike": 190,
      "expiry": "2026-06-05",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM. Exit = wait. Keep shares, keep premium."
    },
    {
      "id": "t4",
      "ts": "2026-06-08 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLF122619250.U^F26",
      "occ": "AAPL 6/12 192.5 C",
      "asset": "CALL",
      "strike": 192.5,
      "expiry": "2026-06-12",
      "limit": 1.64,
      "fill": 1.64,
      "multiplier": 100,
      "notes": "Still long. Write next Friday weekly. Limit = mid."
    },
    {
      "id": "t5",
      "ts": "2026-06-12 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLF122619250.U^F26",
      "occ": "AAPL 6/12 192.5 C",
      "asset": "CALL",
      "strike": 192.5,
      "expiry": "2026-06-12",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t6",
      "ts": "2026-06-15 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLF192619000.U^F26",
      "occ": "AAPL 6/19 190.0 C",
      "asset": "CALL",
      "strike": 190,
      "expiry": "2026-06-19",
      "limit": 1.91,
      "fill": 1.91,
      "multiplier": 100,
      "notes": "Spot dipped; ATM-ish 190s. Limit = mid."
    },
    {
      "id": "t7",
      "ts": "2026-06-19 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLF192619000.U^F26",
      "occ": "AAPL 6/19 190.0 C",
      "asset": "CALL",
      "strike": 190,
      "expiry": "2026-06-19",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t8",
      "ts": "2026-06-22 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLF262619500.U^F26",
      "occ": "AAPL 6/26 195.0 C",
      "asset": "CALL",
      "strike": 195,
      "expiry": "2026-06-26",
      "limit": 1.55,
      "fill": 1.55,
      "multiplier": 100,
      "notes": "Nearest OTM 195s. Limit = mid."
    },
    {
      "id": "t9",
      "ts": "2026-06-26 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLF262619500.U^F26",
      "occ": "AAPL 6/26 195.0 C",
      "asset": "CALL",
      "strike": 195,
      "expiry": "2026-06-26",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t10",
      "ts": "2026-06-29 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLG32619750.U^G26",
      "occ": "AAPL 7/3 197.5 C",
      "asset": "CALL",
      "strike": 197.5,
      "expiry": "2026-07-03",
      "limit": 1.48,
      "fill": 1.48,
      "multiplier": 100,
      "notes": "Monday rewrite. Limit = mid."
    },
    {
      "id": "t11",
      "ts": "2026-07-03 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLG32619750.U^G26",
      "occ": "AAPL 7/3 197.5 C",
      "asset": "CALL",
      "strike": 197.5,
      "expiry": "2026-07-03",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t12",
      "ts": "2026-07-06 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLG102619500.U^G26",
      "occ": "AAPL 7/10 195.0 C",
      "asset": "CALL",
      "strike": 195,
      "expiry": "2026-07-10",
      "limit": 1.72,
      "fill": 1.72,
      "multiplier": 100,
      "notes": "Rewrite 195s. Limit = mid."
    },
    {
      "id": "t13",
      "ts": "2026-07-10 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLG102619500.U^G26",
      "occ": "AAPL 7/10 195.0 C",
      "asset": "CALL",
      "strike": 195,
      "expiry": "2026-07-10",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t14",
      "ts": "2026-07-13 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLG172620000.U^G26",
      "occ": "AAPL 7/17 200.0 C",
      "asset": "CALL",
      "strike": 200,
      "expiry": "2026-07-17",
      "limit": 1.38,
      "fill": 1.38,
      "multiplier": 100,
      "notes": "Nearest OTM 200s. Limit = mid."
    },
    {
      "id": "t15",
      "ts": "2026-07-17 16:00",
      "side": "ASSIGN",
      "qty": 1,
      "instrument": "AAPLG172620000.U^G26",
      "occ": "AAPL 7/17 200.0 C",
      "asset": "CALL",
      "strike": 200,
      "expiry": "2026-07-17",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday ITM. Exit = wait. Assigned the short call against the long stock."
    },
    {
      "id": "t16",
      "ts": "2026-07-17 16:00",
      "side": "SELL",
      "qty": 100,
      "instrument": "AAPL",
      "occ": "AAPL",
      "asset": "STK",
      "strike": 200,
      "expiry": "2026-07-17",
      "limit": 200.0,
      "fill": 200.0,
      "multiplier": 1,
      "notes": "Assignment delivery: sell 100 at strike. Increase cash 100\u00d7200. Now flat."
    },
    {
      "id": "t17",
      "ts": "2026-07-20 09:30",
      "side": "BUY",
      "qty": 100,
      "instrument": "AAPL",
      "occ": "AAPL",
      "asset": "STK",
      "strike": null,
      "expiry": null,
      "limit": 201.2,
      "fill": 201.2,
      "multiplier": 1,
      "notes": "Flat after assignment. Combo stock leg. Decrease cash."
    },
    {
      "id": "t18",
      "ts": "2026-07-20 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLG242620250.U^G26",
      "occ": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "limit": 1.41,
      "fill": 1.41,
      "multiplier": 100,
      "notes": "Combo call leg. Next Friday weekly. Limit = mid."
    },
    {
      "id": "t19",
      "ts": "2026-07-24 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLG242620250.U^G26",
      "occ": "AAPL 7/24 202.5 C",
      "asset": "CALL",
      "strike": 202.5,
      "expiry": "2026-07-24",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t20",
      "ts": "2026-07-27 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLG312620000.U^G26",
      "occ": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200,
      "expiry": "2026-07-31",
      "limit": 1.66,
      "fill": 1.66,
      "multiplier": 100,
      "notes": "Still long. Monday rewrite. Limit = mid."
    },
    {
      "id": "t21",
      "ts": "2026-07-31 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLG312620000.U^G26",
      "occ": "AAPL 7/31 200.0 C",
      "asset": "CALL",
      "strike": 200,
      "expiry": "2026-07-31",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire."
    },
    {
      "id": "t22",
      "ts": "2026-08-03 09:30",
      "side": "SELL",
      "qty": 1,
      "instrument": "AAPLH72620500.U^H26",
      "occ": "AAPL 8/7 205.0 C",
      "asset": "CALL",
      "strike": 205,
      "expiry": "2026-08-07",
      "limit": 1.52,
      "fill": 1.52,
      "multiplier": 100,
      "notes": "Nearest OTM 205s. Limit = mid."
    },
    {
      "id": "t23",
      "ts": "2026-08-07 16:00",
      "side": "EXPIRE",
      "qty": 1,
      "instrument": "AAPLH72620500.U^H26",
      "occ": "AAPL 8/7 205.0 C",
      "asset": "CALL",
      "strike": 205,
      "expiry": "2026-08-07",
      "limit": null,
      "fill": 0,
      "multiplier": 100,
      "notes": "Friday OTM expire. Sample window ends."
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
  "writeup": {
    "title": "Worked example \u2014 AAPL Friday weeklies (wait through expiry)",
    "fill": "Illustrative book, not a live LSEG pull. Limit = fill = (BID+ASK)/2 on the call; stock at the 09:30 print. No bid/ask \u2192 skip. TRDPRC_1 is the scatter Y, not the fill.",
    "roll": "No roll, no BTC. Exit is wait until Friday 16:00. OTM: EXPIRE, keep shares, next Monday write the next weekly. ITM: ASSIGN the short call against the long stock \u2014 you are flat. Deliver 100 shares at strike (cash += 100\u00d7strike). Next Monday buy 100 again and write the new Friday call.",
    "pin": "Assignment is the ITM exit. The blotter shows ASSIGN on the call RIC and SELL on AAPL at the strike.",
    "regT": "Covered call: long 100, short 1 call. Initial = 50% of stock LMV. Maintenance = 25% of LMV. Covered short call adds $0. NAV = cash + stock MV + option MV. Available = NAV \u2212 initial. After assignment LMV is 0 until the next Monday buy."
  },
  "midVsTrade": {
    "points": [
      {
        "mid": 0.928,
        "trade": 1.262
      },
      {
        "mid": 3.57,
        "trade": 4.37
      },
      {
        "mid": 1.215,
        "trade": 1.34
      },
      {
        "mid": 3.093,
        "trade": 3.419
      },
      {
        "mid": 0.52,
        "trade": 0.81
      },
      {
        "mid": 0.251,
        "trade": 0.05
      },
      {
        "mid": 1.284,
        "trade": 1.362
      },
      {
        "mid": 2.064,
        "trade": 1.908
      },
      {
        "mid": 2.068,
        "trade": 1.566
      },
      {
        "mid": 1.479,
        "trade": 1.216
      },
      {
        "mid": 0.827,
        "trade": 0.648
      },
      {
        "mid": 2.002,
        "trade": 1.665
      },
      {
        "mid": 1.61,
        "trade": 1.476
      },
      {
        "mid": 0.307,
        "trade": 0.395
      },
      {
        "mid": 0.66,
        "trade": 0.533
      },
      {
        "mid": 0.464,
        "trade": 0.708
      },
      {
        "mid": 3.63,
        "trade": 3.809
      },
      {
        "mid": 2.377,
        "trade": 2.554
      },
      {
        "mid": 2.119,
        "trade": 2.35
      },
      {
        "mid": 0.263,
        "trade": 0.293
      },
      {
        "mid": 0.163,
        "trade": 0.05
      },
      {
        "mid": 1.202,
        "trade": 1.058
      },
      {
        "mid": 1.052,
        "trade": 1.264
      },
      {
        "mid": 1.937,
        "trade": 2.109
      },
      {
        "mid": 0.344,
        "trade": 0.233
      },
      {
        "mid": 1.963,
        "trade": 2.139
      },
      {
        "mid": 2.043,
        "trade": 1.811
      },
      {
        "mid": 3.031,
        "trade": 2.872
      },
      {
        "mid": 1.031,
        "trade": 0.874
      },
      {
        "mid": 1.453,
        "trade": 1.519
      },
      {
        "mid": 3.644,
        "trade": 3.435
      },
      {
        "mid": 1.59,
        "trade": 1.795
      },
      {
        "mid": 1.633,
        "trade": 1.587
      },
      {
        "mid": 0.339,
        "trade": 0.59
      },
      {
        "mid": 2.44,
        "trade": 2.329
      },
      {
        "mid": 1.703,
        "trade": 1.621
      },
      {
        "mid": 1.881,
        "trade": 2.108
      },
      {
        "mid": 0.543,
        "trade": 0.05
      },
      {
        "mid": 1.122,
        "trade": 1.212
      },
      {
        "mid": 0.43,
        "trade": 0.647
      },
      {
        "mid": 0.882,
        "trade": 0.964
      },
      {
        "mid": 1.015,
        "trade": 0.91
      },
      {
        "mid": 0.986,
        "trade": 1.527
      },
      {
        "mid": 3.605,
        "trade": 3.722
      },
      {
        "mid": 0.492,
        "trade": 0.427
      },
      {
        "mid": 1.189,
        "trade": 1.285
      },
      {
        "mid": 1.176,
        "trade": 0.759
      },
      {
        "mid": 0.193,
        "trade": 0.46
      },
      {
        "mid": 3.846,
        "trade": 3.352
      },
      {
        "mid": 0.76,
        "trade": 0.976
      },
      {
        "mid": 3.239,
        "trade": 2.794
      },
      {
        "mid": 3.841,
        "trade": 3.716
      },
      {
        "mid": 0.764,
        "trade": 1.042
      },
      {
        "mid": 2.023,
        "trade": 1.323
      },
      {
        "mid": 0.601,
        "trade": 0.604
      },
      {
        "mid": 0.332,
        "trade": 0.376
      },
      {
        "mid": 1.488,
        "trade": 1.758
      },
      {
        "mid": 0.156,
        "trade": 0.107
      },
      {
        "mid": 3.216,
        "trade": 3.336
      },
      {
        "mid": 0.697,
        "trade": 1.497
      },
      {
        "mid": 0.277,
        "trade": 0.28
      },
      {
        "mid": 0.192,
        "trade": 0.497
      },
      {
        "mid": 0.307,
        "trade": 1.107
      },
      {
        "mid": 0.306,
        "trade": 0.24
      },
      {
        "mid": 3.097,
        "trade": 3.144
      },
      {
        "mid": 2.026,
        "trade": 2.097
      },
      {
        "mid": 1.046,
        "trade": 1.846
      },
      {
        "mid": 0.42,
        "trade": 1.22
      },
      {
        "mid": 3.745,
        "trade": 4.545
      },
      {
        "mid": 0.162,
        "trade": 0.081
      }
    ],
    "slope": 0.9706,
    "intercept": 0.1098,
    "r2": 0.9185,
    "note": "Illustrative near-the-money prints vs mid \u2014 not a live pull. Y = TRDPRC_1, X = (BID+ASK)/2."
  }
};
