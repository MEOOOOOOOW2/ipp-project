# scoring.py - turns ratio values into points, a composite score, a band and a final label
import pandas as pd                         # tables and missing-value checks
from engine.indicators import windows, indicators   # window maker and ratio calculator

LIMITS = {                                  # (watch limit, red-flag limit) - fixed rules, never edited per company
    "Cash conversion": (0.8, 0.5),          # LOWER is worse
    "Accruals ratio": (0.05, 0.10),
    "Receivable days change": (0.10, 0.25),
    "Inventory days change": (0.10, 0.25),
    "Debt build-up": (0.25, 0.50),
}
LOWER_IS_WORSE = {"Cash conversion"}        # for these, a small value is the warning sign
ORDER = ["Low", "Moderate", "High", "Severe"]   # bands from best to worst
CUTS = (0.20, 0.40, 0.60)                   # score limits between the bands

def points(name, value):                    # 0 = clean, 1 = watch, 2 = red flag, None = not applicable
    if value is None or pd.isna(value):     # no data
        return None                         # excluded from the score
    watch, red = LIMITS[name]               # this indicator's limits
    if name in LOWER_IS_WORSE:              # low-is-bad indicators
        return 2 if value < red else 1 if value < watch else 0
    return 2 if value > red else 1 if value > watch else 0   # high-is-bad indicators

def score_company(t):                       # scores every 3-year window of one company
    rows = []                               # one row per window
    for w in windows(sorted(t.index)):      # each rolling window
        vals = indicators(t, w)             # ratio values
        pts = {k: points(k, v) for k, v in vals.items()}   # points per indicator
        done = [p for p in pts.values() if p is not None]  # only indicators that could be calculated
        score = sum(done) / (2 * len(done)) if done else 0 # points earned / points possible
        band = ORDER[sum(score > c for c in CUTS)]         # Low / Moderate / High / Severe
        flags = [k for k, p in pts.items() if p == 2]      # indicators that are red flags
        profits_without_cash = pts["Cash conversion"] == 2 and pts["Receivable days change"] == 2   # Rule A
        if profits_without_cash or len(flags) >= 2:        # Rule A or Rule B (two or more red flags)
            band = max(band, "High", key=ORDER.index)      # band becomes at least High
        row = {"Window": f"FY{w[0]}-{w[-1]}", "Points": f"{sum(done)}/{2 * len(done)}",
               "Score": score, "Band": band, "Which": ", ".join(flags) or "-"}
        row.update({"val: " + k: v for k, v in vals.items()})   # the actual ratio values
        row.update({"pts: " + k: p for k, p in pts.items()})    # the points given
        rows.append(row)                    # save this window
    return pd.DataFrame(rows)               # all windows as a table

def label(results):                         # final label using the latest 3 windows
    flagged = results["Band"].isin(["High", "Severe"]).tolist()   # True where band is High or Severe
    if sum(flagged[-3:]) >= 2:              # flagged in at least 2 of the latest 3 windows
        return "Persistent risk"
    if flagged and flagged[-1]:             # flagged only in the latest window
        return "Emerging risk"
    return "Flagged earlier" if any(flagged) else "Clean"   # older flag only, or nothing
