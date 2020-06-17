import os
import requests
from flask import Flask, session, render_template, request, redirect, jsonify
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
def index(**kwargs):
    default_args = {"login_click": False, "register_click": False, "register_success": False, "is_error": False,
                    "error_msg": "", "username": "", "name": "", "password": "", "books": None, "title": "Home",
                    "is_book_page": False, "logged_in": "logged_in" in session, "real_name": session.get("name", ""),
                    "book": {}, "reviews": [], "goodreads_rating": 0, "goodreads_number": 0, "review_submitted": False}
    for k, v in kwargs.items():
        default_args[k] = v

    return render_template("index.html", **default_args)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # Is the username appropriate?
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone() is not None:
            return index(register_click=True, is_error=True, error_msg="This username is already taken, please pick "
                                                                       "another one", name=name)

        if password1 == password2:
            db.execute("INSERT INTO users (username, password, name) VALUES (:username, :password, :name)",
                       {"username": username, "password": password1, "name": name})
            db.commit()
            return index(register_success=True)
        else:
            return index(register_click=True, is_error=True, error_msg="Your passwords don't match!",
                         username=username, name=name)
    return index(register_click=True)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_search = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                                 {"username": username, "password": password}).fetchone()
        if user_search is not None:
            session["logged_in"] = True
            session["name"] = user_search["name"]
            session["user_id"] = user_search["id"]
            return index()
        else:
            return index(login_click=True, is_error=True, error_msg="Username or password incorrect!",
                         username=username, password=password)

    return index(login_click=True)


@app.route("/log_out")
def log_out():
    del session['logged_in']
    return index()


@app.route("/search/")
def search():
    book_query = request.args.get('book_query')
    books = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :book_query OR LOWER(author) LIKE :book_query" +
                       " OR isbn LIKE :book_query", {"book_query": f"%{book_query.lower()}%"}).fetchall()
    return index(books=books)


@app.route("/book/<int:book_id>")
def book_page(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT username, rating_text, rating_number FROM users INNER JOIN reviews" +
                         " ON users.id = reviews.user_id WHERE book_id=:book_id", {"book_id": book_id})
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "SdFL9J9xuEJ4cSnF9RwPhg",
                                                                                    "isbns": book.isbn})
    goodreads_rating = res.json()["books"][0]["average_rating"] if res.status_code == 200 else 0
    goodreads_number = res.json()["books"][0]["work_ratings_count"] if res.status_code == 200 else 0
    review_submitted = db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
                                  {"user_id": session["user_id"], "book_id": book_id}).fetchone() is not None
    return index(is_book_page=True, book=book, reviews=reviews, goodreads_number=goodreads_number,
                 goodreads_rating=goodreads_rating, review_submitted=review_submitted)


@app.route("/submit_review/", methods=["POST"])
def submit_review():
    book_id = request.args.get('book_id')
    book_review = request.form.get("book_review")
    rating_number = request.form.get("rating_number")
    db.execute("INSERT INTO reviews (user_id, book_id, rating_number, rating_text) VALUES (:user_id, :book_id, " +
               ":rating_number, :rating_text)", {"user_id": session["user_id"], "book_id": book_id,
                                                 "rating_number": rating_number, "rating_text": book_review})
    db.commit()
    return redirect(f"/book/{book_id}")


@app.route("/api/<string:isbn>")
def api_request(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "This book does not exist on our database"}), 404

    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    review_count = len(reviews)
    average_score = sum([review.rating_number for review in reviews]) / review_count if review_count else 0

    return jsonify({
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "isbn": book.isbn,
                "review_count": review_count,
                "average_score": average_score
            })
