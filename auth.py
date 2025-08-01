# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User # cite: 1
from extensions import db # cite: 1
from sqlalchemy.exc import IntegrityError # Import IntegrityError

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('problems.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first() # cite: 1
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('problems.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('problems.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first(): # cite: 1
            flash('Username already exists. Please choose a different one.', 'warning')
            return render_template('register.html')
        if User.query.filter_by(email=email).first(): # cite: 1
            flash('Email already registered. Please use a different email.', 'warning')
            return render_template('register.html')

        # Changed the hash method to 'pbkdf2:sha256' for compatibility with werkzeug.security
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256') 
        new_user = User(username=username, email=email, password=hashed_password) # cite: 1
        
        try:
            db.session.add(new_user) # cite: 1
            db.session.commit() # cite: 1
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            # This catches database errors like unique constraint violations
            db.session.rollback() # Rollback the session to clear the pending transaction # cite: 1
            flash('A user with that username or email already exists. Please try different credentials.', 'danger')
            return render_template('register.html')
        except Exception as e:
            # Catch any other unexpected errors during database operation
            db.session.rollback() # cite: 1
            flash(f'An unexpected error occurred during registration: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))