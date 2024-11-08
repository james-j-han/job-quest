from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Load environment variables
app.config.update(os.environ)
# app.secret_key = os.getenv('SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

with app.app_context():
    create_users_table = text("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL
    )
    """)
    db.session.execute(create_users_table)
    db.session.commit()

    create_companies_table = text("""
    CREATE TABLE IF NOT EXISTS companies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        industry VARCHAR(100) NOT NULL,
        website VARCHAR(100) NOT NULL UNIQUE
    )
    """)
    db.session.execute(create_companies_table)
    db.session.commit()

    create_job_listing_table = text("""
    CREATE TABLE IF NOT EXISTS job_listings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        company_id INT NOT NULL,
        location VARCHAR(100) NOT NULL,
        salary DECIMAL(10, 2) NOT NULL,
        date_posted DATE NOT NULL,
        deadline DATE NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )
    """)
    db.session.execute(create_job_listing_table)
    db.session.commit()

    create_application_table = text("""
    CREATE TABLE IF NOT EXISTS applications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        job_id INT NOT NULL,
        user_id INT NOT NULL,
        application_date DATE,
        status ENUM('Pending', 'Accepted', 'Rejected') DEFAULT 'Pending',
        notes TEXT,
        FOREIGN KEY (job_id) REFERENCES job_listings(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    db.session.execute(create_application_table)
    db.session.commit()

# @app.before_request
# def clear_session_on_start():
#     session.clear()  # This clears all session data
#     print("Session cleared on app start.")

@app.route('/')
def index():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve user by username
        query = text("SELECT id, password_hash FROM users WHERE username = :username")
        user = db.session.execute(query, {"username": username}).fetchone()

        try:
            if user and bcrypt.check_password_hash(user[1], password):
                # Store user ID in the session to keep the user logged in
                session['user_id'] = user[0]
                flash('You have successfully logged in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            print(e)
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Check if username already exists
        query = text("SELECT * FROM users WHERE username = :username")
        user_exists = db.session.execute(query, {'username': username}).fetchone()

        if user_exists:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # Hash the password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user into the database
        query = text("INSERT INTO users (username, password_hash, email, first_name, last_name) VALUES (:username, :password_hash, :email, :first_name, :last_name)")
        db.session.execute(query, {"username": username, "password_hash": password_hash, "email": email, "first_name": first_name, "last_name": last_name})
        db.session.commit()

        flash('You have successfully registered.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/application', methods=['GET', 'POST'])
def application():
    if request.method == 'POST':
        pass
    
    return render_template('application.html')

@app.route('/job', methods=['GET', 'POST'])
def job():
    if request.method == 'POST':
        title = request.form['job_title']
        description = request.form['description']
        company_id = request.form['company_id']
        location = request.form['location']
        salary = request.form['salary']
        deadline = request.form['deadline']
        date_posted = request.form['date_posted']

        query = text("""
        INSERT INTO job_listings (title, description, company_id, location, salary, date_posted, deadline)
        VALUES (:title, :description, :company_id, :location, :salary, :date_posted, :deadline)
        """)
        db.session.execute(query, {"title": title, "description": description, "company_id": company_id, "location": location, "salary": salary, "date_posted": date_posted, "deadline": deadline})
        db.session.commit()

    query = text("SELECT id, name FROM companies")
    companies = db.session.execute(query).fetchall()
    
    # Join job_listings and companies tables
    query = text("""
        SELECT
        jl.id,
        jl.title,
        jl.description,
        jl.location,
        jl.salary,
        jl.date_posted,
        jl.deadline,
        c.name
        FROM job_listings AS jl
        INNER JOIN companies AS c
        ON jl.company_id = c.id
    """)
    job_listings = db.session.execute(query).fetchall()

    return render_template('job.html', companies=companies, job_listings=job_listings, job_info=None)

@app.route('/company', methods=['GET', 'POST'])
def company():
    if request.method == 'POST':
        company_name = request.form['company_name']
        industry = request.form['industry']
        website = request.form['website']

        query = text("INSERT INTO companies (name, industry, website) VALUES (:name, :industry, :website)")
        db.session.execute(query, {"name": company_name, "industry": industry, "website": website})
        db.session.commit()

        return redirect(url_for('company'))
    
    query = text("SELECT * FROM companies")
    companies = db.session.execute(query).fetchall()
    
    return render_template('company.html', companies=companies)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/notification')
def reminder():
    return 'Notification'

@app.route('/apply/<int:job_id>', methods=['GET'])
def apply(job_id):
    print(job_id)
    return redirect(url_for('job'))

@app.route('/delete-job/<int:job_id>', methods=['GET'])
def delete_job(job_id):
    query = text("DELETE FROM job_listings WHERE id = :job_id")
    db.session.execute(query, {"job_id": job_id})
    db.session.commit()
    return redirect(url_for('job'))

@app.route('/edit-job/<int:job_id>', methods=['GET'])
def edit_job(job_id):
    query = text("""
    SELECT
    jl.id,
    jl.title,
    jl.description,
    jl.location,
    jl.salary,
    jl.date_posted,
    jl.deadline,
    c.name,
    c.id
    FROM job_listings AS jl
    INNER JOIN companies AS c
    ON jl.company_id = c.id
    WHERE jl.id = :job_id
    """)
    job_info = db.session.execute(query, {'job_id': job_id}).fetchone()
    print(job_info)

    query = text("SELECT id, name FROM companies")
    companies = db.session.execute(query).fetchall()

    return render_template('job.html', job_info=job_info, companies=companies)
    # return redirect(url_for('job', location=job_info[3]))