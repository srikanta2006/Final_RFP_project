from flask import Flask, render_template, request, redirect, flash, session, url_for, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from resume_blueprint import resume_bp  # Import the blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up uploads folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register the resume blueprint
app.register_blueprint(resume_bp, url_prefix='/resume')

# Initialize the database
def init_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL
                        );''')
        conn.commit()

init_db()

def get_user_folder():
    """Returns the upload folder for the logged-in user."""
    if 'username' not in session:
        return None
    user_folder = os.path.join(UPLOAD_FOLDER, session['username'])
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

@app.before_request
def load_logged_in_user():
    """Loads the currently logged-in user and prevents unauthorized access to resumes."""
    g.user = session.get('username')
    if request.endpoint and request.endpoint.startswith('resume.') and not g.user:
        flash("You must log in first!", "danger")
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index2345.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[2], password):  # Verify hashed password
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)  # Hash password before storing

        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    user_folder = get_user_folder()
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    return render_template('webpage.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
