import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index(login_click=False, register_click=False, register_success=False, is_error=False,
          error_msg="", username="", name="", password=""):

    return render_template("index.html", logged_in=("logged_in" in session), login_click=login_click,
                           register_click=register_click, register_success=register_success, is_error=is_error,
                           error_msg=error_msg, username=username, name=name, password=password)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # Is the username appropriate?
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone() is not None:
            return index(register_click=True,  is_error=True, error_msg="This username is already taken, please pick "
                                                                        "another one", name=name)

        if password1 == password2:
            db.execute("INSERT INTO users (username, password, name) VALUES (:username, :password, :name)",
                       {"username": username, "password": password1, "name": name})
            db.commit()
            return index(register_success=True)
        else:
            return index(register_click=True,  is_error=True, error_msg="Your passwords don't match!",
                         username=username, name=name)
    return index(register_click=True)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                      {"username": username, "password": password}).fetchone() is not None:
            session["logged_in"] = True
            return index()
        else:
            return index(login_click=True, is_error=True, error_msg="Username or password incorrect!",
                         username=username, password=password)

    return index(login_click=True)


@app.route("/log_out")
def log_out():
    del session['logged_in']
    return index()
