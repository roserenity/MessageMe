import os, flask, psycopg2, string, random, json, requests

DATABASE_URL = os.environ['DATABASE_URL']
KEY = "GeVL4eELow8fpNhJaBTg"

from flask import Flask, session, render_template, request, redirect, url_for, abort
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

#function for db execution
def sqlexecute(sql):
    connect = None
    try:
        connect = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connect.cursor()
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()
        return 1
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if connect is not None:
            connect.close()
        return -1

#function for db search
def sqlsearch1(sql):
    connect = None
    row = None
    try:
        connect = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connect.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        print(row)
        if row is not None:
            cursor.close()
            connect.close()
            return 1
        if row is None:
            cursor.close()
            connect.close()
            return -1
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if connect is not None:
            connect.close()
        return -1

#function for retrieving
def get(sql, num):
    connect = None
    row = None
    try:
        connect = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connect.cursor()
        cursor.execute(sql)
        if num == 1:
            row = cursor.fetchone()
        else:
            row = cursor.fetchall()
        cursor.close()
        connect.close()
        return row
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if connect is not None:
            connect.close()
            return row

#function for id generation
def randomizer():
    rand = ''
    return rand.join(random.choices(string.ascii_uppercase + string.digits, k=15))

#function for session checking
def checksession():
    if session.get('logged_in') == False:
        return False
    else:
        return True

@app.route("/")
@app.route("/a-readers-review")
def login_page():
    if checksession():
        return flask.redirect('/a-readers-review/home')
    else:
        return render_template('index.html')

@app.route("/a-readers-review/logout")
def logout():
    session['logged_in'] = False
    session['userid'] = None
    session['username'] = None
    return render_template('index.html')

@app.route("/a-readers-review/register")
def register():
    if checksession():
        return flask.redirect('/a-readers-review/home')
    else:
        return render_template('register.html')

@app.route("/a-readers-review/home")
def search():
    if checksession():
        return render_template('search.html')
    else:
        return flask.redirect('/a-readers-review')

@app.route("/a-readers-review/registeraccount", methods=["POST"])
def registeraccount():
    givenname = request.form["givenname"]
    lastname = request.form["lastname"]
    username = request.form["username"]
    password = request.form["password"]
    
    sql="SELECT username FROM userinfo WHERE username = '"+username+"'"
    ret_val = sqlsearch1(sql)
    if ret_val == -1:
        ret_val = 1
        while(ret_val == 1):
            id_rand = randomizer()
            sql="SELECT user_id FROM userinfo WHERE user_id = '"+id_rand+"'"
            ret_val = sqlsearch1(sql)
            print(ret_val)
        sql="INSERT INTO userinfo VALUES ('"+id_rand+"','"+username+"','"+givenname+"', '"+lastname+"', '"+password+"' )"
        ret_val = sqlexecute(sql)
        if (ret_val):
            sql="INSERT INTO usertbl VALUES ('"+id_rand+"','"+username+"', '"+password+"' )"
            sqlexecute(sql)
            return render_template('index.html', success="Registration successful! Login with your account")
        else:
            sql="DELETE FROM usertbl WHERE user_id = "+id_rand+"'"
            sqlexecute(sql)
            return render_template('register.html', message="Registeration unsuccessful, try again")
    else:
        return render_template('register.html', message="Username is already in use, try again")

@app.route("/a-readers-review/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql="SELECT user_id, username FROM usertbl WHERE username ='"+username+"' AND password = '"+password+"'"
    row = get(sql, 1)
    if row is None:
        session['logged_in'] = False
        return render_template('index.html', message="incorrect username and password")
    else:
        session['logged_in'] = True
        session['userid'] = row[0]
        session['username'] = row[1]
        return flask.redirect('/a-readers-review/home')

@app.route("/a-readers-review/search", methods=["POST"])
def searchbook():
    search = request.form["search"]
    search = search.replace('"', '//').replace(", ", "/ ").replace("'", '/')
    sql="Select DISTINCT isbn, title, author, year FROM booktbl WHERE UPPER(isbn) LIKE UPPER('%"+search+"%') OR UPPER(title) LIKE UPPER('%"+search+"%') OR UPPER(author) LIKE UPPER('%"+search+"%')"
    books = get(sql, 2)
    if books is not None:
        result = len(books)
    else:
        result = 0
    return render_template('search.html', books=books, results = result)

@app.route("/a-readers-review/api/<isbn>")
def getisbn(isbn):
    data_set = None
    sql = "Select isbn, title, author, year, review_count, average_rating FROM booktbl WHERE isbn = '"+isbn+"'"
    books = get(sql, 2)
    if books:
        for book in books:
            data_set = {"title": book[1], "author": book[2], "year": book[3], "isbn": book[0], "review_count": book[4], "average_rating": book[5]}
        book_dump = json.dumps(data_set)
        return book_dump
    else:
        return abort(404)

@app.route("/a-readers-review/book_info/<isbn>", methods=["GET"])
def getbook(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY , "isbns": isbn})
    try:
        book_request = res.json()
        work_ratings_count = book_request.get("books")[0].get("work_ratings_count")
        average_rating = book_request.get("books")[0].get("average_rating")
    except:
        work_ratings_count = None
        average_rating = None
    sql = "Select isbn, title, author, year FROM booktbl WHERE isbn = '"+isbn+"'"
    book_info = get(sql, 1)

    sql = "Select isbn FROM review WHERE isbn = '"+isbn+"' AND username ='"+session.get("username")+"'"
    review_status = sqlsearch1(sql)
    if review_status == -1:
        review_status = False
    if review_status == 1:
        review_status = True
        
    sql = "Select username, comment, rate rating FROM review WHERE isbn = '"+isbn+"'"
    reviews = get(sql, 2)
    return render_template('bookinfo.html', book_info=book_info, review_count = work_ratings_count, ave_rating=average_rating, review_status=review_status, reviews = reviews)

@app.route("/a-readers-review/<isbn>/review", methods=["POST"])
def review(isbn):
    if checksession():
        review = request.form["review"]
        rate = request.form["rate"]
        if(rate != '0'):
            sql="INSERT INTO review VALUES ('"+isbn+"','"+session.get("username")+"', '"+review+"', "+rate+" )"
            ret_val = sqlexecute(sql)

            #count number of users who reviewed the book
            sql="SELECT COUNT(username) FROM review where isbn='"+isbn+"'"
            count = get(sql, 1)
            
            #count average
            sql="SELECT AVG(rate) FROM review where isbn='"+isbn+"'"
            ave=get(sql, 1)
            
            sql="UPDATE booktbl SET review_count = "+str(count[0])+", average_rating = "+str(ave[0])+" WHERE isbn = '"+isbn+"'"
            sqlexecute(sql)
            
            if ret_val:
                return redirect(url_for("getbook", isbn=str(isbn)))
        else:
            return redirect(url_for("getbook", isbn=str(isbn)))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404