from flask import Blueprint, render_template, request, redirect, url_for, flash
from website.model import db, Event, EventParticipant
from flask_login import current_user, login_required
from datetime import datetime

events = Blueprint('events', __name__)


@events.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        event_date = request.form.get('event_date')
        event_time = request.form.get('event_time')

        # Validate input
        if not title or not event_date or not event_time:
            flash('Title, date, and time are required.', 'danger')
            return redirect(url_for('events.create_event'))

        try:
            # Combine date and time into a datetime object
            event_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')

            # Check if the event date is in the past
            if event_datetime < datetime.now():
                flash('Event date and time must be in the future.', 'danger')
                return redirect(url_for('events.create_event'))

            # Create and save the event
            query = db.insert(Event).values(
                title=title,
                description=description,
                location=location,
                event_date=event_datetime,
                created_by=current_user.id
            )
            db.session.execute(query)
            db.session.commit()

            flash('Event created successfully!', 'success')
            return redirect(url_for('events.view_events'))
        except ValueError:
            flash('Invalid date or time format. Please try again.', 'danger')
            return redirect(url_for('events.create_event'))

    # Render event creation form
    return render_template('create_event.html')


@events.route('/register_event/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    # Check if the user is already registered
    query = db.select(EventParticipant).where(
        EventParticipant.user_id == current_user.id,
        EventParticipant.event_id == event_id
    )
    existing_registration = db.session.execute(query).scalar_one_or_none()

    if existing_registration:
        flash('You are already registered for this event.', 'warning')
        return redirect(url_for('events.view_events'))

    # Register the user for the event
    query = db.insert(EventParticipant).values(
        user_id=current_user.id,
        event_id=event_id
    )
    db.session.execute(query)
    db.session.commit()

    flash('Successfully registered for the event!', 'success')
    return redirect(url_for('events.view_events'))

@events.route('/events', methods=['GET'])
@login_required
def view_events():
    # Fetch all events
    query = db.select(Event)
    events = db.session.execute(query).scalars().all()

    return render_template('view_events.html', events=events)


