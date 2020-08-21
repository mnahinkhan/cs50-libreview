# LibReview - a book reviews website

For YouTube intro, see: https://youtu.be/ucokEiVUwyI

Web Programming with Python and JavaScript (CS50 Project work)

This project implements a dynamic website called "LibReview", a site where users can view information about books and 
leave reviews for them. 

"templates/layout.html" defines the overall layout of the website, while "templates/index.html" has the contents of the
website described. "index.html" uses Jinja2 to describe the contents of the website in various states, such as when the
user is logging in, registering, searching for a book, or viewing the details of a book. 

"application.py" does all the background work involved in such various scenarios, such as checking if the user exists
in a database or loading up information related to a book (both from our own database on Heroku as well as using
Goodreads API).

"import.py" is a file that, upon execution, will load up all the books described in "books.csv" into a database that is
linked to by the "DATABASE_URL" local variable.

"static/styles.scss" is a SASS file that describes the various CSS properties that the elements on the website should
have, and is used to compile "static/styles.css".

To run the website, make sure all the packages under "requirements.txt" are installed and then type "flask run" into a
command line.


