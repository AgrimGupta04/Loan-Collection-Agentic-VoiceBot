import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi
import traceback
from pathlib import Path
import database 

# Railway port detection - CRITICAL: Railway provides PORT env variable
PORT = int(os.environ.get("PORT", 8080))
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
                try:
                    from faker import Faker
                    import random
                    fake = Faker()
                    customers = []
                    for _ in range(5):
                        customers.append((
                            fake.name(),
                            fake.phone_number(),
                            fake.date_between(start_date="today", end_date="+30d").isoformat(),
                            round(random.uniform(1000, 10000), 2),
                            "Pending",
                            ""
                        ))
                    self.con.executemany(
                        "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                        customers
                    )
                    print("✓ MinimalDatabase seeded with Faker")
                except Exception:
                    # fallback static data
                    customers = [
                        ("John Doe", "+1234567890", "2024-01-15", 5000.0, "Pending", ""),
                        ("Jane Smith", "+1234567891", "2024-01-20", 3500.0, "Pending", ""),
                        ("Mike Johnson", "+1234567892", "2024-01-25", 7200.0, "Pending", "")
                    ]
                    self.con.executemany(
                        "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                        customers
                    )
                    print("✓ MinimalDatabase seeded with fallback static data")
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

DB_PATH = "customers.db"
OUTPUT_DIR = Path("demo_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def classify_transcript(transcript: str) -> dict:
    t = (transcript or "").lower().strip()
    import re
    neg_pattern_1 = re.search(r"\b(not|no|never|won['']t|cannot|can['']t|don['']t|dont|unable)\b.*\bpay\b", t)
    neg_pattern_2 = re.search(r"\bpay\b.*\b(not|no|never|won['']t|cannot|can['']t|don['']t|dont|unable)\b", t)
    if neg_pattern_1 or neg_pattern_2 or "not pay" in t or "no pay" in t or "refuse" in t or "refusing" in t:
        return {"status": "NEED FOLLOW UP", "notes": transcript}
    delay_words = ["later", "next week", "after", "sometime", "soonish", "month end", "end of month", "delay", "busy"]
    if any(w in t for w in delay_words):
        return {"status": "NEED FOLLOW UP", "notes": transcript}
    pos_patterns = [
        r"\b(i|we)\s+(will|can|shall|plan to|intend to)\s+pay\b",
        r"\b(make|do)\s+the\s+payment\b",
        r"\bpay(ing)?\s+(today|tomorrow|soon|now)\b",
        r"\byes\b.*\bpay\b",
        r"\bok(?:ay)?\b.*\bpay\b",
        r"\bsure\b.*\bpay\b",
    ]
    if any(re.search(p, t) for p in pos_patterns):
        return {"status": "SUCCESSFUL", "notes": transcript}
    if "yes" in t and ("tomorrow" in t or "today" in t or "soon" in t):
        return {"status": "SUCCESSFUL", "notes": transcript}
    return {"status": "FAILED", "notes": transcript}

def query_all():
    if not DB:
        return []
    try:
        rows = DB.con.execute("SELECT * FROM customers").fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "phone": r[2],
                "due_date": r[3],
                "loan_amount": r[4],
                "call_status": r[5],
                "notes": r[6],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Query error: {e}")
        return []

def query_pending():
    if not DB:
        return []
    try:
        rows = DB.fetch_due_customers()
        if not rows:
            try:
                DB.seed_data(5)  # seed 5 fresh records
                rows = DB.fetch_due_customers()
                print("✓ Database reseeded with Faker due to empty state")
            except Exception as e:
                print(f"Auto-seed failed: {e}")
        return [
            {
                "id": r[0],
                "name": r[1],
                "phone": r[2],
                "due_date": r[3],
                "loan_amount": r[4],
                "call_status": r[5],
                "notes": r[6],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Pending query error: {e}")
        return []

def render_table(rows):
    if not rows:
        return """
        <div class="empty">
          <div class="empty-icon">🗂️</div>
          <div class="empty-title">No records</div>
          <div class="empty-sub">Everything looks up to date</div>
        </div>
        """
    body = "".join(
        f"""
        <tr>
          <td>{r['id']}</td>
          <td>{r['name']}</td>
          <td>{r['phone']}</td>
          <td>{r['due_date']}</td>
          <td>₹{r['loan_amount']}</td>
          <td><span class="badge status status-{r['call_status'].replace(' ', '')}">{r['call_status']}</span></td>
          <td>{(r['notes'] or '')}</td>
        </tr>
        """
        for r in rows
    )
    return f"""
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr>
          <th>ID</th><th>Name</th><th>Phone</th><th>Due Date</th><th>Loan</th><th>Status</th><th>Notes</th>
        </tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    """

def render_customer_options(rows):
    return "".join(
        f"<option value=\"{r['id']}\">#{r['id']} — {r['name']} — ₹{r['loan_amount']} due {r['due_date']}</option>"
        for r in rows
    )

def page_shell(title, body_html):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%%TITLE%%</title>
<style>
:root { --bg: #0b1020; --surface: #0f172a; --card: #111827; --muted: #94a3b8; --text: #e5e7eb; --brand: #60a5fa; --brand2: #818cf8; --ok: #22c55e; --warn: #f59e0b; --err: #ef4444; }
* { box-sizing: border-box; }
body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; background: linear-gradient(180deg, #0b1020, #0b1020 200px, #0b1020); color: var(--text); }
.appbar { position: sticky; top: 0; background: linear-gradient(90deg, rgba(96,165,250,.15), rgba(129,140,248,.15)); border-bottom: 1px solid rgba(255,255,255,.05); backdrop-filter: blur(6px); }
.appbar-inner { max-width: 1100px; margin: 0 auto; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; }
.brand { font-weight: 800; font-size: 18px; letter-spacing: .3px; background: linear-gradient(90deg, var(--brand), var(--brand2)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.nav a { color: var(--muted); text-decoration: none; font-weight: 600; padding: 8px 10px; border-radius: 8px; }
.nav a:hover { color: #fff; background: rgba(255,255,255,.05); }
.container { max-width: 1100px; margin: 24px auto; padding: 0 16px; }
.hero { background: radial-gradient(1200px 300px at 20% -10%, rgba(96,165,250,.12), transparent), radial-gradient(900px 250px at 80% -10%, rgba(129,140,248,.12), transparent); padding: 18px 18px 6px; border-radius: 16px; border: 1px solid rgba(255,255,255,.06); }
.hero-title { font-size: 20px; font-weight: 700; margin: 0 0 6px; }
.hero-sub { color: var(--muted); margin: 0 0 2px; font-size: 13px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01)); border: 1px solid rgba(255,255,255,.06); border-radius: 14px; box-shadow: 0 10px 30px rgba(2,6,23,.35); padding: 16px; }
.section-title { font-size: 15px; font-weight: 700; margin: 0 0 12px; }
.data-table { width: 100%; border-collapse: collapse; border-radius: 10px; overflow: hidden; }
.data-table thead th { background: rgba(255,255,255,.04); color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .4px; font-size: 12px; }
.data-table th, .data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,.06); }
.data-table tbody tr:hover { background: rgba(255,255,255,.02); }
.badge { display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.status-Pending { color: var(--warn); background: rgba(245,158,11,.15); border: 1px solid rgba(245,158,11,.35); }
.status-SUCCESSFUL { color: var(--ok); background: rgba(34,197,94,.15); border: 1px solid rgba(34,197,94,.35); }
.status-NEEDFOLLOWUP { color: var(--warn); background: rgba(245,158,11,.15); border: 1px solid rgba(245,158,11,.35); }
.status-FAILED { color: var(--err); background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.35); }
.input, .select, .button, .file { width: 100%; font-size: 14px; padding: 12px 12px; border: 1px solid rgba(255,255,255,.12); border-radius: 10px; color: var(--text); background: rgba(255,255,255,.02); }
.file::-webkit-file-upload-button { border: 0; padding: 8px 10px; margin-right: 10px; border-radius: 8px; background: rgba(96,165,250,.15); color: #cfe5ff; cursor: pointer; }
.button { background: linear-gradient(90deg, var(--brand), var(--brand2)); border: none; cursor: pointer; color: #fff; font-weight: 700; letter-spacing: .2px; transition: transform .06s ease; }
.button:hover { transform: translateY(-1px); }
.button.secondary { background: linear-gradient(90deg, #0ea5e9, #22d3ee); }
.note { color: var(--muted); font-size: 12px; margin-top: 8px; }
.empty { text-align: center; padding: 30px 10px; color: var(--muted); }
.empty-icon { font-size: 28px; margin-bottom: 6px; }
.empty-title { font-weight: 800; margin-bottom: 4px; }
.table-wrap { overflow-x: auto; }
@media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
  <div class="appbar">
    <div class="appbar-inner">
      <div class="brand"><h1>Loan Collection VoiceBot</h1></div>
      <nav class="nav">
        <a href="/">Pending</a>
        <a href="/all">All Customers</a>
      </nav>
    </div>
  </div>
  <div class="container">
    %%BODY%%
  </div>
</body>
</html>"""
    return html.replace("%%TITLE%%", title).replace("%%BODY%%", body_html)

def render_home():
    pending = query_pending()
    make_call_options = render_customer_options(pending)
    pending_table = render_table(pending)
    body = f"""
    <div class="hero">
      <p class="hero-title">Pending Customers</p>
      <p class="hero-sub">Manage reminders and process voice notes to update statuses</p>
    </div>

    <div class="grid" style="margin-top:14px">
      <div class="card">
        <div class="section-title">Queue</div>
        {pending_table}
      </div>

      <div class="card">
        <div class="section-title">Local Pipeline Test — Voice Note → STT → DB Update → TTS</div>
        <form class="grid" method="POST" action="/upload" enctype="multipart/form-data">
          <input class="file" type="file" name="audio" accept="audio/wav" required />
          <select class="select" name="customer_id" required>
            {make_call_options}
          </select>
          <input class="input" type="text" name="fallback_transcript" placeholder="If STT is unavailable, enter transcript here" />
          <button class="button" type="submit">Process Upload</button>
        </form>
        <div class="note">Audio transcription and TTS require external packages. When unavailable, the fallback transcript is used.</div>
      </div>
    </div>

    <div class="card" style="margin-top:14px">
      <div class="section-title">Make Call</div>
      <form class="grid" method="POST" action="/make_call">
        <select class="select" name="customer_id" required>
          {make_call_options}
        </select>
        <button class="button secondary" type="submit">Make Call</button>
      </form>
      <div class="note">Calls require Twilio credentials. In this sandbox, a simulated call note is recorded.</div>
    </div>
    """
    return page_shell("Loan Collection VoiceBot — Pending", body)

def render_all_page():
    all_rows = query_all()
    all_table = render_table(all_rows)
    body = f"""
    <div class="hero">
      <p class="hero-title">All Customers (Updated)</p>
      <p class="hero-sub">Statuses reflect the latest processed voice notes and actions</p>
    </div>
    <div class="card" style="margin-top:14px">
      {all_table}
    </div>
    """
    return page_shell("Loan Collection VoiceBot — All Customers", body)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Only log errors to reduce spam
        if "error" in format.lower() or args and any("error" in str(arg).lower() for arg in args):
            print(f"HTTP: {format % args}")

    def _send(self, code=200, content=b"", content_type="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.wfile.write(content)

    def do_GET(self):
        try:
            if self.path == "/":
                self._send(200, render_home())
                return
                
            elif self.path == "/all":
                self._send(200, render_all_page())
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
                self._send(200, json.dumps(health, indent=2), "application/json; charset=utf-8")
                return
                
            elif self.path.startswith("/customers") or self.path.startswith("/api/customers"):
                data = query_all()
                self._send(200, json.dumps({"customers": data}, indent=2), "application/json; charset=utf-8")
                return
                
            else:
                self._send(404, """
                <html><body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a1a;color:#fff">
                <h1>404 - Page Not Found</h1>
                <p><a href="/" style="color:#60a5fa">Go Home</a></p>
                </body></html>
                """)
                
        except Exception as e:
            print(f"❌ GET Request error: {e}")
            traceback.print_exc()
            try:
                error_html = f"""
                <html><body style="font-family:Arial;padding:40px;background:#1a1a1a;color:#fff">
                <h1>500 - Server Error</h1>
                <pre style="background:#333;padding:20px;border-radius:5px;overflow:auto">{str(e)}</pre>
                <p><a href="/" style="color:#60a5fa">Go Home</a></p>
                </body></html>
                """
                self._send(500, error_html)
            except:
                pass

    def do_POST(self):
        try:
            if self.path == "/upload":
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type"),
                })
                customer_id = int(form.getfirst("customer_id", "0") or 0)
                fallback_transcript = form.getfirst("fallback_transcript", "").strip()
                audio_field = form.getfirst("audio")
                audio_saved_path = None
                if isinstance(audio_field, cgi.MiniFieldStorage):
                    pass
                else:
                    file_item = form["audio"] if "audio" in form else None
                    if file_item is not None and file_item.file and file_item.filename:
                        ts = int(time.time())
                        audio_saved_path = OUTPUT_DIR / f"uploaded_{ts}.wav"
                        with open(audio_saved_path, "wb") as f:
                            f.write(file_item.file.read())
                transcript = None
                if CALLER is not None and audio_saved_path is not None:
                    try:
                        transcript = CALLER.transcribe_audio(str(audio_saved_path))
                    except Exception:
                        transcript = None
                if transcript is None:
                    try:
                        import speech_recognition as sr  # optional
                        if audio_saved_path is not None:
                            r = sr.Recognizer()
                            with sr.AudioFile(str(audio_saved_path)) as source:
                                audio_data = r.record(source)
                                transcript = r.recognize_google(audio_data)
                    except Exception:
                        transcript = None
                if not transcript:
                    transcript = fallback_transcript or ""
                chosen_id = customer_id
                if not chosen_id:
                    pending = query_pending()
                    chosen_id = pending[0]["id"] if pending else None
                if AGENT is not None and chosen_id is not None:
                    try:
                        outcome = AGENT.process_customer(transcript, chosen_id)
                    except Exception:
                        outcome = classify_transcript(transcript)
                        DB.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])
                else:
                    outcome = classify_transcript(transcript)
                    if chosen_id is not None:
                        DB.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])
                self.send_response(302)
                self.send_header("Location", "/all")
                self.end_headers()
                return
            elif self.path == "/make_call":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                form = parse_qs(body)
                try:
                    customer_id = int(form.get("customer_id", [""])[0])
                except Exception:
                    self._send(400, "Invalid customer id")
                    return
                row = DB.con.execute("SELECT id,name,phone,due_date,loan_amount,call_status,notes FROM customers WHERE id=?", (customer_id,)).fetchone()
                if not row:
                    self._send(404, "Customer not found")
                    return
                c_id, name, phone, due_date, loan_amount, call_status, notes = row
                if CALLER is not None:
                    message = f"Hello {name}, this is a reminder for your loan payment of amount {loan_amount} due on {due_date}. Please pay as soon as possible. Thank you!"
                    sid = None
                    try:
                        sid = CALLER.make_call(to_number=str(phone), message=message)
                    except Exception:
                        sid = None
                    if sid:
                        note = (notes + "\n" if notes else "") + f"Twilio call initiated SID: {sid}"
                        DB.log_call_outcome(customer_id, call_status or "Pending", note)
                    else:
                        note = (notes + "\n" if notes else "") + "Call requested but Twilio call failed"
                        DB.log_call_outcome(customer_id, call_status or "Pending", note)
                else:
                    note = (notes + "\n" if notes else "") + "Call requested (Twilio not configured in this environment)"
                    DB.log_call_outcome(customer_id, call_status or "Pending", note)
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return
            elif self.path == "/update":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                form = parse_qs(body)
                try:
                    customer_id = int(form.get("customer_id", [""])[0])
                    status = form.get("status", [""])[0]
                    notes = form.get("notes", [""])[0]
                except Exception:
                    self._send(400, "Invalid form data")
                    return
                DB.log_call_outcome(customer_id, status, notes)
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return
            else:
                self._send(404, "Not Found")
                
        except Exception as e:
            print(f"❌ POST Request error: {e}")
            traceback.print_exc()
            try:
                self._send(500, json.dumps({"error": str(e)}), "application/json")
            except:
                pass

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