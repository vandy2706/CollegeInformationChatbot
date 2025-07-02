from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv

def load_responses():
    responses = {}
    with open('QA.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            user_input = row['user_input'].strip().lower()
            bot_response = row['bot_response']
            responses[user_input] = bot_response
    return responses

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

def init_db():
    if not os.path.exists('users.db'):
        with sqlite3.connect('users.db') as conn:
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            ''')
            print("Database initialized.")
init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect('users.db') as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            flash("Signup successful. Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('users.db') as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user[2], password):
            session['user'] = username
            return redirect(url_for('chatbot'))
        else:
            flash("Invalid username or password", "error")

    return render_template('login.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user' not in session:
        return redirect(url_for('login'))

    bot_reply = None
    if request.method == 'POST':
        user_message = request.form['message'].strip().lower()
        responses = load_responses()
        bot_reply = responses.get(user_message, "I'm not sure how to respond to that.")

    return render_template('chatbot.html', bot_reply=bot_reply)

from flask import jsonify

@app.route('/get_response', methods=['POST'])
def get_response():
    if 'user' not in session:
        return jsonify({'response': 'Please log in to chat.'})

    user_message = request.json.get('message', '').strip().lower()
    responses = load_responses()
    bot_reply = responses.get(user_message, "I'm not sure how to respond to that.")
    return jsonify({'response': bot_reply})


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
