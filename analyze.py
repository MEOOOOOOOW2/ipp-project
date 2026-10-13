# analyze.py - Vercel serverless function: receives the Excel file, returns the analysed Excel file
import os, sys                              # file paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))   # lets this file import the engine folder
from http.server import BaseHTTPRequestHandler   # Python built-in web handler (no extra library)
from engine.pipeline import run_analysis    # the whole analysis

class handler(BaseHTTPRequestHandler):      # Vercel looks for a class called handler
    def do_POST(self):                      # runs when the page sends the file
        try:                                # catch problems and report them nicely
            size = int(self.headers.get("Content-Length", 0))   # how many bytes were uploaded
            out = run_analysis(self.rfile.read(size))           # read the file and analyse it
            self.send_response(200)         # success
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.end_headers()              # finish headers
            self.wfile.write(out)           # send the Excel file back
        except Exception as e:              # anything went wrong
            self.send_response(400)         # bad request
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())   # send the reason as text
