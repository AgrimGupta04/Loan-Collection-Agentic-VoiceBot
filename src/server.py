import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import traceback
from pathlib import Path

# Railway port detection - CRITICAL: Railway provides PORT env variable
PORT = int(os.environ.get("PORT", 8000))
print(f"🚀 Starting on PORT: {PORT}")

# Initialize with minimal dependencies first
DB_AVAILABLE = False
CALLER_AVAILABLE = False  
AGENT_AVAILABLE = False

# Safe imports with detailed error logging
try:
    import sqlite3
    print("✓ SQLite available")
    
    # Create a minimal database class if the full one fails
    class MinimalDatabase:
        def __init__(self, db_file="customers.db"):
            self.con = sqlite3.connect(db_file, check_same_thread=False)
            self.create_table()
            self.seed_if_empty()
        
        def create_table(self):
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS customers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    phone VARCHAR NOT NULL,
                    due_date DATE NOT NULL,
                    loan_amount REAL NOT NULL,
                    call_status VARCHAR DEFAULT 'Pending',
                    notes VARCHAR DEFAULT ''
                )
            """)
            self.con.commit()
        
        def seed_if_empty(self):
            count = self.con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            if count == 0:
                customers = [
                    ("John Doe", "+1234567890", "2024-01-15", 5000.0, "Pending", ""),
                    ("Jane Smith", "+1234567891", "2024-01-20", 3500.0, "Pending", ""),
                    ("Mike Johnson", "+1234567892", "2024-01-25", 7200.0, "Pending", "")
                ]
                self.con.executemany(
                    "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    customers
                )
                self.con.commit()
        
        def fetch_due_customers(self):
            return self.con.execute("SELECT * FROM customers WHERE call_status = 'Pending'").fetchall()
        
        def log_call_outcome(self, customer_id, status, notes):
            self.con.execute("UPDATE customers SET call_status = ?, notes = ? WHERE id = ?", (status, notes, customer_id))
            self.con.commit()
    
    DB = MinimalDatabase()
    DB_AVAILABLE = True
    print("✓ Minimal Database initialized")
    
except Exception as e:
    print(f"✗ Database failed: {e}")
    DB = None

# Try to import the full modules, fall back to minimal versions
try:
    from database import Database
    DB = Database("customers.db")
    print("✓ Full Database module loaded")
except Exception as e:
    print(f"Note: Using minimal database due to: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Environment variables loaded")
except Exception as e:
    print(f"Note: dotenv not available: {e}")

try:
    from caller_agent import CallerAgent
    CALLER = CallerAgent(use_groq=True)
    CALLER_AVAILABLE = True
    print("✓ CallerAgent ready")
except Exception as e:
    print(f"Note: CallerAgent not available: {e}")
    CALLER = None
    
try:
    from outcome_agent import Outcome_agent  
    AGENT = Outcome_agent(use_groq=True)
    AGENT_AVAILABLE = True
    print("✓ Outcome_agent ready")
except Exception as e:
    print(f"Note: Outcome_agent not available: {e}")
    AGENT = None

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
        pending_html = "<p>✅ No pending customers</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Collection VoiceBot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; min-height: 100vh; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .card {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 25px; margin: 20px 0; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); }}
            .status {{ color: #4ade80; font-weight: bold; }}
            .failed {{ color: #f87171; }}
            h1 {{ text-align: center; font-size: 2.5em; margin-bottom: 10px; }}
            .subtitle {{ text-align: center; opacity: 0.8; margin-bottom: 30px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4ade80; }}
            a {{ color: #60a5fa; text-decoration: none; font-weight: bold; }}
            a:hover {{ color: #93c5fd; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .metric {{ text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #4ade80; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Loan Collection VoiceBot</h1>
            <p class="subtitle">AI-Powered Voice Assistant for Loan Collection</p>
            
            <div class="card">
                <h2>📊 System Status</h2>
                <div class="grid">
                    <div class="metric">
                        <div class="metric-value">{len(all_customers)}</div>
                        <div>Total Customers</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len(pending)}</div>
                        <div>Pending Calls</div>
                    </div>
                </div>
                <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.2); margin: 20px 0;">
                <p>Database: <span class="{'status' if DB else 'failed'}">{'✓ Connected' if DB else '✗ Failed'}</span></p>
                <p>CallerAgent: <span class="{'status' if CALLER else 'failed'}">{'✓ Ready' if CALLER else '✗ Not Available'}</span></p>
                <p>OutcomeAgent: <span class="{'status' if AGENT else 'failed'}">{'✓ Ready' if AGENT else '✗ Not Available'}</span></p>
            </div>
            
            <div class="card">
                <h2>📞 Pending Customer Calls</h2>
                {pending_html}
            </div>
            
            <div class="card">
                <h2>🔗 Navigation</h2>
                <p>
                    <a href="/health">🏥 Health Check</a> | 
                    <a href="/all">👥 All Customers</a> | 
                    <a href="/api/customers">📡 API Endpoint</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Only log errors to reduce spam
        if "error" in format.lower() or args and any("error" in str(arg).lower() for arg in args):
            print(f"HTTP: {format % args}")
        
    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(simple_home().encode())
                return
                
            elif self.path == "/health":
                health = {
                    "status": "healthy",
                    "port": PORT,
                    "database": DB is not None,
                    "caller_agent": CALLER is not None,
                    "outcome_agent": AGENT is not None,
                    "customers": len(query_all()) if DB else 0,
                    "pending": len(query_pending()) if DB else 0,
                    "timestamp": time.time()
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps(health, indent=2).encode())
                return
                
            elif self.path == "/all":
                customers = query_all()
                customers_html = ""
                if customers:
                    customers_html = "<ul>" + "".join([
                        f"""<li style="border-left-color: {'#4ade80' if c['call_status'] == 'SUCCESSFUL' else '#f87171' if c['call_status'] == 'FAILED' else '#fbbf24'}">
                        <strong>#{c['id']} - {c['name']}</strong><br>
                        📞 {c['phone']} | 💰 ₹{c['loan_amount']} | 📅 {c['due_date']}<br>
                        Status: <span class="{'status' if c['call_status'] == 'SUCCESSFUL' else 'failed'}">{c['call_status']}</span>
                        {f"<br>📝 {c['notes']}" if c['notes'] else ""}
                        </li>"""
                        for c in customers
                    ]) + "</ul>"
                else:
                    customers_html = "<p>No customers found</p>"
                
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>All Customers - VoiceBot</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;margin:0;padding:20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;min-height:100vh}}
                        .container{{max-width:800px;margin:0 auto}}
                        .card{{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);padding:25px;margin:20px 0;border-radius:15px;border:1px solid rgba(255,255,255,0.2)}}
                        ul{{list-style:none;padding:0}}
                        li{{background:rgba(255,255,255,0.05);padding:15px;margin:10px 0;border-radius:8px;border-left:4px solid #4ade80}}
                        .status{{color:#4ade80;font-weight:bold}}
                        .failed{{color:#f87171;font-weight:bold}}
                        a{{color:#60a5fa;text-decoration:none;font-weight:bold}}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="card">
                            <h1>👥 All Customers ({len(customers)})</h1>
                            {customers_html}
                            <p><a href="/">← Back to Dashboard</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
                return
                
            elif self.path == "/api/customers":
                customers = query_all()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps({"customers": customers}, indent=2).encode())
                return
                
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html><body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a1a;color:#fff">
                <h1>404 - Page Not Found</h1>
                <p><a href="/" style="color:#60a5fa">Go Home</a></p>
                </body></html>
                """)
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                error_html = f"""
                <html><body style="font-family:Arial;padding:40px;background:#1a1a1a;color:#fff">
                <h1>500 - Server Error</h1>
                <pre style="background:#333;padding:20px;border-radius:5px;overflow:auto">{str(e)}</pre>
                <p><a href="/" style="color:#60a5fa">Go Home</a></p>
                </body></html>
                """
                self.wfile.write(error_html.encode())
            except:
                pass

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            response = {"message": "POST endpoint working", "received_data": post_data}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"POST error: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def test_port():
    """Test if the port is available"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", PORT))
        s.close()
        return True
    except:
        return False

if __name__ == "__main__":
    try:
        print(f"🔧 Components Status:")
        print(f"   Database: {'✓' if DB_AVAILABLE else '✗'}")
        print(f"   CallerAgent: {'✓' if CALLER_AVAILABLE else '✗'}")  
        print(f"   OutcomeAgent: {'✓' if AGENT_AVAILABLE else '✗'}")
        
        if not test_port():
            print(f"⚠️  Port {PORT} might be busy, but continuing...")
        
        print(f"🚀 Starting HTTP server on 0.0.0.0:{PORT}")
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        
        print(f"✅ Server ready!")
        print(f"🌐 Local: http://localhost:{PORT}")
        print(f"🏥 Health: http://localhost:{PORT}/health")
        print(f"📡 API: http://localhost:{PORT}/api/customers")
        print(f"🎯 Railway will proxy this to your domain")
        print("=" * 50)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"💥 Server startup failed: {e}")
        traceback.print_exc()
        # Try alternative port
        try:
            alt_port = 3000
            print(f"🔄 Trying alternative port {alt_port}")
            server = HTTPServer(("0.0.0.0", alt_port), Handler)
            server.serve_forever()
        except:
            print("❌ All startup attempts failed")