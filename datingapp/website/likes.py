from flask import Blueprint, render_template
from website.model import db, User
from flask import redirect, url_for, flash
from flask_login import current_user
import flask_login
from flask_login import current_user


likes = Blueprint('likes', __name__)


@likes.route('/like/<int:user_id>', methods=['POST'])
@flask_login.login_required
def like_user(user_id):
    # Check if the user is trying to like themselves
    if user_id == current_user.id:
        flash("You cannot like yourself", "danger")
        return redirect(url_for('profile.view_profile', user_id=current_user.id))

    # Check if the user exists
    query = db.select(User).where(User.id == user_id)
    liked_user = db.session.execute(query).scalar_one_or_none()
    if not liked_user:
        flash("User not found", "danger")
        return redirect(url_for('profile.view_profile', user_id=current_user.id))

    # Check if the user is already liked
    if liked_user in current_user.liking:
        flash("You have already liked this user", "info")
        return redirect(url_for('profile.view_profile', user_id=user_id))

    # Add the like
    current_user.liking.append(liked_user)
    db.session.commit()
    flash(f"You have liked {liked_user.first_name} {liked_user.last_name}", "success")
    return redirect(url_for('profile.view_profile', user_id=user_id))


@likes.route('/unlike/<int:user_id>', methods=['POST'])
@flask_login.login_required
def unlike_user(user_id):
    # Check if the user exists
    query = db.select(User).where(User.id == user_id)
    liked_user = db.session.execute(query).scalar_one_or_none()
    if not liked_user:
        flash("User not found", "danger")
        return redirect(url_for('profile.view_profile', user_id=current_user.id))

    # Check if the user is liked
    if liked_user not in current_user.liking:
        flash("You haven't liked this user yet", "info")
        return redirect(url_for('profile.view_profile', user_id=user_id))

    # Remove the like
    current_user.liking.remove(liked_user)
    db.session.commit()
    flash(f"You have stopped liking {liked_user.first_name} {liked_user.last_name}", "success")
    return redirect(url_for('profile.view_profile', user_id=user_id))


@likes.route('/my_likes')
@flask_login.login_required
def my_likes():
    # Get all users liked by the current user
    liked_users = current_user.liking
    return render_template('liked_profiles.html', liked_users=liked_users)


