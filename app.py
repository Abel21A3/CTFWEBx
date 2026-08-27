from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

app.config["SECRET_KEY"] = "ef6929bd8dc5b20b459a8662e85b9bff2332302bf0658de6667a1225dcd31c49"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[]
)


# Database connection
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Home
@app.route("/")
def home():
    return render_template("home.html")


# About
@app.route("/about")
def about():
    return render_template("about.html")


# Login
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return "Invalid username or password."

    return render_template("login.html")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        connection.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password_hash)
        )

        connection.commit()
        connection.close()

        return "Account created successfully."

    return render_template("register.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    return render_template("dashboard.html", username=username)


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/account", methods=["GET", "POST"])
def account():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        display_name = request.form.get("display_name")

        connection = get_db_connection()

        connection.execute(
            "UPDATE users SET display_name = ? WHERE id = ?",
            (display_name, session["user_id"])
        )

        connection.commit()
        connection.close()

        return redirect(url_for("account"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()

    return render_template("account.html", user=user)
@app.route("/profile/<int:user_id>")
def profile(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT id, username, display_name FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    if user is None:
        return "User not found", 404

    return render_template("profile.html", user=user)

# Start Flask
if __name__ == "__main__":
    app.run(debug=True, port=5000)
