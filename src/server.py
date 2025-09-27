import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi
from pathlib import Path

# Fix PORT variable - Railway uses 8000, not 8501
PORT = int(os.environ.get("PORT", 8000))

# Import with better error handling
DB_AVAILABLE = False
CALLER_AVAILABLE = False
AGENT_AVAILABLE = False

try:
    from database import Database
    DB_AVAILABLE = True
    print("✓ Database module imported successfully")
except Exception as e:
    print(f"✗ Database import failed: {e}")
    Database = None

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Environment variables loaded")
except Exception as e:
    print(f"Note: dotenv not available: {e}")

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

DB_PATH = "customers.db"
OUTPUT_DIR = Path("demo_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize components safely
DB = None
CALLER = None
AGENT = None

if DB_AVAILABLE:
    try:
        DB = Database(DB_PATH)
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        DB = None

if CALLER_AVAILABLE and CallerAgent:
    try:
        CALLER = CallerAgent(use_groq=True)
        print("✓ CallerAgent initialized")
    except Exception as e:
        print(f"Note: CallerAgent initialization failed: {e}")
        CALLER = None

if AGENT_AVAILABLE and Outcome_agent:
    try:
        AGENT = Outcome_agent(use_groq=True)
        print("✓ Outcome_agent initialized")
    except Exception as e:
        print(f"Note: Outcome_agent initialization failed: {e}")
        AGENT = None


def classify_transcript(transcript: str) -> dict:
    """Fallback classification when agent is not available"""
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


def query_all(db):
    """Query all customers with error handling"""
    if not db:
        return []
    try:
        rows = db.con.execute("SELECT * FROM customers").fetchall()
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
        print(f"Error querying all customers: {e}")
        return []


def query_pending(db):
    """Query pending customers with error handling"""
    if not db:
        return []
    try:
        rows = db.fetch_due_customers()
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
        print(f"Error querying pending customers: {e}")
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
.status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.status-indicator.ok { background: var(--ok); }
.status-indicator.warn { background: var(--warn); }
.status-indicator.err { background: var(--err); }
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
        <a href="/health">Health</a>
      </nav>
    </div>
  </div>
  <div class="container">
    %%BODY%%
  </div>
</body>
</html>"""
    return html.replace("%%TITLE%%", title).replace("%%BODY%%", body_html)


def render_health_page():
    """Health check page showing component status"""
    components = [
        ("Database", DB is not None, "✓" if DB else "✗"),
        ("CallerAgent", CALLER is not None, "✓" if CALLER else "✗"),
        ("OutcomeAgent", AGENT is not None, "✓" if AGENT else "✗"),
    ]
    
    status_rows = "".join([
        f"""
        <tr>
          <td>{name}</td>
          <td><span class="status-indicator {'ok' if status else 'err'}"></span>{icon}</td>
          <td>{'Available' if status else 'Not Available'}</td>
        </tr>
        """
        for name, status, icon in components
    ])
    
    overall_status = "Healthy" if DB else "Limited"
    
    body = f"""
    <div class="hero">
      <p class="hero-title">System Health Check</p>
      <p class="hero-sub">Overall Status: {overall_status}</p>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="section-title">Component Status</div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr>
            <th>Component</th><th>Status</th><th>Details</th>
          </tr></thead>
          <tbody>{status_rows}</tbody>
        </table>
      </div>
    </div>
    """
    return page_shell("Loan Collection VoiceBot — Health Check", body)


def render_home():
    """Render home page with error handling"""
    if not DB:
        body = """
        <div class="hero">
          <p class="hero-title">Database Not Available</p>
          <p class="hero-sub">Database connection failed - running in limited mode</p>
        </div>
        <div class="card">
          <div class="section-title">Status</div>
          <p>The application is running but database functionality is not available.</p>
        </div>
        """
        return page_shell("Loan Collection VoiceBot — Limited Mode", body)

    pending = query_pending(DB)
    all_rows = query_all(DB)
    pending_table = render_table(pending)
    make_call_options = render_customer_options(pending or all_rows)
    
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
    """Render all customers page with error handling"""
    if not DB:
        return render_home()  # Fallback to home page if DB not available
        
    all_rows = query_all(DB)
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
    def _send(self, code=200, content=b"", content_type="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Reduce log noise for health checks
        pass

    def do_GET(self):
        if self.path == "/":
            self._send(200, render_home())
            return
        if self.path == "/health":
            # Simple health check that Railway can use
            health_data = {
                "status": "healthy" if DB else "limited",
                "database": DB is not None,
                "caller_agent": CALLER is not None,
                "outcome_agent": AGENT is not None
            }
            self._send(200, json.dumps(health_data), "application/json")
            return
        if self.path == "/all":
            self._send(200, render_all_page())
            return
        if self.path.startswith("/customers"):
            if not DB:
                self._send(503, json.dumps({"error": "Database not available"}), "application/json")
                return
            data = query_all(DB)
            self._send(200, json.dumps(data), "application/json; charset=utf-8")
            return
        self._send(404, "Not Found")

    def do_POST(self):
        if self.path == "/upload":
            if not DB:
                self._send(503, "Database not available")
                return
                
            try:
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type"),
                })
                customer_id = int(form.getfirst("customer_id", "0") or 0)
                fallback_transcript = form.getfirst("fallback_transcript", "").strip()
                
                # Handle file upload
                audio_saved_path = None
                if "audio" in form:
                    file_item = form["audio"]
                    if hasattr(file_item, 'file') and file_item.file and hasattr(file_item, 'filename') and file_item.filename:
                        ts = int(time.time())
                        audio_saved_path = OUTPUT_DIR / f"uploaded_{ts}.wav"
                        with open(audio_saved_path, "wb") as f:
                            f.write(file_item.file.read())

                # Try transcription
                transcript = None
                if CALLER and audio_saved_path:
                    try:
                        transcript = CALLER.transcribe_audio(str(audio_saved_path))
                    except Exception as e:
                        print(f"CallerAgent transcription failed: {e}")

                # Fallback to Google STT
                if transcript is None and audio_saved_path:
                    try:
                        import speech_recognition as sr
                        r = sr.Recognizer()
                        with sr.AudioFile(str(audio_saved_path)) as source:
                            audio_data = r.record(source)
                            transcript = r.recognize_google(audio_data)
                    except Exception as e:
                        print(f"Google STT failed: {e}")

                # Use fallback transcript if all else fails
                if not transcript:
                    transcript = fallback_transcript or "Unable to transcribe audio"

                # Process outcome
                chosen_id = customer_id
                if not chosen_id:
                    pending = query_pending(DB)
                    chosen_id = pending[0]["id"] if pending else None

                if chosen_id:
                    if AGENT:
                        try:
                            outcome = AGENT.process_customer(transcript, chosen_id)
                        except Exception as e:
                            print(f"Agent processing failed: {e}")
                            outcome = classify_transcript(transcript)
                            DB.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])
                    else:
                        outcome = classify_transcript(transcript)
                        DB.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])

            except Exception as e:
                print(f"Upload processing error: {e}")

            self.send_response(302)
            self.send_header("Location", "/all")
            self.end_headers()
            return

        if self.path == "/make_call":
            if not DB:
                self._send(503, "Database not available")
                return
                
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                form = parse_qs(body)
                customer_id = int(form.get("customer_id", [""])[0])
                
                row = DB.con.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
                if not row:
                    self._send(404, "Customer not found")
                    return
                
                c_id, name, phone, due_date, loan_amount, call_status, notes = row

                if CALLER:
                    message = f"Hello {name}, this is a reminder for your loan payment of amount {loan_amount} due on {due_date}. Please pay as soon as possible. Thank you!"
                    try:
                        sid = CALLER.make_call(to_number=str(phone), message=message)
                        if sid:
                            note = (notes + "\n" if notes else "") + f"Twilio call initiated SID: {sid}"
                        else:
                            note = (notes + "\n" if notes else "") + "Call requested but Twilio call failed"
                    except Exception as e:
                        note = (notes + "\n" if notes else "") + f"Call failed: {e}"
                else:
                    note = (notes + "\n" if notes else "") + "Call requested (Twilio not configured in this environment)"
                
                DB.log_call_outcome(customer_id, call_status or "Pending", note)
                
            except Exception as e:
                print(f"Make call error: {e}")

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        self._send(404, "Not Found")


if __name__ == "__main__":
    print(f"Starting server on port {PORT}")
    print(f"Database available: {DB is not None}")
    print(f"CallerAgent available: {CALLER is not None}")
    print(f"OutcomeAgent available: {AGENT is not None}")
    
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✓ Server ready at http://0.0.0.0:{PORT}")
    print(f"✓ Health check available at http://0.0.0.0:{PORT}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()
        print("Server stopped.")