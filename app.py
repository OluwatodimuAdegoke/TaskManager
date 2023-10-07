import datetime
import pytz
##import pytz

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from functools import wraps

app = Flask(__name__)
app.secret_key = "super secret key"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///task.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function




@app.route("/")
@login_required
def index():
    id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?",id)[0]
    name = user["username"]
    time = datetime.datetime.now()
    format = '%Y-%m-%d %H:%M:%S'
    tasks = db.execute("SELECT * FROM ? WHERE status='TODO'",name)
    for a in range(len(tasks)):
        ctime = datetime.datetime.strptime(tasks[a]["time"],format)
        ctime = time - ctime
        tasks[a]["ttime"] = datetime.timedelta(seconds=int(ctime.total_seconds()))
    return render_template("index.html",tasks=tasks)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    if request.method == "POST":

        if not request.form.get("username"):
            flash("No UserName Inputed")
            return render_template("login.html")
        elif not request.form.get("password"):
            flash("No Password Inputed")
            return render_template("login.html")

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash( rows[0]["hash"], request.form.get("password")):
            flash("Invalid UserName/Password Inputed")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        name = request.form.get("username")
        passw = request.form.get("password")
        if not name:
            flash("No Name Inputed")
            return render_template("register.html")
        if not passw:
            flash("No Password Inputed")
            return render_template("register.html")
        if not request.form.get("confirmation"):
            flash("Input the Confirmation Password")
            return render_template("register.html")
        if not (passw == request.form.get("confirmation")):
            flash("Password Is Different")
            return render_template("register.html")
        names = db.execute("SELECT * FROM users")
        for a in range(len(names)):
            if name == names[a]["username"]:
                flash("Username Already Chosen")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (username,hash) VALUES (?,?)",
            name,
            generate_password_hash(passw),
        )

        db.execute( "CREATE TABLE IF NOT EXISTS ? (task_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, task TEXT NOT NULL,status TEXT NOT NULL, time NUMERIC NOT NULL);",name,)
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/add",methods = ["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        task = request.form.get("task")
        if not task:
            flash("No Task Inputed")
            return redirect("/")
        
        id = session["user_id"]
        user = db.execute("SELECT * FROM users WHERE id = ?",id)[0]
        name = user["username"]
        time = datetime.datetime.now()
        db.execute("INSERT INTO ? (task,status,time) VALUES (?,?,?)",name,task,"TODO",time)
        return redirect("/")
    else:
        return redirect("/")
    
@app.route("/action",methods = ["GET","POST"])
@login_required
def action():
    if request.method == "GET":
        return redirect("/")
    else:
        id = session["user_id"]
        user = db.execute("SELECT * FROM users WHERE id = ?",id)[0]
        name = user["username"]
    
        page_id = request.form.getlist("tasks")
        if not page_id:
            flash("No Task Selected")
            return redirect("/")
        
        time = datetime.datetime.now()
        if request.form['action'] == "delete":
            for a in page_id:
                db.execute("UPDATE ? SET status = ?, time = ? WHERE task_id = ? ",name,"TRASH",time, a)
        elif request.form['action'] == "finished":
            for a in page_id:
                db.execute("UPDATE ? SET status = ?, time = ? WHERE task_id = ? ",name,"COMPLETED",time, a)


        return redirect("/")


@app.route("/completed",methods=["GET","POST"])
@login_required
def completed():
    id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?",id)[0]
    name = user["username"]
    time = datetime.datetime.now()

    tasks = db.execute("SELECT * FROM ? WHERE status='COMPLETED'",name)
    if request.method == "GET":
        return render_template("completed.html",tasks=tasks)
    else:
        page_id = request.form.getlist("tasks")
        if not page_id:
            flash("No Task Selected")
            return redirect("/completed")
        
        if request.form['action'] == "delete":
            for a in page_id:
                db.execute("UPDATE ? SET status = ?, time = ? WHERE task_id = ? ",name,"TRASH",time, a)

        return redirect("/completed")


@app.route("/trash",methods=["GET","POST"])
@login_required
def trash():
    id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?",id)[0]
    name = user["username"]
    time = datetime.datetime.now()

    tasks = db.execute("SELECT * FROM ? WHERE status='TRASH'",name)
    if request.method == "GET":
        return render_template("trash.html",tasks=tasks)
    else:
        return redirect("/trash")
