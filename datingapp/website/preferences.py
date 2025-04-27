from flask import Blueprint, render_template
from website.model import db, UserProfile, GenderPreference, MatchingPreference, DateProposal, ProposalStatus, User, BlockingAssociation, Photo, photo_filename
from flask import request, redirect, url_for, flash
from flask_login import current_user, login_required
import flask_login
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import extract
from datetime import datetime
from flask_login import current_user


preferences = Blueprint('preferences', __name__)

@preferences.route('/matching_preferences', methods=['GET', 'POST'])
@login_required
def matching_preferences():
    user = current_user
    query = db.select(MatchingPreference).where(MatchingPreference.user_id == user.id)
    matches = db.session.execute(query).scalar_one_or_none()

    # Create a default MatchingPreference if none exists
    if matches is None:
        matches = MatchingPreference(user_id=user.id, gender_preference=GenderPreference.Other, min_age= 50, max_age=50)
        db.session.add(matches)
        db.session.commit()

    if request.method == 'POST':
        # Get the form values
        gender_preference = request.form["gender"].capitalize()
        min_age = request.form.get("min_age", "")
        max_age = request.form.get("max_age", "")

        # Validate the gender preference
        if gender_preference not in GenderPreference.__members__:
            flash('Invalid gender preference.', 'error')
            return redirect(url_for('preferences.matching_preferences'))

        # Validate min_age and max_age to ensure they are positive and between 0 and 50 (we think that no one wants a date with a person with 50 years of difference of age)
        try:
            min_age = int(min_age)
            max_age = int(max_age)
            if not (0 <= min_age <= 50) or not (0 <= max_age <= 50):
                raise ValueError("Age values must be between 0 and 50.")
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('preferences.matching_preferences'))

        # Update `MatchingPreference` attributes
        matches.gender_preference = GenderPreference[gender_preference] 
        matches.min_age = min_age
        matches.max_age = max_age

        db.session.commit()
        flash('Matching preferences updated', 'success')
        return redirect(url_for('main.index'))

    return render_template('preferences.html', user=user, matches=matches)