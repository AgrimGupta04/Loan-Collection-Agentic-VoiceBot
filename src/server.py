import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi
from pathlib import Path

PORT = int(os.environ.get("PORT", 8501))

from database import Database
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from caller_agent import CallerAgent
except Exception:
    CallerAgent = None
try:
    from outcome_agent import Outcome_agent
except Exception:
    Outcome_agent = None

DB_PATH = "customers.db"
PORT = 8501
OUTPUT_DIR = Path("demo_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Ensure DB exists and seeded
_ = Database(DB_PATH)

CALLER = None
AGENT = None
if 'CallerAgent' in globals() and CallerAgent is not None:
    try:
        CALLER = CallerAgent(use_groq=True)
    except Exception:
        CALLER = None
if 'Outcome_agent' in globals() and Outcome_agent is not None:
    try:
        AGENT = Outcome_agent(use_groq=True)
    except Exception:
        AGENT = None


def classify_transcript(transcript: str) -> dict:
    t = (transcript or "").lower().strip()

    import re
    neg_pattern_1 = re.search(r"\b(not|no|never|won['’]t|cannot|can['’]t|don['’]t|dont|unable)\b.*\bpay\b", t)
    neg_pattern_2 = re.search(r"\bpay\b.*\b(not|no|never|won['’]t|cannot|can['’]t|don['’]t|dont|unable)\b", t)
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


def query_all(db: Database):
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


def query_pending(db: Database):
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


def render_table(rows):
    if not rows:
        return """
        <div class=\"empty\">
          <div class=\"empty-icon\">🗂️</div>
          <div class=\"empty-title\">No records</div>
          <div class=\"empty-sub\">Everything looks up to date</div>
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
          <td><span class=\"badge status status-{r['call_status'].replace(' ', '')}\">{r['call_status']}</span></td>
          <td>{(r['notes'] or '')}</td>
        </tr>
        """
        for r in rows
    )
    return f"""
    <div class=\"table-wrap\">\n      <table class=\"data-table\">\n        <thead><tr>\n          <th>ID</th><th>Name</th><th>Phone</th><th>Due Date</th><th>Loan</th><th>Status</th><th>Notes</th>\n        </tr></thead>\n        <tbody>{body}</tbody>\n      </table>\n    </div>\n    """


def render_customer_options(rows):
    return "".join(
        f"<option value=\"{r['id']}\">#{r['id']} — {r['name']} — ₹{r['loan_amount']} due {r['due_date']}</option>"
        for r in rows
    )


def page_shell(title, body_html):
    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
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


def render_home(db: Database):
    pending = query_pending(db)
    all_rows = query_all(db)
    pending_table = render_table(pending)
    make_call_options = render_customer_options(pending or all_rows)
    body = f"""
    <div class=\"hero\">\n      <p class=\"hero-title\">Pending Customers</p>\n      <p class=\"hero-sub\">Manage reminders and process voice notes to update statuses</p>\n    </div>\n
    <div class=\"grid\" style=\"margin-top:14px\">\n      <div class=\"card\">\n        <div class=\"section-title\">Queue</div>\n        {pending_table}\n      </div>\n
      <div class=\"card\">\n        <div class=\"section-title\">Local Pipeline Test — Voice Note → STT → DB Update → TTS</div>\n        <form class=\"grid\" method=\"POST\" action=\"/upload\" enctype=\"multipart/form-data\">\n          <input class=\"file\" type=\"file\" name=\"audio\" accept=\"audio/wav\" required />\n          <select class=\"select\" name=\"customer_id\" required>\n            {make_call_options}\n          </select>\n          <input class=\"input\" type=\"text\" name=\"fallback_transcript\" placeholder=\"If STT is unavailable, enter transcript here\" />\n          <button class=\"button\" type=\"submit\">Process Upload</button>\n        </form>\n        <div class=\"note\">Audio transcription and TTS require external packages. When unavailable, the fallback transcript is used.</div>\n      </div>\n    </div>\n
    <div class=\"card\" style=\"margin-top:14px\">\n      <div class=\"section-title\">Make Call</div>\n      <form class=\"grid\" method=\"POST\" action=\"/make_call\">\n        <select class=\"select\" name=\"customer_id\" required>\n          {make_call_options}\n        </select>\n        <button class=\"button secondary\" type=\"submit\">Make Call</button>\n      </form>\n      <div class=\"note\">Calls require Twilio credentials. In this sandbox, a simulated call note is recorded.</div>\n    </div>\n    """
    return page_shell("Loan Collection VoiceBot — Pending", body)


def render_all_page(db: Database):
    all_rows = query_all(db)
    all_table = render_table(all_rows)
    body = f"""
    <div class=\"hero\">\n      <p class=\"hero-title\">All Customers (Updated)</p>\n      <p class=\"hero-sub\">Statuses reflect the latest processed voice notes and actions</p>\n    </div>\n    <div class=\"card\" style=\"margin-top:14px\">\n      {all_table}\n    </div>\n    """
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

    def do_GET(self):
        if self.path == "/":
            db = Database(DB_PATH)
            self._send(200, render_home(db))
            return
        if self.path == "/all":
            db = Database(DB_PATH)
            self._send(200, render_all_page(db))
            return
        if self.path.startswith("/customers"):
            db = Database(DB_PATH)
            data = query_all(db)
            self._send(200, json.dumps(data), "application/json; charset=utf-8")
            return
        self._send(404, "Not Found")

    def do_POST(self):
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
            if 'CALLER' in globals() and CALLER is not None and audio_saved_path is not None:
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

            db = Database(DB_PATH)
            chosen_id = customer_id
            if not chosen_id:
                pending = query_pending(db)
                chosen_id = pending[0]["id"] if pending else None

            if 'AGENT' in globals() and AGENT is not None and chosen_id is not None:
                try:
                    outcome = AGENT.process_customer(transcript, chosen_id)
                except Exception:
                    outcome = classify_transcript(transcript)
                    db.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])
            else:
                outcome = classify_transcript(transcript)
                if chosen_id is not None:
                    db.log_call_outcome(chosen_id, outcome["status"], outcome["notes"])

            self.send_response(302)
            self.send_header("Location", "/all")
            self.end_headers()
            return

        if self.path == "/make_call":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            form = parse_qs(body)
            try:
                customer_id = int(form.get("customer_id", [""])[0])
            except Exception:
                self._send(400, "Invalid customer id")
                return
            db = Database(DB_PATH)
            row = db.con.execute("SELECT id,name,phone,due_date,loan_amount,call_status,notes FROM customers WHERE id=?", (customer_id,)).fetchone()
            if not row:
                self._send(404, "Customer not found")
                return
            c_id, name, phone, due_date, loan_amount, call_status, notes = row

            if 'CALLER' in globals() and CALLER is not None:
                message = f"Hello {name}, this is a reminder for your loan payment of amount {loan_amount} due on {due_date}. Please pay as soon as possible. Thank you!"
                sid = None
                try:
                    sid = CALLER.make_call(to_number=str(phone), message=message)
                except Exception:
                    sid = None
                if sid:
                    note = (notes + "\n" if notes else "") + f"Twilio call initiated SID: {sid}"
                    db.log_call_outcome(customer_id, call_status or "Pending", note)
                else:
                    note = (notes + "\n" if notes else "") + "Call requested but Twilio call failed"
                    db.log_call_outcome(customer_id, call_status or "Pending", note)
            else:
                note = (notes + "\n" if notes else "") + "Call requested (Twilio not configured in this environment)"
                db.log_call_outcome(customer_id, call_status or "Pending", note)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/update":
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

            db = Database(DB_PATH)
            db.log_call_outcome(customer_id, status, notes)
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        self._send(404, "Not Found")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
