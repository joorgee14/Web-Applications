from flask import Blueprint, render_template
from website.model import db, UserProfile, Photo, photo_filename
from flask import request, redirect, url_for, flash
from flask_login import current_user
import flask_login
from datetime import datetime
from flask_login import current_user


profile = Blueprint('profile', __name__)


@profile.route('/edit_profile', methods=['GET', 'POST'])
@flask_login.login_required
def edit_profile():
    user = current_user
    profile = user.profile

    if request.method == 'POST':
        # Update `User` attributes
        user.first_name = request.form["first_name"]
        user.last_name = request.form["last_name"]
        db.session.commit()

        # Update `UserProfile` attributes
        profile.description = request.form["description"]

        # Handle photo upload
        uploaded_file = request.files.get('photo')
        if uploaded_file and uploaded_file.filename != '':
            # Validate file type
            content_type = uploaded_file.content_type
            if content_type == "image/png":
                file_extension = "png"
            elif content_type == "image/jpeg":
                file_extension = "jpg"
            else:
                flash(f"Unsupported file type: {content_type}", "danger")
                return redirect(url_for('main.edit_profile'))

            # Remove old photo if it exists
            if profile.photo:
                old_photo_path = photo_filename(profile.photo)
                try:
                    old_photo_path.unlink()
                except FileNotFoundError:
                    pass
                db.session.delete(profile.photo)

            # Create a new photo object
            new_photo = Photo(file_extension=file_extension)
            db.session.add(new_photo)
            db.session.commit()

            # Save the new photo file
            profile.photo = new_photo
            photo_path = photo_filename(new_photo)
            uploaded_file.save(photo_path)

        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('main.index'))

    return render_template('edit_profile.html', user=user, profile=profile)



@profile.route('/view_profile/<int:user_id>', methods=['GET'])
@flask_login.login_required
def view_profile(user_id):
    # Query the user profile:
    query = db.select(UserProfile).where(UserProfile.user_id == user_id)
    profile = db.session.execute(query).scalar_one_or_none()
    if profile is None:
        return "User not found", 404

    # Return the public properties:
    public = {
        "id": profile.user.id,  # Include user ID
        "first_name": profile.user.first_name,
        "gender": profile.gender.name if profile.gender else None,
        "birth": profile.birth,
        "description": profile.description,
        "photo": profile.photo,
    }

    return render_template('view_profile.html', profile=public)