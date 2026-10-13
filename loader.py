# loader.py - reads the uploaded Excel file and builds ONE clean table (rows = years, columns = standard fields)
import re                                   # regular expressions, used to read year labels like "Mar-2024"
import pandas as pd                         # tables and Excel reading
# Same line item can have different names in different sources, so each standard field lists its aliases
ALIASES = {
    "Sales": ["sales", "revenue from operations", "total revenue", "net sales", "revenue"],
    "COGS": ["cost of goods sold", "cost of revenue", "cost of materials consumed"],
    "Net profit": ["net profit", "profit after tax", "pat", "net income"],
    "Receivables": ["receivables", "trade receivables", "accounts receivable", "debtors"],
    "Inventory": ["inventory", "inventories"],
    "Total Assets": ["total assets"],
    "Borrowings": ["borrowings", "total debt"],
    "CFO": ["cash from operating activity", "operating cash flow", "net cash from operating activities"],
}

def to_year(label):                         # turns "Mar-2024", "FY24", "2023-24" or an Excel date into 2024
    if hasattr(label, "year"):              # real Excel dates already carry a year
        return label.year                   # use it directly
    text = str(label)                       # otherwise treat the label as text
    m = re.search(r"(20\d\d)\s*-\s*(\d\d)\b", text)   # pattern like 2023-24
    if m:                                   # found
        return 2000 + int(m.group(2))       # the later year is the financial year
    m = re.search(r"(20\d\d)", text)        # pattern like Mar-2024
    if m:                                   # found
        return int(m.group(1))              # that is the year
    m = re.search(r"FY\s*(\d\d)\b", text, re.I)       # pattern like FY24
    return 2000 + int(m.group(1)) if m else None      # None means "not a year"

def clean(text):                            # lowercase and drop symbols so names can be compared
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(text).lower())).strip()

def read_sheet(xl, name):                   # one statement sheet -> table (rows = line items, columns = years)
    raw = xl.parse(name, header=None)       # read without assuming where the header is
    for i in range(min(15, len(raw))):      # the year header must be in the top 15 rows
        years = [to_year(v) if pd.notna(v) else None for v in raw.iloc[i, 1:]]   # try every cell as a year
        if sum(y is not None for y in years) >= 3:      # a real header row has at least 3 years
            body = raw.iloc[i + 1:, 1:].copy()          # the numbers below the header
            body.columns = years                        # label the columns by year
            body.index = [clean(v) for v in raw.iloc[i + 1:, 0]]   # label rows by cleaned line item name
            body = body.loc[:, [c for c in body.columns if c is not None]]   # drop columns that are not years
            body = body.apply(pd.to_numeric, errors="coerce")      # text -> numbers (bad cells become NaN)
            return body[~body.index.duplicated()]       # keep the first of any repeated line item
    return pd.DataFrame()                   # no header found in this sheet

def read_info(xl):                          # reads the Info sheet (key in column A, value in column B)
    info = {"Company": "Company", "Sector": "-", "Type": "Manufacturing"}   # defaults if Info is missing
    for s in xl.sheet_names:                # look through every sheet name
        if clean(s) == "info":              # only the Info sheet
            for _, r in xl.parse(s, header=None).iterrows():   # go row by row
                if pd.notna(r[0]) and pd.notna(r[1]):          # both key and value present
                    info[str(r[0]).strip()] = str(r[1]).strip()   # store them
    return info                             # dictionary of company details

def load_company(source):                   # main loader: Excel file -> (table, info, missing fields)
    xl = pd.ExcelFile(source)               # open the workbook
    keys = ("income", "profit", "balance", "cash")      # words that identify statement sheets
    frames = [read_sheet(xl, s) for s in xl.sheet_names if any(k in clean(s) for k in keys)]   # read each one
    frames = [f for f in frames if not f.empty]         # drop sheets where no year header was found
    if not frames:                          # nothing usable
        raise ValueError("No Income / Balance Sheet / Cash Flow sheet with a year header row was found")
    stacked = pd.concat(frames)             # all line items from all statements in one table
    stacked = stacked[~stacked.index.duplicated()]      # keep the first of any repeated names
    table, missing = {}, []                 # standard table and list of fields we could not find
    for field, names in ALIASES.items():    # go through every standard field
        hit = next((n for n in names if n in stacked.index), None)   # first alias that exists in the file
        if hit is None:                     # not found
            missing.append(field)           # remember it so the Checks sheet can show it
        else:                               # found
            table[field] = stacked.loc[hit]     # take that row (indexed by year)
    out = pd.DataFrame(table).reindex(columns=list(ALIASES)).sort_index()   # missing fields become empty columns
    return out, read_info(xl), missing      # table + company details + missing list
