# ==========================
# IMPORTLAR
# ==========================

import os 
import subprocess
import json
import sqlite3
import threading
import time
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session
)

# ==========================
# UYGULAMA
# ==========================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

init_db()

# ==========================
# AYARLAR
# ==========================

DEBUG = True
HOST = "0.0.0.0"
PORT = 5000

# ==========================
# FONKSİYONLAR
# ==========================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password)
    VALUES (?, ?)
    """, ("admin", "123456"))

    conn.commit()
    conn.close()

init_db()

# ==========================
# ROUTELAR
# ==========================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))

        return "Kullanıcı adı veya şifre yanlış!"

    return render_template("login.html")


@app.route("/panel")
def panel():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("panel.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        current_user=session["user"],
        current_time=datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    )

@app.route("/users")
def users():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("users.html", users=users)

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Bu kullanıcı zaten mevcut."

        conn.close()
        return redirect(url_for("users"))

    return render_template("add_user.html")

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("users"))

@app.route("/module1")
def module1():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module1.html")

script1 = None
script2 = None
script3 = None
script4 = None
script5 = None
script6 = None
script7 = None
script8 = None
script9 = None 


@app.route("/module4/start")
def start_module4():
    global script4

    if "user" not in session:
        return redirect(url_for("login"))

    if script4 is None:
        script4 = subprocess.Popen(
            ["python", "fastspring.py"],
            cwd="modules"
        )

    return redirect(url_for("module4"))


@app.route("/module4/stop")
def stop_module4():
    global script4

    if "user" not in session:
        return redirect(url_for("login"))

    if script4:
        script4.terminate()
        script4 = None

    return redirect(url_for("module4"))


@app.route("/module5/start")
def start_module5():
    global script5

    if "user" not in session:
        return redirect(url_for("login"))

    if script5 is None:
        script5 = subprocess.Popen(
            ["python", "iyzico_charge.py"],
            cwd="modules"
        )

    return redirect(url_for("module5"))


@app.route("/module5/stop")
def stop_module5():
    global script5

    if "user" not in session:
        return redirect(url_for("login"))

    if script5:
        script5.terminate()
        script5 = None

    return redirect(url_for("module5"))

@app.route("/module6/start")
def start_module6():
    global script6

    if "user" not in session:
        return redirect(url_for("login"))

    if script6 is None:
        script6 = subprocess.Popen(
            ["python", "puan.py"],
            cwd="modules"
        )

    return redirect(url_for("module6"))


@app.route("/module6/stop")
def stop_module6():
    global script6

    if "user" not in session:
        return redirect(url_for("login"))

    if script6:
        script6.terminate()
        script6 = None

    return redirect(url_for("module6"))

@app.route("/module1/start")
def start_module1():
    global script1

    if "user" not in session:
        return redirect(url_for("login"))

    if script1 is None:
        script1 = subprocess.Popen(
            ["python", "adyen.py"],
            cwd="modules"
        )

    return redirect(url_for("module1"))


@app.route("/module2/start")
def start_module2():
    global script2

    if "user" not in session:
        return redirect(url_for("login"))

    if script2 is None:
        script2 = subprocess.Popen(
            ["python", "braintree.py"],
            cwd="modules"
        )

    return redirect(url_for("module2"))


@app.route("/module2/stop")
def stop_module2():
    global script2

    if "user" not in session:
        return redirect(url_for("login"))

    if script2:
        script2.terminate()
        script2 = None

    return redirect(url_for("module2"))

@app.route("/module3/start")
def start_module3():
    global script3

    if "user" not in session:
        return redirect(url_for("login"))

    if script3 is None:
        script3 = subprocess.Popen(
            ["python", "clover.py"],
            cwd="modules"
        )

    return redirect(url_for("module3"))


@app.route("/module3/stop")
def stop_module3():
    global script3

    if "user" not in session:
        return redirect(url_for("login"))

    if script3:
        script3.terminate()
        script3 = None

    return redirect(url_for("module3"))

@app.route("/module7/start")
def start_module7():
    global script7

    if "user" not in session:
        return redirect(url_for("login"))

    if script7 is None:
        script7 = subprocess.Popen(
            ["python", "stripe.py"],
            cwd="modules"
        )

    return redirect(url_for("module7"))


@app.route("/module7/stop")
def stop_module7():
    global script7

    if "user" not in session:
        return redirect(url_for("login"))

    if script7:
        script7.terminate()
        script7 = None

    return redirect(url_for("module7"))

@app.route("/module8/start")
def start_module8():
    global script8

    if "user" not in session:
        return redirect(url_for("login"))

    if script8 is None:
        script8 = subprocess.Popen(
            ["python", "stripe_auth.py"],
            cwd="modules"
        )

    return redirect(url_for("module8"))


@app.route("/module8/stop")
def stop_module8():
    global script8

    if "user" not in session:
        return redirect(url_for("login"))

    if script8:
        script8.terminate()
        script8 = None

    return redirect(url_for("module8"))

@app.route("/module7")
def module7():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module7.html")

@app.route("/module2")
def module2():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module2.html")

@app.route("/module3")
def module3():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module3.html")


@app.route("/module4")
def module4():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module4.html")


@app.route("/module5")
def module5():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module5.html")


@app.route("/module6")
def module6():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module6.html")


@app.route("/module8")
def module8():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module8.html")


@app.route("/module9")
def module9():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("module9.html")

@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("settings.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================
# BAŞLAT
# ==========================

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)