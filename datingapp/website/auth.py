from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_bcrypt import bcrypt, Bcrypt
from website import db
from . import model
import flask_login
from datetime import datetime
import re
from website.model import photo_filename

bcrypt = Bcrypt()

auth = Blueprint('auth', __name__)

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    # Extract form data
    email = request.form.get('email')
    username = request.form.get('username')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    gender = request.form.get('gender')
    birth = request.form.get('birth') 
    description = request.form.get('description')

    # Convert `birth` to a date object
    try:
        birth_date = datetime.strptime(birth, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format for birth date.')
        return redirect(url_for('auth.signup'))

    # Validate age -- +18 in our case
    today = datetime.now().date()
    age = (today - birth_date).days // 365
    if age < 18:
        flash('You must be at least 18 years old to sign up.')
        return redirect(url_for('auth.signup'))

    # Validate password
    if password != confirm_password:
        flash('Passwords do not match.')
        return redirect(url_for('auth.signup'))
    if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        flash('Password must be at least 8 characters long, include a number, and a symbol.')
        return redirect(url_for('auth.signup'))

    # Check uniqueness of email and username
    existing_user_by_email = db.session.execute(
        db.select(model.User).where(model.User.email == email)
    ).scalar_one_or_none()
    if existing_user_by_email:
        flash('Email already exists.')
        return redirect(url_for('auth.signup'))

    existing_user_by_username = db.session.execute(
        db.select(model.User).where(model.User.username == username)
    ).scalar_one_or_none()
    if existing_user_by_username:
        flash('Username already exists.')
        return redirect(url_for('auth.signup'))

    # Hash password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a new user
    new_user = model.User(
        email=email,
        username=username,
        password=password_hash,
        first_name=first_name,
        last_name=last_name
    )
    db.session.add(new_user)
    db.session.commit()

    # Handle profile photo upload
    uploaded_file = request.files.get('photo')
    new_photo = None
    if uploaded_file and uploaded_file.filename:
        # Check file type
        content_type = uploaded_file.content_type
        if content_type == 'image/png':
            file_extension = 'png'
        elif content_type == 'image/jpeg':
            file_extension = 'jpg'
        else:
            flash(f'Unsupported file type: {content_type}')
            return redirect(url_for('auth.signup'))

        # Create Photo entry
        new_photo = model.Photo(file_extension=file_extension)
        db.session.add(new_photo)
        db.session.commit()

        # Save the photo to the filesystem
        photo_path = photo_filename(new_photo)
        uploaded_file.save(photo_path)

    # Create a new profile
    new_profile = model.UserProfile(
        user_id=new_user.id,
        gender=gender,
        birth=birth_date,
        description=description,
        photo=new_photo  
    )
    db.session.add(new_profile)
    db.session.commit()

    flash('Account created!', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    # Query user by email
    query = db.select(model.User).where(model.User.email == email)
    user = db.session.execute(query).scalar_one_or_none()

    if user and bcrypt.check_password_hash(user.password, password):
        flask_login.login_user(user)
        return redirect(url_for('main.index'))
    else:
        flash('Invalid email or password')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('main.loading'))