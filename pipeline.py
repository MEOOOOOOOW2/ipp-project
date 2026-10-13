# pipeline.py - runs the full flow: load -> score -> write report
import io                                   # in-memory files
from engine.loader import load_company     # step 1: read the Excel
from engine.scoring import score_company   # step 2: score every window
from engine.report import build_workbook   # step 3: write the output Excel

def run_analysis(data):                     # data = uploaded file bytes, returns analysed file bytes
    table, info, missing = load_company(io.BytesIO(data))   # step 1
    results = score_company(table)          # step 2
    if results.empty:                       # fewer than 3 years of data
        raise ValueError("Need at least 3 years of data to form one window")
    return build_workbook(data, table, info, missing, results)   # step 3
