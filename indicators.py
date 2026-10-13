# indicators.py - the red-flag ratios, each calculated over one 3-year window
import pandas as pd                         # for missing-value checks

def div(a, b):                              # safe division: returns None instead of crashing
    return None if (pd.isna(a) or pd.isna(b) or b == 0) else a / b

def windows(years):                         # rolling 3-year windows, e.g. [2015,16,17], [2016,17,18] ...
    return [years[i:i + 3] for i in range(len(years) - 2)]

def indicators(t, w):                       # t = table of years, w = list of 3 years
    d = t.loc[w]                            # only the rows of this window
    profit, cash = d["Net profit"].sum(), d["CFO"].sum()   # 3-year profit and 3-year operating cash flow
    missing = d[["Net profit", "CFO"]].isna().any().any()  # True if any needed number is empty
    cc = None if (profit <= 0 or missing) else cash / profit   # cash conversion: cash earned per rupee of profit
    gap = (d["Net profit"] - d["CFO"]).mean()              # average profit that is NOT backed by cash
    acc = div(gap, d["Total Assets"].mean())               # accruals ratio: that gap as a share of assets
    def days_change(item, base):            # how much "days" (item / base) grew from first to last year
        s = div(d[item].iloc[0], d[base].iloc[0])          # days measure in the first year
        e = div(d[item].iloc[-1], d[base].iloc[-1])        # days measure in the last year
        return None if not s or e is None else e / s - 1   # percentage change
    start = div(d["Borrowings"].iloc[0], d["Sales"].iloc[0])    # debt per rupee of sales, first year
    end = div(d["Borrowings"].iloc[-1], d["Sales"].iloc[-1])    # debt per rupee of sales, last year
    if end is None or end < 0.20:           # debt too small to matter
        debt = 0.0                          # treat as no build-up
    else:                                   # debt is material
        debt = None if not start else end / start - 1      # growth in debt relative to sales
    return {"Cash conversion": cc, "Accruals ratio": acc,
            "Receivable days change": days_change("Receivables", "Sales"),
            "Inventory days change": days_change("Inventory", "COGS"),
            "Debt build-up": debt}          # name -> value, N/A shown as None
