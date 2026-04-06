from flask import Flask, request, redirect, session, jsonify
import json, os
import psutil

app = Flask(__name__, static_folder="static")
app.secret_key = "secret123"

STATUS_FILE = "status.json"
ADMIN_FILE = "admins.json"
LOG_FILE = "login_logs.json"

# ---------- ADMIN ----------
def load_admins():
    if not os.path.exists(ADMIN_FILE):
        data = {"admins":[{"username":"admin","password":"1234"}]}
        json.dump(data, open(ADMIN_FILE,"w"))
        return data["admins"]
    return json.load(open(ADMIN_FILE))["admins"]

def save_admins(admins):
    json.dump({"admins":admins}, open(ADMIN_FILE,"w"))

def validate(u,p):
    return any(a["username"]==u and a["password"]==p for a in load_admins())

@app.route("/get_admins")
def get_admins():
    return jsonify(load_admins())

@app.route("/add_admin", methods=["POST"])
def add_admin():
    admins = load_admins()
    admins.append({"username":request.form["user"],"password":request.form["pw"]})
    save_admins(admins)
    return "ok"

@app.route("/delete_admin", methods=["POST"])
def delete_admin():
    admins = load_admins()
    admins = [a for a in admins if a["username"] != request.form["user"]]
    save_admins(admins)
    return "ok"

# ---------- STATUS ----------
def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"locked":True}
    return json.load(open(STATUS_FILE))

def save_status(d):
    json.dump(d, open(STATUS_FILE,"w"))

@app.route("/lock", methods=["POST"])
def lock():
    d = get_status()
    d["locked"] = True
    save_status(d)
    return "ok"

@app.route("/unlock", methods=["POST"])
def unlock():
    d = get_status()
    d["locked"] = False
    save_status(d)
    return "ok"

# ---------- LOGS ----------
def get_logs():
    if not os.path.exists(LOG_FILE):
        return []
    return json.load(open(LOG_FILE))[-50:]

@app.route("/logs")
def logs():
    return jsonify(get_logs())

@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    if "user" not in session:
        return "unauthorized"
    json.dump([], open(LOG_FILE, "w"))
    return "cleared"

# ---------- SYSTEM ----------
@app.route("/system")
def system():
    return jsonify({
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    })

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if validate(request.form["user"], request.form["pw"]):
            session["user"]=request.form["user"]
            return redirect("/dashboard")

    return """
    <body style="background:#0f172a;color:white;
    display:flex;justify-content:center;align-items:center;height:100vh;font-family:Segoe UI">
    <form method="post" style="background:#111827;padding:30px;border-radius:12px">
    <h2>🔐 AsimPa Admin</h2>
    <input name="user" placeholder="Username"><br><br>
    <input name="pw" type="password" placeholder="Password"><br><br>
    <button>Login</button>
    </form>
    </body>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return f"""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{
    margin:0;
    font-family:Segoe UI;
    display:flex;
    background:#0f172a;
    color:white;
}}
.sidebar {{
    width:250px;
    background:#020617;
    height:100vh;
    padding:20px;
}}
.sidebar img {{
    width:100%;
    border-radius:12px;
}}
.sidebar button {{
    width:100%;
    margin:6px 0;
    padding:10px;
    background:#111827;
    border:none;
    color:white;
    border-radius:8px;
    cursor:pointer;
}}
.sidebar button:hover {{
    background:#1e293b;
}}
.main {{
    flex:1;
    padding:20px;
}}
.card {{
    background:#111827;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
}}
</style>
</head>

<body>

<div class="sidebar">
<img src="/static/logo.jpg">
<h2 style="text-align:center;color:#38bdf8;">⚡ AsimPa</h2>
<hr>
<button onclick="loadSystem()">🖥 System</button>
<button onclick="loadLogs()">📜 Logs</button>
<button onclick="lock()">🔒 Lock</button>
<button onclick="unlock()">🔓 Unlock</button>
<hr>
<button onclick="logout()" style="background:#ef4444;">
🚪 Logout
</button>
</div>

<div class="main">
<h2>AsimPa Panel | {session["user"]}</h2>

<div class="card">
<h3>System</h3>
<p id="sys"></p>
</div>

<div class="card">
<h3>Admins</h3>
<div id="admins"></div>
<input id="newuser" placeholder="user">
<input id="newpass" placeholder="pass">
<button onclick="addAdmin()">Add</button>
</div>

<div class="card">
<h3>Logs</h3>

<button onclick="clearLogs()" 
style="background:#ef4444;padding:8px;border:none;color:white;border-radius:6px;margin-bottom:10px;">
🗑 Clear Logs
</button>

<pre id="logs"></pre>
</div>

</div>

<script>
async function loadAdmins(){{
let a = await fetch('/get_admins').then(r=>r.json());
document.getElementById("admins").innerHTML =
a.map(x=>`
<div>
${{x.username}}
<button onclick="delAdmin('${{x.username}}')">❌</button>
</div>`).join("");
}}

async function addAdmin(){{
await fetch('/add_admin', {{
method:'POST',
headers:{{'Content-Type':'application/x-www-form-urlencoded'}},
body:`user=${{newuser.value}}&pw=${{newpass.value}}`
}});
loadAdmins();
}}

async function delAdmin(u){{
await fetch('/delete_admin', {{
method:'POST',
headers:{{'Content-Type':'application/x-www-form-urlencoded'}},
body:`user=${{u}}`
}});
loadAdmins();
}}

async function loadSystem(){{
let s = await fetch('/system').then(r=>r.json());
document.getElementById("sys").innerText =
"CPU: "+s.cpu+"% | RAM: "+s.ram+"% | Disk: "+s.disk+"%";
}}

async function loadLogs(){{
let l = await fetch('/logs').then(r=>r.json());
document.getElementById("logs").innerText =
l.map(x=>x.user+" | "+x.time).join("\\n");
}}

async function clearLogs(){{
if(confirm("Delete all logs?")){{
    await fetch('/clear_logs', {{method:'POST'}});
    loadLogs();
}}
}}

function lock(){{fetch('/lock',{{method:'POST'}})}}
function unlock(){{fetch('/unlock',{{method:'POST'}})}}
function logout(){{window.location.href="/logout"}}

loadAdmins();
loadSystem();
loadLogs();
</script>

</body>
</html>
"""

# ---------- RUN ----------
app.run(host="0.0.0.0", port=8080, debug=True)