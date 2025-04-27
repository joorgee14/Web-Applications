from flask import Blueprint, render_template
from website.model import db, UserProfile, MatchingPreference
from flask_login import current_user
import flask_login
from datetime import datetime
from sqlalchemy import extract
from datetime import datetime
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
def loading():
    return render_template('loading.html')

@main.route('/index')
@flask_login.login_required
def index():
    user = current_user

    # Fetch matching preferences
    query_preferences = db.select(MatchingPreference).where(MatchingPreference.user_id == user.id)
    preferences = db.session.execute(query_preferences).scalar_one_or_none()

    # Get IDs of blocked users
    blocked_user_ids = [blocked_user.id for blocked_user in user.blocking]

    # Base query for profiles
    query_profiles = db.select(UserProfile).where(UserProfile.user_id != user.id)

    if preferences:
        current_year = datetime.now().year
        user_birth_year = user.profile.birth.year

        # Calculate acceptable birth year range
        min_birth_year = user_birth_year - preferences.max_age
        max_birth_year = user_birth_year + preferences.min_age

        # Apply filters for age and gender
        query_profiles = query_profiles.where(
            UserProfile.gender == preferences.gender_preference,  # Compare Enums
            extract('year', UserProfile.birth).between(min_birth_year, max_birth_year)
        )

    if blocked_user_ids:
        query_profiles = query_profiles.where(UserProfile.user_id.not_in(blocked_user_ids))

    # Execute query
    profiles = db.session.execute(query_profiles).scalars().all()

    return render_template('index.html', profiles=profiles)
