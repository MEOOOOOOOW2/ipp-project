# Earnings Red-Flag Screener
Upload a company Excel file, get it back with Summary, Ratios, Scores, Charts and Checks sheets.
Folders: engine/ (all Python logic, one file per topic), api/ (Vercel function), public/ (upload page).
Deploy: push to GitHub, import the repo in Vercel. Python libraries: pandas, numpy, matplotlib, openpyxl.
Input: sheets Info (key/value: Company, Sector, Type), Income, Balance Sheet, Cash Flow (line items in column A, years across).
