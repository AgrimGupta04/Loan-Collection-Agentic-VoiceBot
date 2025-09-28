import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import traceback
from pathlib import Path

# Railway port detection
PORT = int(os.environ.get("PORT", 8000))
print(f"Starting on PORT: {PORT}")

# Safe imports with detailed error logging
DB_AVAILABLE = False
CALLER_AVAILABLE = False  
AGENT_AVAILABLE = False

try:
    from database import Database
    DB_AVAILABLE = True
    print("✓ Database module imported")
except Exception as e:
    print(f"✗ Database import failed: {e}")
    Database = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

try:
    from caller_agent import CallerAgent
    CALLER_AVAILABLE = True
    print("✓ CallerAgent imported")
except Exception as e:
    print(f"Note: CallerAgent not available: {e}")
    CallerAgent = None
    
try:
    from outcome_agent import Outcome_agent  
    AGENT_AVAILABLE = True
    print("✓ Outcome_agent imported")
except Exception as e:
    print(f"Note: Outcome_agent not available: {e}")
    Outcome_agent = None

# Initialize components safely
DB = None
CALLER = None
AGENT = None

if DB_AVAILABLE:
    try:
        DB = Database("customers.db")
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database failed: {e}")
        DB = None

if CALLER_AVAILABLE and CallerAgent:
    try:
        CALLER = CallerAgent(use_groq=True)
        print("✓ CallerAgent ready")
    except Exception as e:
        print(f"Note: CallerAgent init failed: {e}")

if AGENT_AVAILABLE and Outcome_agent:
    try:
        AGENT = Outcome_agent(use_groq=True)  
        print("✓ Outcome_agent ready")
    except Exception as e:
        print(f"Note: Outcome_agent init failed: {e}")

# Simple classification fallback
def classify_transcript(transcript: str) -> dict:
    t = (transcript or "").lower().strip()
    if any(word in t for word in ['yes', 'pay', 'sure', 'okay', 'will pay']):
        return {"status": "SUCCESSFUL", "notes": transcript}
    elif any(word in t for word in ["no", "can't", "later", "problem"]):
        return {"status": "NEED FOLLOW UP", "notes": transcript}
    else:
        return {"status": "FAILED", "notes": transcript}

# Safe query functions
def query_all():
    if not DB:
        return []
    try:
        rows = DB.con.execute("SELECT * FROM customers").fetchall()
        return [{"id": r[0], "name": r[1], "phone": r[2], "due_date": r[3], 
                "loan_amount": r[4], "call_status": r[5], "notes": r[6]} for r in rows]
    except Exception as e:
        print(f"Query error: {e}")
        return []

def query_pending():
    if not DB:
        return []
    try:
        rows = DB.fetch_due_customers()
        return [{"id": r[0], "name": r[1], "phone": r[2], "due_date": r[3], 
                "loan_amount": r[4], "call_status": r[5], "notes": r[6]} for r in rows]
    except Exception as e:
        print(f"Pending query error: {e}")
        return []

# Simple HTML responses
def simple_home():
    pending = query_pending()
    all_customers = query_all()
    
    pending_html = ""
    if pending:
        pending_html = "<ul>" + "".join([
            f"<li>#{p['id']} - {p['name']} - ₹{p['loan_amount']} due {p['due_date']}</li>"
            for p in pending
        ]) + "</ul>"
    else:
        pending_html = "<p>No pending customers</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Collection VoiceBot</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .card {{ background: #333; padding: 20px; margin: 20px 0; border-radius: 10px; }}
            .status {{ color: #4ade80; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Loan Collection VoiceBot</h1>
            <div class="card">
                <h2>System Status</h2>
                <p>Database: <span class="status">{'✓ Connected' if DB else '✗ Failed'}</span></p>
                <p>CallerAgent: <span class="status">{'✓ Ready' if CALLER else '✗ Not Available'}</span></p>
                <p>OutcomeAgent: <span class="status">{'✓ Ready' if AGENT else '✗ Not Available'}</span></p>
                <p>Total Customers: {len(all_customers)}</p>
            </div>
            <div class="card">
                <h2>Pending Customers</h2>
                {pending_html}
            </div>
            <div class="card">
                <p><a href="/health" style="color: #60a5fa;">Health Check</a> | 
                   <a href="/all" style="color: #60a5fa;">All Customers</a></p>
            </div>
        </div>
    </body>
    </html>
    """

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Reduce log spam
        pass
        
    def do_GET(self):
        try:
            print(f"Request: {self.path}")
            
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(simple_home().encode())
                return
                
            elif self.path == "/health":
                health = {
                    "status": "healthy",
                    "database": DB is not None,
                    "caller_agent": CALLER is not None,
                    "outcome_agent": AGENT is not None,
                    "customers": len(query_all()) if DB else 0
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(health).encode())
                return
                
            elif self.path == "/all":
                customers = query_all()
                customers_html = "<ul>" + "".join([
                    f"<li>#{c['id']} - {c['name']} - {c['call_status']} - ₹{c['loan_amount']}</li>"
                    for c in customers
                ]) + "</ul>" if customers else "<p>No customers found</p>"
                
                html = f"""
                <!DOCTYPE html>
                <html>
                <head><title>All Customers</title>
                <style>body{{font-family:Arial;margin:40px;background:#1a1a1a;color:#fff}}</style>
                </head>
                <body>
                    <h1>All Customers</h1>
                    {customers_html}
                    <p><a href="/" style="color:#60a5fa">← Back to Home</a></p>
                </body>
                </html>
                """
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
                return
                
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>404 - Page Not Found</h1>")
                
        except Exception as e:
            print(f"Request error: {e}")
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>500 - Server Error</h1><pre>{str(e)}</pre>".encode())
            except:
                pass

    def do_POST(self):
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>POST requests not implemented yet</h1>")
        except Exception as e:
            print(f"POST error: {e}")

if __name__ == "__main__":
    try:
        print(f"All components initialized. Starting server on {PORT}")
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        print(f"✓ Server ready at http://0.0.0.0:{PORT}")
        print(f"✓ Health: http://0.0.0.0:{PORT}/health")
        server.serve_forever()
    except Exception as e:
        print(f"Server startup failed: {e}")
        traceback.print_exc()