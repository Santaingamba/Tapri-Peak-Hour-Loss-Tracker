from __future__ import annotations
import csv, hmac, os, secrets, sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, abort, flash, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get("TAPRI_DB_PATH",ROOT/"tapri.sqlite3")).expanduser().resolve()
TZ=ZoneInfo(os.environ.get("TAPRI_TIMEZONE","Asia/Kolkata"))
SECRET=os.environ.get("TAPRI_SECRET_KEY","")
OWNER_PASSWORD=os.environ.get("TAPRI_ADMIN_PIN","")
if len(SECRET)<32: raise RuntimeError("Set TAPRI_SECRET_KEY to a random value of at least 32 characters.")
if len(OWNER_PASSWORD)<8: raise RuntimeError("Set TAPRI_ADMIN_PIN to a private password of at least 8 characters.")
app=Flask(__name__)
app.config.update(SECRET_KEY=SECRET,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",
 SESSION_COOKIE_SECURE=os.environ.get("TAPRI_HTTPS","0")=="1",PERMANENT_SESSION_LIFETIME=timedelta(hours=8),MAX_CONTENT_LENGTH=16384)
SCHEMA="""
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,item TEXT NOT NULL,
 unit_price INTEGER NOT NULL CHECK(unit_price>0),served INTEGER NOT NULL CHECK(served>0),
 paid_qty INTEGER NOT NULL CHECK(paid_qty>=0 AND paid_qty<=served),
 method TEXT NOT NULL CHECK(method IN ('cash','upi','mixed','unknown')),
 crowd TEXT NOT NULL CHECK(crowd IN ('low','medium','high')),note TEXT NOT NULL DEFAULT '',
 confirmed_unpaid INTEGER NOT NULL DEFAULT 0 CHECK(confirmed_unpaid IN (0,1)));
CREATE TABLE IF NOT EXISTS recoveries(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
 amount INTEGER NOT NULL CHECK(amount>0),recovered_at TEXT NOT NULL,
 method TEXT NOT NULL CHECK(method IN ('cash','upi','other')),note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY,ip TEXT NOT NULL,at TEXT NOT NULL,success INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_recoveries_order ON recoveries(order_id);
CREATE INDEX IF NOT EXISTS idx_attempts_ip_time ON attempts(ip,at);
"""
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(DB,timeout=10); c.row_factory=sqlite3.Row
 c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA busy_timeout=10000")
 return c
def init_db():
 with connect() as c:
  c.executescript(SCHEMA)
  if not c.execute("SELECT 1 FROM settings WHERE key='password_hash'").fetchone():
   c.execute("INSERT INTO settings VALUES('password_hash',?)",(generate_password_hash(OWNER_PASSWORD,method="scrypt"),))
@app.before_request
def open_db():
 g.db=connect()
 if "csrf" not in session: session["csrf"]=secrets.token_urlsafe(32)
@app.teardown_request
def close_db(_):
 c=g.pop("db",None)
 if c: c.close()
@app.before_request
def csrf_check():
 if request.method=="POST":
  got=request.form.get("csrf",""); expected=session.get("csrf","")
  if not got or not expected or not hmac.compare_digest(got,expected): abort(400,"Form expired. Refresh and try again.")
@app.after_request
def security_headers(r):
 r.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer",
 "Permissions-Policy":"camera=(), microphone=(), geolocation=()",
 "Content-Security-Policy":"default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'",
 "Cache-Control":"no-store"})
 return r
def auth(fn):
 @wraps(fn)
 def wrapped(*a,**kw):
  if not session.get("ok"): return redirect(url_for("login"))
  return fn(*a,**kw)
 return wrapped
def money(p): return f"₹{p/100:,.2f}" if p%100 else f"₹{p//100:,}"
def parse_price(v):
 try: f=float(v); p=round(f*100)
 except (ValueError,TypeError,OverflowError): raise ValueError("Enter a valid price.")
 if not 1<=p<=10_000_000 or abs(f*100-p)>1e-7: raise ValueError("Price must be ₹0.01–₹100,000 with at most two decimals.")
 return p
def whole(v,label,zero=False):
 try: n=int(v)
 except (ValueError,TypeError): raise ValueError(f"{label} must be a whole number.")
 if n<(0 if zero else 1) or n>10000: raise ValueError(f"{label} is outside the allowed range.")
 return n
def now(): return datetime.now(TZ).isoformat(timespec="seconds")
def balance(o):
 initial=(o["served"]-o["paid_qty"])*o["unit_price"]
 recovered=o["recovered"] if "recovered" in o.keys() else 0
 if recovered>initial: abort(409,"Recovery total exceeds original discrepancy.")
 return initial-recovered
STYLE="""*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#172033;font:15px system-ui,sans-serif}.wrap{max-width:1080px;margin:auto;padding:20px}.top,.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.brand{font-size:21px;font-weight:800}.muted,small{color:#667085}.panel,.stat{background:#fff;border:1px solid #e5e9f0;border-radius:14px;padding:17px;margin:14px 0}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stat strong{display:block;font-size:24px;margin-top:6px}.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}.form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}label{display:block;font-weight:650;font-size:13px;margin-bottom:5px}input,select{width:100%;padding:11px;border:1px solid #ccd3df;border-radius:9px;font:inherit;background:white}.full{grid-column:1/-1}.btn{display:inline-block;padding:11px 15px;border:0;border-radius:9px;background:#1d4ed8;color:white;font-weight:700;text-decoration:none;cursor:pointer}.alt{background:#edf2ff;color:#243b7a}.danger{background:#fff0f0;color:#a32626}.flash{padding:11px;border-radius:9px;background:#fff3d7;margin:10px 0}.error{background:#fff0f0;color:#a32626}.table{overflow:auto}table{width:100%;border-collapse:collapse;min-width:620px}td,th{text-align:left;padding:10px;border-bottom:1px solid #edf0f4}th{font-size:12px;color:#667085}.pill{border-radius:20px;padding:4px 8px;background:#fff3d7;color:#885400;font-size:12px}.ok{background:#e9f8ef;color:#176b3a}.login{max-width:420px;margin:10vh auto}.small{font-size:12px}@media(max-width:720px){.wrap{padding:12px}.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.form{grid-template-columns:1fr}.full{grid-column:auto}}"""
LAYOUT="""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}} · Tapri Tracker</title><style>"""+STYLE+"""</style></head><body><main class="wrap">{{body|safe}}</main></body></html>"""
LOGIN="""<section class="panel login"><div class="brand">Tapri Tracker</div><p class="muted">Owner sign-in</p>{% for m in get_flashed_messages() %}<div class="flash error">{{m}}</div>{% endfor %}<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><label>Password</label><input type="password" name="password" minlength="8" maxlength="128" required autocomplete="current-password"><p><button class="btn">Sign in</button></p></form><small>Private owner access. Do not share your password.</small></section>"""
DASH="""<header class="top"><div><div class="brand">Tapri Tracker</div><small>Daily orders · payment reconciliation</small></div><form method="post" action="{{url_for('logout')}}"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn alt">Lock</button></form></header>
{% for c,m in get_flashed_messages(with_categories=true) %}<div class="flash {{'error' if c=='error' else ''}}">{{m}}</div>{% endfor %}
<div class="stats"><div class="stat"><small>Orders today</small><strong>{{totals.orders}}</strong></div><div class="stat"><small>Units served</small><strong>{{totals.units}}</strong></div><div class="stat"><small>Payments received</small><strong>{{money(totals.received)}}</strong></div><div class="stat"><small>Needs checking</small><strong>{{money(totals.open)}}</strong></div></div>
<div class="grid"><section class="panel"><h2>Record an order</h2><p class="muted small">Enter what was served and what you actually received. A mismatch is a reminder to check, not an accusation.</p><form class="form" method="post" action="{{url_for('add_order')}}"><input type="hidden" name="csrf" value="{{csrf}}"><div><label>Item</label><input name="item" list="menu" maxlength="60" required placeholder="Tea"><datalist id="menu">{% for x in menu %}<option value="{{x[0]}}">{% endfor %}</datalist></div><div><label>Unit price (₹)</label><input name="price" type="number" min=".01" max="100000" step=".01" required placeholder="10"></div><div><label>Quantity served</label><input name="served" type="number" min="1" max="10000" value="1" required></div><div><label>Quantity paid for</label><input name="paid" type="number" min="0" max="10000" value="1" required></div><div><label>Payment method</label><select name="method"><option>cash</option><option>upi</option><option>mixed</option><option>unknown</option></select></div><div><label>Crowd level</label><select name="crowd"><option>low</option><option>medium</option><option>high</option></select></div><div class="full"><label>Note (optional; no customer details)</label><input name="note" maxlength="240"></div><div class="full"><button class="btn">Save order</button></div></form></section>
<section class="panel"><h2>During the rush</h2><ol class="muted"><li>Record item and quantity served.</li><li>Enter quantity paid for.</li><li>Check flagged mismatches after the rush.</li><li>Record later payments against the order.</li><li>Confirm unpaid only after checking.</li></ol><p class="small muted">A trusted helper can enter orders while Rupam Daa serves customers. Do not store customer names or phone numbers.</p></section></div>
<section class="panel"><div class="bar"><h2>Today's orders · {{today}}</h2><a class="btn alt" href="{{url_for('history')}}">History</a></div>{% if orders %}<div class="table"><table><tr><th>Time</th><th>Item</th><th>Served</th><th>Paid qty</th><th>Outstanding</th><th>Status</th><th></th></tr>{% for o in orders %}<tr><td>{{o.created_at[11:16]}}</td><td>{{o.item}}<br><small>{{money(o.unit_price)}} / unit</small></td><td>{{o.served}}</td><td>{{o.paid_qty}}</td><td>{{money(o.balance)}}</td><td>{% if o.balance==0 %}<span class="pill ok">Settled</span>{% elif o.confirmed_unpaid %}<span class="pill">Confirmed unpaid</span>{% else %}<span class="pill">Check payment</span>{% endif %}</td><td><a href="{{url_for('detail',oid=o.id)}}">Open</a></td></tr>{% endfor %}</table></div>{% else %}<p class="muted">No orders recorded today. Add the first order above.</p>{% endif %}</section>
<p class="small muted">No POS or UPI integration: payment entries must be checked by the operator. A mismatch alone does not prove intent or theft.</p>"""
DETAIL="""<header class="top"><div><div class="brand">Tapri Tracker</div><small><a href="{{url_for('home')}}">← Dashboard</a> / Order #{{o.id}}</small></div></header>{% for c,m in get_flashed_messages(with_categories=true) %}<div class="flash {{'error' if c=='error' else ''}}">{{m}}</div>{% endfor %}
<section class="panel"><h2>{{o.item}}</h2><p class="muted">{{o.created_at}} · {{o.served}} served · {{o.paid_qty}} initially paid</p><div class="stats"><div class="stat"><small>Order value</small><strong>{{money(o.served*o.unit_price)}}</strong></div><div class="stat"><small>Initially paid</small><strong>{{money(o.paid_qty*o.unit_price)}}</strong></div><div class="stat"><small>Recovered later</small><strong>{{money(o.recovered)}}</strong></div><div class="stat"><small>Still outstanding</small><strong>{{money(balance)}}</strong></div></div></section>
<div class="grid"><section class="panel"><h3>Record later payment</h3>{% if balance %}<form method="post" action="{{url_for('recover',oid=o.id)}}" class="form"><input type="hidden" name="csrf" value="{{csrf}}"><div><label>Amount received (₹)</label><input name="amount" type="number" min=".01" max="100000" step=".01" required></div><div><label>Method</label><select name="method"><option>cash</option><option>upi</option><option>other</option></select></div><div class="full"><label>Note</label><input name="note" maxlength="240"></div><div class="full"><button class="btn">Save recovery</button></div></form>{% else %}<p class="muted">Order settled.</p>{% endif %}</section>
<section class="panel"><h3>Reconciliation</h3><p class="muted small">Only confirm after checking cash/UPI records and allowing for delayed or group payments.</p>{% if balance %}<form method="post" action="{{url_for('confirm',oid=o.id)}}"><input type="hidden" name="csrf" value="{{csrf}}"><button class="btn {{'alt' if o.confirmed_unpaid else 'danger'}}">{{'Remove confirmed status' if o.confirmed_unpaid else 'Confirm still unpaid'}}</button></form>{% endif %}<p class="small muted">Payment: {{o.method}} · Crowd: {{o.crowd}}</p><p>{{o.note}}</p></section></div>
<section class="panel"><h3>Recovery history</h3>{% if recoveries %}<div class="table"><table><tr><th>When</th><th>Amount</th><th>Method</th><th>Note</th></tr>{% for r in recoveries %}<tr><td>{{r.recovered_at}}</td><td>{{money(r.amount)}}</td><td>{{r.method}}</td><td>{{r.note}}</td></tr>{% endfor %}</table></div>{% else %}<p class="muted">No later payments recorded.</p>{% endif %}</section>"""
HISTORY="""<header class="top"><div><div class="brand">Tapri Tracker</div><small><a href="{{url_for('home')}}">← Dashboard</a> / History</small></div></header><section class="panel"><h2>Order history</h2><form class="bar"><label>Date</label><input style="max-width:190px" type="date" name="day" value="{{day}}"><button class="btn alt">Filter</button></form>{% if orders %}<div class="table"><table><tr><th>Time</th><th>Item</th><th>Served</th><th>Paid</th><th>Outstanding</th><th></th></tr>{% for o in orders %}<tr><td>{{o.created_at}}</td><td>{{o.item}}</td><td>{{o.served}}</td><td>{{o.paid_qty}}</td><td>{{money(o.balance)}}</td><td><a href="{{url_for('detail',oid=o.id)}}">Open</a></td></tr>{% endfor %}</table></div>{% else %}<p class="muted">No orders on this date.</p>{% endif %}</section>"""
def page(title,t,**ctx):
 ctx.update(csrf=session.get("csrf",""),money=money)
 return render_template_string(LAYOUT,title=title,body=render_template_string(t,**ctx))
def menu_items():
 try:
  with (ROOT/"products.csv").open(newline="",encoding="utf-8-sig") as f: return [(r["item"].strip(),r["unit_price_inr"]) for r in csv.DictReader(f) if r.get("item")]
 except (OSError,KeyError): return []
@app.get("/health")
def health():
 try: g.db.execute("SELECT 1"); return {"status":"ok"}
 except sqlite3.Error: return {"status":"unavailable"},503
@app.route("/login",methods=["GET","POST"])
def login():
 if session.get("ok"): return redirect(url_for("home"))
 ip=request.remote_addr or "unknown"; cutoff=(datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(minutes=15)).isoformat(timespec="seconds")
 fails=g.db.execute("SELECT COUNT(*) FROM attempts WHERE ip=? AND at>=? AND success=0",(ip,cutoff)).fetchone()[0]
 if request.method=="POST":
  if fails>=8: abort(429,"Too many failed attempts. Wait 15 minutes.")
  saved=g.db.execute("SELECT value FROM settings WHERE key='password_hash'").fetchone()[0]
  good=check_password_hash(saved,request.form.get("password",""))
  g.db.execute("INSERT INTO attempts(ip,at,success) VALUES(?,?,?)",(ip,datetime.utcnow().isoformat(timespec="seconds"),int(good))); g.db.commit()
  if good:
   session.clear(); session["ok"]=True; session["csrf"]=secrets.token_urlsafe(32); session.permanent=True
   return redirect(url_for("home"))
  flash("Incorrect password.")
 return page("Sign in",LOGIN)
@app.post("/logout")
@auth
def logout():
 session.clear(); return redirect(url_for("login"))
@app.get("/")
@auth
def home():
 today=datetime.now(TZ).date().isoformat()
 rows=g.db.execute("""SELECT o.*,(o.served-o.paid_qty)*o.unit_price-COALESCE((SELECT SUM(amount) FROM recoveries r WHERE r.order_id=o.id),0) balance FROM orders o WHERE substr(created_at,1,10)=? ORDER BY id DESC""",(today,)).fetchall()
 sums=g.db.execute("SELECT COUNT(*) orders,COALESCE(SUM(served),0) units,COALESCE(SUM(paid_qty*unit_price),0) received FROM orders WHERE substr(created_at,1,10)=?",(today,)).fetchone()
 rec=g.db.execute("SELECT COALESCE(SUM(r.amount),0) FROM recoveries r JOIN orders o ON o.id=r.order_id WHERE substr(o.created_at,1,10)=?",(today,)).fetchone()[0]
 orders=[dict(r) for r in rows]
 return page("Dashboard",DASH,today=today,orders=orders,menu=menu_items(),
  totals={"orders":sums["orders"],"units":sums["units"],"received":sums["received"]+rec,"open":sum(max(0,r["balance"]) for r in rows)})
@app.post("/orders")
@auth
def add_order():
 try:
  item=request.form.get("item","").strip()
  if not item or len(item)>60 or any(ord(c)<32 for c in item): raise ValueError("Enter an item name of 1–60 characters.")
  p=parse_price(request.form.get("price")); served=whole(request.form.get("served"),"Served quantity"); paid=whole(request.form.get("paid"),"Paid quantity",True)
  if paid>served: raise ValueError("Paid quantity cannot exceed quantity served.")
  method=request.form.get("method","cash"); crowd=request.form.get("crowd","low")
  if method not in {"cash","upi","mixed","unknown"} or crowd not in {"low","medium","high"}: raise ValueError("Choose valid payment and crowd options.")
  note=request.form.get("note","").strip()
  if len(note)>240: raise ValueError("Note must be 240 characters or fewer.")
  cur=g.db.execute("INSERT INTO orders(created_at,item,unit_price,served,paid_qty,method,crowd,note) VALUES(?,?,?,?,?,?,?,?)",(now(),item,p,served,paid,method,crowd,note)); g.db.commit()
  flash("Order saved. Check the mismatch if quantities differ.")
  if served!=paid: return redirect(url_for("detail",oid=cur.lastrowid))
 except ValueError as e: flash(str(e),"error")
 return redirect(url_for("home"))
def get_order(oid):
 o=g.db.execute("""SELECT o.*,COALESCE((SELECT SUM(amount) FROM recoveries r WHERE r.order_id=o.id),0) recovered FROM orders o WHERE id=?""",(oid,)).fetchone()
 if not o: abort(404)
 return o,balance(o)
@app.get("/orders/<int:oid>")
@auth
def detail(oid):
 o,b=get_order(oid); rec=g.db.execute("SELECT * FROM recoveries WHERE order_id=? ORDER BY id DESC",(oid,)).fetchall()
 return page("Order",DETAIL,o=o,balance=b,recoveries=rec)
@app.post("/orders/<int:oid>/recover")
@auth
def recover(oid):
 try:
  amount=parse_price(request.form.get("amount")); method=request.form.get("method","cash"); note=request.form.get("note","").strip()
  if method not in {"cash","upi","other"}: raise ValueError("Choose a valid recovery method.")
  if len(note)>240: raise ValueError("Note must be 240 characters or fewer.")
  g.db.execute("BEGIN IMMEDIATE"); o,b=get_order(oid)
  if amount>b: g.db.rollback(); raise ValueError(f"Recovery cannot exceed the outstanding balance ({money(b)}).")
  g.db.execute("INSERT INTO recoveries(order_id,amount,recovered_at,method,note) VALUES(?,?,?,?,?)",(oid,amount,now(),method,note)); g.db.commit()
  flash(f"Recorded recovery of {money(amount)}.")
 except ValueError as e: flash(str(e),"error")
 return redirect(url_for("detail",oid=oid))
@app.post("/orders/<int:oid>/confirm")
@auth
def confirm(oid):
 o,b=get_order(oid)
 if b<=0: flash("This order is already settled.","error")
 else:
  g.db.execute("UPDATE orders SET confirmed_unpaid=? WHERE id=?",(0 if o["confirmed_unpaid"] else 1,oid)); g.db.commit()
  flash("Reconciliation status updated. This is an operator record, not proof of intent.")
 return redirect(url_for("detail",oid=oid))
@app.get("/history")
@auth
def history():
 day=request.args.get("day",datetime.now(TZ).date().isoformat())
 try: datetime.strptime(day,"%Y-%m-%d")
 except ValueError: abort(400,"Date must use YYYY-MM-DD.")
 rows=g.db.execute("""SELECT o.*,(o.served-o.paid_qty)*o.unit_price-COALESCE((SELECT SUM(amount) FROM recoveries r WHERE r.order_id=o.id),0) balance FROM orders o WHERE substr(created_at,1,10)=? ORDER BY id DESC LIMIT 500""",(day,)).fetchall()
 return page("History",HISTORY,day=day,orders=[dict(r) for r in rows])
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(429)
@app.errorhandler(500)
def errors(e):
 code=getattr(e,"code",500); msg=e.description if code in (400,404,429) else "Request failed. Internal details are hidden."
 return page("Error","<section class='panel'><h2>Could not complete request</h2><p>{{msg}}</p><a href='{{url_for(\"home\") if session.get(\"ok\") else url_for(\"login\")}}'>Return</a></section>",msg=msg),code
init_db()
if __name__=="__main__": app.run(host=os.environ.get("TAPRI_HOST","127.0.0.1"),port=int(os.environ.get("PORT","5000")),debug=False)
