import os
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect
from flask_login import login_required, current_user, login_user, logout_user
from models import UserModel, db, login

from pyTwitter import Twitter

app = Flask(__name__)
app.secret_key = 'xyz'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login.init_app(app)
login.login_view = 'login'

DB = 'tweets.db'
DIR_NAME = parent_path = Path(os.path.abspath(os.path.dirname(__file__)))
with sqlite3.connect(os.path.join(DIR_NAME, DB)) as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS Tweets (created_at TEXT, keyword TEXT, text TEXT)')

@app.route('/test_home', methods=['GET'])
def test_home():
    return render_template('home.html')


@app.route("/")
def home():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword')

    if tweet_is_in_db(keyword):
        list_of_tweets_from_db = get_tweets_from_db(keyword)
        if less_than_5minutes(list_of_tweets_from_db[0][0]):
            tweets = [{'text': x[2]} for x in list_of_tweets_from_db]
        else:
            print("insert new tweets in db")
            search_result = Twitter().search_tweets(keyword)
            tweets = search_result['statuses']
            add_tweets_in_db(keyword, tweets)
    # Keyword isn t in DB
    else:
        print("!!!!!!!!!!!NOT FOUND IN DATABASE")
        search_result = Twitter().search_tweets(keyword)
        tweets = search_result['statuses']
        add_tweets_in_db(keyword, tweets)

    return render_template("tweets.html", tweets=tweets)


@app.before_first_request
def create_all():
    db.create_all()


@app.route('/blogs')
@login_required
def blog():
    return render_template('blog.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/blogs')

    if request.method == 'POST':
        email = request.form['email']
        user = UserModel.query.filter_by(email=email).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            return redirect('/blogs')

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/blogs')

    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if UserModel.query.filter_by(email=email).first():
            return ('Email already Present')

        user = UserModel(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/blogs')


def get_tweets_from_db(keyword):
    try:
        with sqlite3.connect(os.path.join(DIR_NAME, DB)) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM Tweets WHERE keyword = ? ORDER BY created_at DESC;''', (keyword,))
            rows = cursor.fetchall()

            return rows
    except sqlite3.Error as error:
        print("Failed to GET TWEETS BASED ON KEYWORD from DB", error)


def tweet_is_in_db(keyword):
    found = False
    try:
        with sqlite3.connect(os.path.join(DIR_NAME, DB)) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(keyword) FROM Tweets WHERE keyword="{}"'.format(keyword))
            rows = cursor.fetchall()
            if rows[0][0] > 0:
                found = True

        return found
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
        return found


def less_than_5minutes(start):
    time_now = datetime.now()
    db_time = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    time_delta = (time_now - db_time)
    diff_in_min = time_delta.total_seconds() / 60

    if diff_in_min < 5:
        return True
    else:
        return False


def insert_tweets(creation_time, keyword, tweet):
    try:
        with sqlite3.connect(os.path.join(DIR_NAME, DB)) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Tweets VALUES(?, ?, ?)".format(), (creation_time, keyword, tweet))
    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table", error)


def add_tweets_in_db(keyword, tweets):
    for t in tweets:
        creation = datetime.now()
        tw = t['text']
        insert_tweets(creation, keyword, tw)


if __name__ == "__main__":
    app.run(debug=True)
