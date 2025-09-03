#!/usr/bin/env python3
"""
VPN Request & Coordination Portal — Single File (app.py)
-------------------------------------------------------

WHAT THIS FILE DOES
- Presents an initial "New VPN Request" form (VPN name/vendor, type: Policy/Routed,
  reason, remote contact, local team emails).
- Emails unique tokenized links to the Remote contact and Local network team.
- Remote and Local each fill their own detailed form (gateway, IKE, crypto, DH group,
  PSK, protected subnets, notes).
- When both sides submit, a Review/Agreement email is sent; each side can Review and
  either Agree or Edit their side. Both must Agree to finalize.
- Final summary email is sent to both sides when both agree.

QUICK START (local)
1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install flask sqlalchemy
4) export BASE_URL="http://localhost:5000"         # recommended for correct links
5) python app.py
6) open http://127.0.0.1:5000

ENVIRONMENT VARIABLES
- BASE_URL: Public base URL (default http://localhost:5000)
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM (optional) — if not configured, email bodies will print to console.

SECURITY NOTES
- Tokens are unguessable UUIDs but treat links as sensitive.
- PSKs are stored in plaintext for demo simplicity — do NOT use this as-is in production. Use KMS/vault & encryption at rest.
- Use HTTPS in production; add authentication / allowlists / rate limiting as needed.

Author: ChatGPT (regenerated full file on user request)
"""

import os
import json
import uuid
from urllib.parse import urljoin

from flask import (
    Flask, request, redirect, url_for,
    render_template_string, abort, flash
)
from flask_sqlalchemy import SQLAlchemy
from email.mime.text import MIMEText
import smtplib

# -------------------------
# Configuration
# -------------------------
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25")) if os.environ.get("SMTP_PORT") else None
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "vpn-portal@noreply.local")

# Flask app + DB
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vpn_portal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
db = SQLAlchemy(app)


# -------------------------
# Database model
# -------------------------
class VPNRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String, nullable=False)
    vpn_name = db.Column(db.String(200), nullable=False)
    vpn_type = db.Column(db.String(20), nullable=False)  # Policy / Routed
    reason = db.Column(db.Text, nullable=False)
    requester_name = db.Column(db.String(120))
    requester_email = db.Column(db.String(120))

    remote_contact_name = db.Column(db.String(200), nullable=False)
    remote_contact_email = db.Column(db.String(200), nullable=False)
    local_team_email = db.Column(db.String(200), nullable=False)  # can be comma separated

    remote_token = db.Column(db.String(64), unique=True, nullable=False)
    local_token = db.Column(db.String(64), unique=True, nullable=False)

    status = db.Column(db.String(40), default="awaiting_details")  # awaiting_details | awaiting_agreement | complete | cancelled
    remote_agreed = db.Column(db.Boolean, default=False)
    local_agreed = db.Column(db.Boolean, default=False)

    # JSON blobs for each side
    remote_data = db.Column(db.Text)  # JSON
    local_data = db.Column(db.Text)   # JSON


with app.app_context():
    db.create_all()

# -------------------------
# Shared CSS + Header HTML
# -------------------------
BASE_CSS = """
<style>
:root{--bg:#f6f8fb;--card:#fff;--muted:#64748b;--accent:#2563eb}
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial; background:var(--bg); margin:0;color:#0f172a}
.header{background:linear-gradient(90deg,#0f172a,#091226);color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}
.header h1{margin:0;font-size:1.05rem}
.header .subtitle{color:#cbd5e1;font-size:.92rem}
.container{max-width:1000px;margin:22px auto;padding:0 16px}
.card{background:var(--card);border-radius:12px;padding:18px;border:1px solid #e6eef8;box-shadow:0 10px 30px rgba(11,20,34,0.05)}
.form-grid label{display:block;margin:10px 0 6px;font-weight:600}
input[type="text"], input[type="email"], select, textarea{width:100%;padding:10px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:1rem;background:#fff}
textarea{min-height:84px;resize:vertical}
.actions{margin-top:14px;display:flex;gap:10px;align-items:center}
.btn{background:var(--accent);color:#fff;padding:10px 14px;border-radius:8px;border:0;font-weight:700;cursor:pointer}
.btn.secondary{background:#e2e8f0;color:#0f172a}
.hint{color:var(--muted);font-size:.95rem;margin-top:8px}
.grid-two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.kv{width:100%;border-collapse:collapse;margin-top:8px}
.kv th,.kv td{padding:8px;border-bottom:1px solid #f1f5f9;text-align:left;vertical-align:top;font-size:.95rem}
.pretty{background:#fbfdff;padding:12px;border-radius:8px;border:1px solid #e6eef8}
@media (max-width:900px){.grid-two{grid-template-columns:1fr}}
small.muted{color:var(--muted)}
.flash{margin-bottom:12px}
.flash .success{background:#ecfdf5;border:1px solid #a7f3d0;padding:8px;border-radius:8px}
.flash .error{background:#fff1f2;border:1px solid #fecaca;padding:8px;border-radius:8px}
</style>
"""

HEADER_HTML = f"""
<header class="header">
  <div>
    <h1>VPN Request & Coordination Portal</h1>
    <div class="subtitle">Create site-to-site VPN requests, gather remote/local details, review and get mutual agreement.</div>
  </div>
  <div style="text-align:right; display: flex; gap: 12px; align-items: center;">
    <a href="/admin" style="color: #cbd5e1; text-decoration: none; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.1);">Admin Panel</a>
    <small class="muted">Single-file demo — set BASE_URL env var for correct links</small>
  </div>
</header>
"""

# -------------------------
# Email helper (fallback prints)
# -------------------------
def send_email(to_addrs, subject, body):
    """
    Sends email via configured SMTP if present; otherwise prints to console.
    `to_addrs` may be a string or list.
    """
    if isinstance(to_addrs, str):
        to = [to_addrs]
    else:
        to = to_addrs

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(to)

    # If SMTP_HOST is empty, fallback to printing
    if not SMTP_HOST:
        print("\n--- EMAIL FALLBACK (no SMTP configured) ---")
        print("To:", msg["To"])
        print("Subject:", subject)
        print("Body:\n", body)
        print("--- end email ---\n")
        return

    try:
        import smtplib
        port = SMTP_PORT or 25
        with smtplib.SMTP(SMTP_HOST, port) as s:
            if SMTP_USER and SMTP_PASS:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_FROM, to, msg.as_string())
        print(f"[email] sent to {to}")
    except Exception as e:
        print("[email] send failed — printing fallback. Error:", e)
        print("\n--- EMAIL FALLBACK ---")
        print("To:", msg["To"])
        print("Subject:", subject)
        print("Body:\n", body)
        print("--- end email ---\n")


# -------------------------
# Utility: render base template wrapper
# -------------------------
BASE_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>VPN Portal</title>
    {{ css|safe }}
  </head>
  <body>
    {{ header|safe }}
    <div class="container">
      {% with messages = messages %}
        {% if messages %}
          <div class="flash">
            {% for cat, msg in messages %}
              <div class="{{ 'success' if cat=='success' else 'error' }}">{{ msg }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}
      <div class="card">
        {{ content|safe }}
      </div>
      <div style="height:24px"></div>
    </div>
  </body>
</html>
"""


def render_page(content_html, messages=None):
    if messages is None:
        messages = []
    return render_template_string(BASE_TEMPLATE,
                                  css=BASE_CSS,
                                  header=HEADER_HTML,
                                  content=content_html,
                                  messages=messages)


# -------------------------
# Routes
# -------------------------
from datetime import datetime


@app.route("/")
def index():
    content = """
      <h2>New VPN Request</h2>
      <form method="post" action="/request/new" class="form-grid">
        <label>VPN Name / Vendor</label>
        <input type="text" name="vpn_name" required>

        <label>VPN Type</label>
        <select name="vpn_type" required>
          <option value="Policy">Policy</option>
          <option value="Routed">Routed</option>
        </select>

        <label>Reason / Business Justification</label>
        <textarea name="reason" required></textarea>

        <label>Your Name (optional)</label>
        <input type="text" name="requester_name" placeholder="Requester name">

        <label>Your Email (optional)</label>
        <input type="email" name="requester_email" placeholder="you@example.com">

        <label>Remote Contact Name</label>
        <input type="text" name="remote_contact_name" required>

        <label>Remote Contact Email</label>
        <input type="email" name="remote_contact_email" required>

        <label>Local Network Team Email (group or comma-separated)</label>
        <input type="text" name="local_team_email" required>

        <div class="actions">
          <button class="btn" type="submit">Submit Request</button>
          <button class="btn secondary" type="reset">Reset</button>
        </div>

        <p class="hint">After submission, unique links will be emailed to remote & local contacts to provide their side's details.</p>
      </form>
    """
    return render_page(content)


@app.route("/request/new", methods=["POST"])
def request_new():
    # Collect initial form
    vpn_name = request.form.get("vpn_name", "").strip()
    vpn_type = request.form.get("vpn_type", "").strip()
    reason = request.form.get("reason", "").strip()
    requester_name = request.form.get("requester_name", "").strip()
    requester_email = request.form.get("requester_email", "").strip()
    remote_contact_name = request.form.get("remote_contact_name", "").strip()
    remote_contact_email = request.form.get("remote_contact_email", "").strip()
    local_team_email = request.form.get("local_team_email", "").strip()

    if not (vpn_name and vpn_type and reason and remote_contact_email and local_team_email):
        return render_page("<p class='hint'>Missing required fields.</p>", messages=[("error", "Missing required fields.")])

    remote_token = uuid.uuid4().hex
    local_token = uuid.uuid4().hex

    vpn = VPNRequest(
        created_at=datetime.utcnow().isoformat(),
        vpn_name=vpn_name,
        vpn_type=vpn_type,
        reason=reason,
        requester_name=requester_name,
        requester_email=requester_email,
        remote_contact_name=remote_contact_name,
        remote_contact_email=remote_contact_email,
        local_team_email=local_team_email,
        remote_token=remote_token,
        local_token=local_token,
        status="awaiting_details"
    )
    db.session.add(vpn)
    db.session.commit()

    # Build links
    remote_link = urljoin(BASE_URL, f"/remote/{remote_token}")
    local_link = urljoin(BASE_URL, f"/local/{local_token}")

    # Send invites
    send_email(
        remote_contact_email,
        f"[VPN Portal] Please provide remote details for '{vpn_name}'",
        f"<p>Hello {remote_contact_name or ''},</p>"
        f"<p>Please provide your side's VPN details here: <a href='{remote_link}'>{remote_link}</a></p>"
        f"<p>Reason: {reason}</p>"
    )

    # local_team_email may be comma separated
    for addr in [a.strip() for a in local_team_email.split(",") if a.strip()]:
        send_email(
            addr,
            f"[VPN Portal] Please provide local details for '{vpn_name}'",
            f"<p>Please provide your local VPN details here: <a href='{local_link}'>{local_link}</a></p>"
            f"<p>Reason: {reason}</p>"
        )

    content = f"""
      <h2>Request Submitted</h2>
      <p>Request <strong>{vpn_name}</strong> has been recorded.</p>
      <p>Unique links were emailed to:</p>
      <ul>
        <li>Remote contact: <em>{remote_contact_email}</em></li>
        <li>Local team: <em>{local_team_email}</em></li>
      </ul>
      <p class="hint">Both sides can update their forms until both agree.</p>
    """
    return render_page(content, messages=[("success", "Request created and emails sent (or printed).")])


# -------------------------
# Helper to get by token
# -------------------------
def get_request_by_token(token, side):
    if side == "remote":
        return VPNRequest.query.filter_by(remote_token=token).first()
    else:
        return VPNRequest.query.filter_by(local_token=token).first()


# -------------------------
# Side form rendering
# -------------------------
SIDE_FORM_TEMPLATE = """
<h2>{{ title }}</h2>
<form method="post">
  <label>Company / Engineer Name</label>
  <input type="text" name="contact_name" value="{{ data.get('contact_name','') }}">

  <label>Contact Email</label>
  <input type="email" name="contact_email" value="{{ data.get('contact_email','') }}">

  <label>Gateway Public IP / FQDN</label>
  <input type="text" name="gateway" value="{{ data.get('gateway','') }}" required>

  <label>IKE Version</label>
  <input type="text" name="ike_version" value="{{ data.get('ike_version','') }}" placeholder="e.g. IKEv2">

  <label>Encryption (phase1/phase2)</label>
  <input type="text" name="encryption" value="{{ data.get('encryption','') }}" placeholder="e.g. AES256/AES256">

  <label>Hashing</label>
  <input type="text" name="hashing" value="{{ data.get('hashing','') }}" placeholder="e.g. SHA256">

  <label>DH Group</label>
  <input type="text" name="dh_group" value="{{ data.get('dh_group','') }}" placeholder="e.g. 14, 19">

  <label>Protected Subnets (comma-separated CIDRs)</label>
  <textarea name="subnets">{{ data.get('subnets','') }}</textarea>

  <label>Notes</label>
  <textarea name="notes">{{ data.get('notes','') }}</textarea>

  <div class="actions">
    <button class="btn" type="submit">Save</button>
    <a class="btn secondary" href="/">Home</a>
  </div>
  <p class="hint">You can return later using the link in your email to update your details until both parties agree.</p>
</form>
"""


@app.route("/remote/<token>", methods=["GET", "POST"])
def remote_form(token):
    vpn = get_request_by_token(token, "remote")
    if not vpn:
        abort(404)
    
    if vpn.status == "cancelled":
        content = """
          <h2>Request Cancelled</h2>
          <p>This VPN request has been cancelled by an administrator.</p>
          <p>No further processing is possible for this request.</p>
          <p class="hint">If you believe this is an error, please contact your system administrator.</p>
        """
        return render_page(content)

    # pre-fill if remote_data present
    data = {}
    if vpn.remote_data:
        try:
            data = json.loads(vpn.remote_data)
        except Exception:
            data = {}

    if request.method == "POST":
        # Collect only fields for remote side
        data = {
            "contact_name": request.form.get("contact_name", "").strip(),
            "contact_email": request.form.get("contact_email", "").strip(),
            "gateway": request.form.get("gateway", "").strip(),
            "ike_version": request.form.get("ike_version", "").strip(),
            "encryption": request.form.get("encryption", "").strip(),
            "hashing": request.form.get("hashing", "").strip(),
            "dh_group": request.form.get("dh_group", "").strip(),
            "subnets": request.form.get("subnets", "").strip(),
            "notes": request.form.get("notes", "").strip(),
        }
        vpn.remote_data = json.dumps(data)
        db.session.commit()

        # maybe transition to agreement
        maybe_transition_to_agreement(vpn)

        return render_page("<p class='hint'>Remote details saved. You may close this page.</p>", messages=[("success", "Remote details saved.")])

    return render_page(render_template_string(SIDE_FORM_TEMPLATE, title=f"Remote Side — {vpn.vpn_name}", data=data))


@app.route("/local/<token>", methods=["GET", "POST"])
def local_form(token):
    vpn = get_request_by_token(token, "local")
    if not vpn:
        abort(404)
    
    if vpn.status == "cancelled":
        content = """
          <h2>Request Cancelled</h2>
          <p>This VPN request has been cancelled by an administrator.</p>
          <p>No further processing is possible for this request.</p>
          <p class="hint">If you believe this is an error, please contact your system administrator.</p>
        """
        return render_page(content)

    data = {}
    if vpn.local_data:
        try:
            data = json.loads(vpn.local_data)
        except Exception:
            data = {}

    if request.method == "POST":
        data = {
            "contact_name": request.form.get("contact_name", "").strip(),
            "contact_email": request.form.get("contact_email", "").strip(),
            "gateway": request.form.get("gateway", "").strip(),
            "ike_version": request.form.get("ike_version", "").strip(),
            "encryption": request.form.get("encryption", "").strip(),
            "hashing": request.form.get("hashing", "").strip(),
            "dh_group": request.form.get("dh_group", "").strip(),
            "subnets": request.form.get("subnets", "").strip(),
            "notes": request.form.get("notes", "").strip(),
        }
        vpn.local_data = json.dumps(data)
        db.session.commit()

        maybe_transition_to_agreement(vpn)

        return render_page("<p class='hint'>Local details saved. You may close this page.</p>", messages=[("success", "Local details saved.")])

    return render_page(render_template_string(SIDE_FORM_TEMPLATE, title=f"Local Side — {vpn.vpn_name}", data=data))


# -------------------------
# When both sides have at least some details, email review links
# -------------------------
def maybe_transition_to_agreement(vpn_req):
    if vpn_req.status == "cancelled":
        return  # Don't process cancelled requests
    
    if vpn_req.remote_data and vpn_req.local_data and vpn_req.status == "awaiting_details":
        vpn_req.status = "awaiting_agreement"
        db.session.commit()

        # send review links to both sides
        base = BASE_URL.rstrip("/")
        remote_review = urljoin(base + "/", f"agree/{vpn_req.remote_token}")
        local_review = urljoin(base + "/", f"agree/{vpn_req.local_token}")

        # email remote
        send_email(
            vpn_req.remote_contact_email,
            f"[VPN Portal] Review & Agree — {vpn_req.vpn_name}",
            f"<p>Both sides have submitted details for <strong>{vpn_req.vpn_name}</strong>.</p>"
            f"<p>Please review and either Agree or Edit using this link: <a href='{remote_review}'>{remote_review}</a></p>"
        )
        # email local team (may be comma list)
        for addr in [a.strip() for a in vpn_req.local_team_email.split(",") if a.strip()]:
            send_email(
                addr,
                f"[VPN Portal] Review & Agree — {vpn_req.vpn_name}",
                f"<p>Both sides have submitted details for <strong>{vpn_req.vpn_name}</strong>.</p>"
                f"<p>Please review and either Agree or Edit using this link: <a href='{local_review}'>{local_review}</a></p>"
            )


# -------------------------
# Agreement / Review page
# -------------------------
REVIEW_TEMPLATE = """
<h2>Review & Agree — {{ vpn.vpn_name }}</h2>
<p><small class="muted">Status: {{ vpn.status }}</small></p>
<div class="grid-two">
  <div>
    <h3>Local Side</h3>
    {% if local %}
      <table class="kv">
        <tr><th>Contact</th><td>{{ local.contact_name }} &lt;{{ local.contact_email }}&gt;</td></tr>
        <tr><th>Gateway</th><td>{{ local.gateway }}</td></tr>
        <tr><th>IKE</th><td>{{ local.ike_version }}</td></tr>
        <tr><th>Encryption</th><td>{{ local.encryption }}</td></tr>
        <tr><th>Hashing</th><td>{{ local.hashing }}</td></tr>
        <tr><th>DH Group</th><td>{{ local.dh_group }}</td></tr>
        <tr><th>Subnets</th><td>{{ local.subnets }}</td></tr>
        <tr><th>Notes</th><td>{{ local.notes }}</td></tr>
      </table>
    {% else %}
      <p class="hint">Awaiting local details.</p>
    {% endif %}
  </div>
  <div>
    <h3>Remote Side</h3>
    {% if remote %}
      <table class="kv">
        <tr><th>Contact</th><td>{{ remote.contact_name }} &lt;{{ remote.contact_email }}&gt;</td></tr>
        <tr><th>Gateway</th><td>{{ remote.gateway }}</td></tr>
        <tr><th>IKE</th><td>{{ remote.ike_version }}</td></tr>
        <tr><th>Encryption</th><td>{{ remote.encryption }}</td></tr>
        <tr><th>Hashing</th><td>{{ remote.hashing }}</td></tr>
        <tr><th>DH Group</th><td>{{ remote.dh_group }}</td></tr>
        <tr><th>Subnets</th><td>{{ remote.subnets }}</td></tr>
        <tr><th>Notes</th><td>{{ remote.notes }}</td></tr>
      </table>
    {% else %}
      <p class="hint">Awaiting remote details.</p>
    {% endif %}
  </div>
</div>

<form method="post" style="margin-top:12px">
  <div class="actions">
    <button class="btn" name="action" value="agree" type="submit">Agree</button>
    <button class="btn secondary" name="action" value="edit" type="submit">Edit My Info</button>
  </div>
  <p class="hint">Selecting Edit will take you back to your form pre-filled with your previously saved values.</p>
</form>
"""

@app.route("/agree/<token>", methods=["GET", "POST"])
def agree(token):
    # Find request by either token
    vpn = VPNRequest.query.filter((VPNRequest.remote_token == token) | (VPNRequest.local_token == token)).first()
    if not vpn:
        abort(404)
    
    if vpn.status == "cancelled":
        content = """
          <h2>Request Cancelled</h2>
          <p>This VPN request has been cancelled by an administrator.</p>
          <p>No further processing is possible for this request.</p>
          <p class="hint">If you believe this is an error, please contact your system administrator.</p>
        """
        return render_page(content)

    # determine which side this token belongs to
    side = "remote" if vpn.remote_token == token else "local"

    # parse JSON blobs to dicts
    remote = {}
    local = {}
    try:
        remote = json.loads(vpn.remote_data) if vpn.remote_data else {}
    except:
        remote = {}
    try:
        local = json.loads(vpn.local_data) if vpn.local_data else {}
    except:
        local = {}

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "edit":
            # redirect to the appropriate form so the values get prefilled
            if side == "remote":
                return redirect(url_for("remote_form", token=vpn.remote_token))
            else:
                return redirect(url_for("local_form", token=vpn.local_token))
        elif action == "agree":
            if side == "remote":
                vpn.remote_agreed = True
            else:
                vpn.local_agreed = True
            db.session.commit()

            # if both agreed -> finalize and email summary
            if vpn.remote_agreed and vpn.local_agreed:
                vpn.status = "complete"
                db.session.commit()
                # Send final summary to both parties
                summary_html = render_template_string(
                    "<h3>Finalized VPN: {{ vpn.vpn_name }}</h3><h4>Local Side</h4><pre>{{ local_pretty }}</pre><h4>Remote Side</h4><pre>{{ remote_pretty }}</pre>",
                    vpn=vpn,
                    local_pretty=json.dumps(local, indent=2),
                    remote_pretty=json.dumps(remote, indent=2)
                )
                # send to remote contact
                send_email(vpn.remote_contact_email, f"[VPN Portal] Finalized VPN - {vpn.vpn_name}", summary_html)
                # send to every address in local team field
                for addr in [a.strip() for a in vpn.local_team_email.split(",") if a.strip()]:
                    send_email(addr, f"[VPN Portal] Finalized VPN - {vpn.vpn_name}", summary_html)
                return render_page("<p class='hint'>✅ Both parties have agreed. Final summary emails sent.</p>", messages=[("success", "Both parties agreed — finalized.")])
            else:
                return render_page("<p class='hint'>Your agreement was recorded. Waiting on the other party.</p>", messages=[("success", "Agreement recorded.")])

    # GET: show review page
    content = render_template_string(REVIEW_TEMPLATE, vpn=vpn, remote=remote, local=local)
    return render_page(content)


# -------------------------
# Admin Panel
# -------------------------
@app.route("/admin")
def admin_panel():
    """Admin panel to view all VPN requests and re-trigger email alerts."""
    requests = VPNRequest.query.order_by(VPNRequest.id.desc()).all()
    
    content = f"""
      <h2>Admin Panel - VPN Requests</h2>
      <p class="hint">View all VPN requests and re-trigger email alerts as needed.</p>
      
      <table class="kv" style="width: 100%; margin-top: 16px;">
        <thead>
          <tr style="background: #f8fafc;">
            <th style="padding: 12px 8px;">ID</th>
            <th style="padding: 12px 8px;">VPN Name</th>
            <th style="padding: 12px 8px;">Type</th>
            <th style="padding: 12px 8px;">Status</th>
            <th style="padding: 12px 8px;">Created</th>
            <th style="padding: 12px 8px;">Remote Contact</th>
            <th style="padding: 12px 8px;">Local Team</th>
            <th style="padding: 12px 8px;">Actions</th>
          </tr>
        </thead>
        <tbody>
    """
    
    for req in requests:
        # Parse created timestamp for display
        created_display = req.created_at[:10] if req.created_at else "N/A"
        
        # Status badge styling
        status_class = ""
        if req.status == "complete":
            status_class = "style='background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;'"
        elif req.status == "cancelled":
            status_class = "style='background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;'"
        elif req.status == "awaiting_agreement":
            status_class = "style='background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;'"
        else:
            status_class = "style='background: #e2e8f0; color: #475569; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;'"
        
        # Agreement status indicators
        agreement_status = ""
        if req.status == "awaiting_agreement":
            remote_check = "✓" if req.remote_agreed else "○"
            local_check = "✓" if req.local_agreed else "○"
            agreement_status = f"<br><small class='muted'>Remote: {remote_check} Local: {local_check}</small>"
        
        content += f"""
          <tr>
            <td style="padding: 8px;">#{req.id}</td>
            <td style="padding: 8px;"><strong>{req.vpn_name}</strong></td>
            <td style="padding: 8px;">{req.vpn_type}</td>
            <td style="padding: 8px;"><span {status_class}>{req.status.replace('_', ' ').title()}</span>{agreement_status}</td>
            <td style="padding: 8px;">{created_display}</td>
            <td style="padding: 8px;">{req.remote_contact_email}<br><small class='muted'>{req.remote_contact_name or 'N/A'}</small></td>
            <td style="padding: 8px;">{req.local_team_email}</td>
            <td style="padding: 8px;">
              <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                <form method="post" action="/admin/resend-initial/{req.id}" style="display: inline;">
                  <button class="btn" style="font-size: 0.8rem; padding: 4px 8px;" type="submit" 
                    {'disabled' if req.status == 'cancelled' else ''}>Resend Initial</button>
                </form>
                <form method="post" action="/admin/resend-agreement/{req.id}" style="display: inline;">
                  <button class="btn secondary" style="font-size: 0.8rem; padding: 4px 8px;" type="submit" 
                    {'disabled' if not (req.remote_data and req.local_data) or req.status == 'cancelled' else ''}>Resend Agreement</button>
                </form>
                <form method="post" action="/admin/resend-final/{req.id}" style="display: inline;">
                  <button class="btn secondary" style="font-size: 0.8rem; padding: 4px 8px;" type="submit"
                    {'disabled' if req.status != "complete" else ''}>Resend Final</button>
                </form>
                <form method="post" action="/admin/cancel/{req.id}" style="display: inline;" 
                  onsubmit="return confirm('Are you sure you want to cancel this VPN request? This action cannot be undone.')">
                  <button class="btn" style="font-size: 0.8rem; padding: 4px 8px; background: #dc2626;" type="submit"
                    {'disabled' if req.status in ['complete', 'cancelled'] else ''}>Cancel Request</button>
                </form>
              </div>
            </td>
          </tr>
        """
    
    content += """
        </tbody>
      </table>
      
      <div style="margin-top: 20px;">
        <a href="/" class="btn secondary">← Back to Home</a>
      </div>
      
      <div class="pretty" style="margin-top: 16px;">
        <h4 style="margin-top: 0;">Email Actions:</h4>
        <ul style="margin: 8px 0;">
          <li><strong>Resend Initial:</strong> Re-sends the initial email with unique links to remote contact and local team</li>
          <li><strong>Resend Agreement:</strong> Re-sends review & agreement emails (only available when both sides have submitted details)</li>
          <li><strong>Resend Final:</strong> Re-sends final summary email (only available for completed requests)</li>
        </ul>
      </div>
    """
    
    return render_page(content)


# -------------------------
# Admin email re-trigger routes
# -------------------------
@app.route("/admin/resend-initial/<int:request_id>", methods=["POST"])
def admin_resend_initial(request_id):
    """Re-trigger initial detail request emails."""
    vpn = VPNRequest.query.get_or_404(request_id)
    
    if vpn.status == "cancelled":
        flash(f"Cannot resend emails - VPN request #{request_id} has been cancelled", "error")
        return redirect(url_for("admin_panel"))
    
    # Build links
    remote_link = urljoin(BASE_URL, f"/remote/{vpn.remote_token}")
    local_link = urljoin(BASE_URL, f"/local/{vpn.local_token}")
    
    # Send to remote contact
    send_email(
        vpn.remote_contact_email,
        f"[VPN Portal] [RESENT] Please provide remote details for '{vpn.vpn_name}'",
        f"<p>Hello {vpn.remote_contact_name or ''},</p>"
        f"<p>Please provide your side's VPN details here: <a href='{remote_link}'>{remote_link}</a></p>"
        f"<p>Reason: {vpn.reason}</p>"
        f"<p><em>This is a resent email from the admin panel.</em></p>"
    )
    
    # Send to local team (may be comma separated)
    for addr in [a.strip() for a in vpn.local_team_email.split(",") if a.strip()]:
        send_email(
            addr,
            f"[VPN Portal] [RESENT] Please provide local details for '{vpn.vpn_name}'",
            f"<p>Please provide your local VPN details here: <a href='{local_link}'>{local_link}</a></p>"
            f"<p>Reason: {vpn.reason}</p>"
            f"<p><em>This is a resent email from the admin panel.</em></p>"
        )
    
    flash(f"Initial emails resent for VPN request #{request_id} ({vpn.vpn_name})", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/resend-agreement/<int:request_id>", methods=["POST"])
def admin_resend_agreement(request_id):
    """Re-trigger agreement/review emails."""
    vpn = VPNRequest.query.get_or_404(request_id)
    
    if vpn.status == "cancelled":
        flash(f"Cannot resend emails - VPN request #{request_id} has been cancelled", "error")
        return redirect(url_for("admin_panel"))
    
    if not (vpn.remote_data and vpn.local_data):
        flash(f"Cannot resend agreement emails - both sides haven't submitted details yet", "error")
        return redirect(url_for("admin_panel"))
    
    # Build review links
    base = BASE_URL.rstrip("/")
    remote_review = urljoin(base + "/", f"agree/{vpn.remote_token}")
    local_review = urljoin(base + "/", f"agree/{vpn.local_token}")
    
    # Send to remote contact
    send_email(
        vpn.remote_contact_email,
        f"[VPN Portal] [RESENT] Review & Agree — {vpn.vpn_name}",
        f"<p>Both sides have submitted details for <strong>{vpn.vpn_name}</strong>.</p>"
        f"<p>Please review and either Agree or Edit using this link: <a href='{remote_review}'>{remote_review}</a></p>"
        f"<p><em>This is a resent email from the admin panel.</em></p>"
    )
    
    # Send to local team (may be comma list)
    for addr in [a.strip() for a in vpn.local_team_email.split(",") if a.strip()]:
        send_email(
            addr,
            f"[VPN Portal] [RESENT] Review & Agree — {vpn.vpn_name}",
            f"<p>Both sides have submitted details for <strong>{vpn.vpn_name}</strong>.</p>"
            f"<p>Please review and either Agree or Edit using this link: <a href='{local_review}'>{local_review}</a></p>"
            f"<p><em>This is a resent email from the admin panel.</em></p>"
        )
    
    flash(f"Agreement emails resent for VPN request #{request_id} ({vpn.vpn_name})", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/resend-final/<int:request_id>", methods=["POST"])
def admin_resend_final(request_id):
    """Re-trigger final summary emails."""
    vpn = VPNRequest.query.get_or_404(request_id)
    
    if vpn.status != "complete":
        flash(f"Cannot resend final emails - VPN request is not yet complete", "error")
        return redirect(url_for("admin_panel"))
    
    # Parse JSON data for summary
    remote = {}
    local = {}
    try:
        remote = json.loads(vpn.remote_data) if vpn.remote_data else {}
        local = json.loads(vpn.local_data) if vpn.local_data else {}
    except:
        pass
    
    # Generate summary
    summary_html = render_template_string(
        "<h3>Finalized VPN: {{ vpn.vpn_name }}</h3><h4>Local Side</h4><pre>{{ local_pretty }}</pre><h4>Remote Side</h4><pre>{{ remote_pretty }}</pre><p><em>This is a resent email from the admin panel.</em></p>",
        vpn=vpn,
        local_pretty=json.dumps(local, indent=2),
        remote_pretty=json.dumps(remote, indent=2)
    )
    
    # Send to remote contact
    send_email(vpn.remote_contact_email, f"[VPN Portal] [RESENT] Finalized VPN - {vpn.vpn_name}", summary_html)
    
    # Send to local team
    for addr in [a.strip() for a in vpn.local_team_email.split(",") if a.strip()]:
        send_email(addr, f"[VPN Portal] [RESENT] Finalized VPN - {vpn.vpn_name}", summary_html)
    
    flash(f"Final summary emails resent for VPN request #{request_id} ({vpn.vpn_name})", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/cancel/<int:request_id>", methods=["POST"])
def admin_cancel_request(request_id):
    """Cancel a VPN request to stop all processing and prevent future emails."""
    vpn = VPNRequest.query.get_or_404(request_id)
    
    if vpn.status in ["complete", "cancelled"]:
        flash(f"Cannot cancel request #{request_id} - it is already {vpn.status}", "error")
        return redirect(url_for("admin_panel"))
    
    # Set status to cancelled
    vpn.status = "cancelled"
    db.session.commit()
    
    flash(f"VPN request #{request_id} ({vpn.vpn_name}) has been cancelled", "success")
    return redirect(url_for("admin_panel"))


# -------------------------
# Health check / debug
# -------------------------
@app.route("/_status")
def status():
    return {"status": "ok", "version": "1.0", "BASE_URL": BASE_URL}


# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    # Ensure tables exist
    with app.app_context():
        db.create_all()
    # Run server
    app.run(debug=True, host="0.0.0.0", port=5000)
