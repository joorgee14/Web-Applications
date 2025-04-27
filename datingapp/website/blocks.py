from flask import Blueprint, render_template
from website.model import db,  User, BlockingAssociation
from flask import request, redirect, url_for, flash
from flask_login import current_user, login_required
import flask_login
from flask_login import current_user



blocks = Blueprint('blocks', __name__)


@blocks.route('/block/<int:user_id>', methods = ['POST'])
@flask_login.login_required
def block_user(user_id):
    # Check if the user is trying to block themselves
    if user_id == current_user.id:
        flash("You cannot block yourself", "danger")
        return redirect(url_for('profile.view_profile', user_id=current_user.id))
    
    #Check if the user exists:
    query = db.select(User).where(User.id == user_id)
    blocked_user = db.session.execute(query).scalar_one_or_none()
    if not blocked_user:
        flash("The user does not exists", "danger")
        return redirect(url_for('profile.view_profile', user_id = current_user.id))
    
    #Check if the user is already blocked:
    if blocked_user in current_user.blocking:
        flash("You have already blocked this user", "info")
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # Block:
    current_user.blocking.append(blocked_user)
    db.session.commit()
    
    flash(f"You have blocked {blocked_user.first_name} {blocked_user.last_name}", "success")
    return redirect(url_for('profile.view_profile', user_id=user_id))


@blocks.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    # Check if the user exists
    query = db.select(User).where(User.id == user_id)
    blocked_user = db.session.execute(query).scalar_one_or_none()
    if not blocked_user:
        flash("User not found", "danger")
        return redirect(url_for('profile.view_profile', user_id=current_user.id))

    # Check if the user is blocked
    if blocked_user not in current_user.blocking:
        flash("You haven't blocked this user yet", "info")
        return redirect(url_for('profile.view_profile', user_id=user_id))

    # Remove the block
    current_user.blocking.remove(blocked_user)
    db.session.commit()
    flash(f"You have unblocked {blocked_user.first_name} {blocked_user.last_name}", "success")
    return redirect(url_for('profile.view_profile', user_id=user_id))


@blocks.route('/my_blocks')
@login_required
def my_blocks():
    # Get all users blocked by the current user
    blocked_users = current_user.blocking
    return render_template('blocked_users.html', blocked_users=blocked_users)   