from flask import Blueprint, render_template
from website.model import db, DateProposal, ProposalStatus, User, BlockingAssociation
from flask import request, redirect, url_for, flash
from flask_login import current_user
import flask_login
from datetime import datetime
from sqlalchemy import func
from datetime import datetime
from flask_login import current_user

proposals = Blueprint('proposals', __name__)

TOTAL_TABLES = 10

@proposals.route('/propose_date/<int:recipient_id>', methods=['GET', 'POST'])
@flask_login.login_required
def propose_date(recipient_id):
    user = current_user

    # Ensure recipient exists:
    query = db.select(User).where(User.id == recipient_id)
    recipient = db.session.execute(query).scalar_one_or_none()
    if not recipient:
        flash("Recipient not found", "danger")
        return redirect(url_for("main.index"))
    
    # Check if current user is blocked by the recipient:
    query = db.select(BlockingAssociation).where(
        BlockingAssociation.blocker_id == recipient_id,
        BlockingAssociation.blocked_id == user.id
    )
    is_blocked = db.session.execute(query).scalar_one_or_none()
    if is_blocked:
        flash("You cannot propose a date to this user", "danger")
        return redirect(url_for("main.index"))
    
    if recipient_id == user.id:
        flash("You cannot propose a date to yourself", "danger")
        return redirect(url_for("main.index"))
    
    if request.method == "POST":
        # Retrieve date input
        date = request.form.get("date")
        optional_text = request.form.get("optional_text_proposal")

        if not date:
            flash("Date is required.", "danger")
            return redirect(url_for("proposals.propose_date", recipient_id=recipient_id))

        try:
            proposed_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("proposals.propose_date", recipient_id=recipient_id))

        if proposed_date <= datetime.today().date():
            flash("Invalid date. Please choose a future date.", "danger")
            return redirect(url_for("proposals.propose_date", recipient_id=recipient_id))

        # Check if the user has already proposed a date for the same day
        query = db.select(DateProposal).where(
            DateProposal.proposer_id == user.id,
            DateProposal.recipient_id == recipient_id,
            DateProposal.date_time == proposed_date  
        )
        existing_proposal = db.session.execute(query).scalar_one_or_none()
        if existing_proposal:
            flash(f"You have already proposed a date for {proposed_date} to this user.", "info")
            return redirect(url_for("proposals.propose_date", recipient_id=recipient_id))
        
        # Check if there are already enough active proposals for the proposed date
        query = db.select(func.count(DateProposal.id)).where(
            DateProposal.date_time == proposed_date,  
            DateProposal.status.in_([ProposalStatus.proposed, ProposalStatus.accepted])
        )
        active_proposals = db.session.execute(query).scalar()
        
        if active_proposals >= TOTAL_TABLES:
            flash("Sorry, all tables are taken for this date.", "danger")
            return redirect(url_for("proposals.propose_date", recipient_id=recipient_id))
        
        # Create a new proposal
        proposal = DateProposal(
            proposer_id=user.id,
            recipient_id=recipient_id,
            date_time=proposed_date,  
            status=ProposalStatus.proposed,
            optional_text_proposal=optional_text
        )
        db.session.add(proposal)
        db.session.commit()
        flash("Date proposal sent!", "success")
        return redirect(url_for("profile.view_profile", user_id=recipient_id))

    return render_template('propose_date.html', recipient=recipient)


@proposals.route("/respond_to_proposal/<int:proposal_id>", methods=["POST", "GET"])
@flask_login.login_required
def respond_to_proposal(proposal_id):
    user = current_user

    # Get the proposal
    query = db.select(DateProposal).where(DateProposal.id == proposal_id)
    proposal = db.session.execute(query).scalar_one_or_none()
    if not proposal:
        flash("Proposal not found", "danger")
        return redirect(url_for("main.index"))

    if proposal.recipient_id != user.id:
        flash("You are not authorized to respond to this proposal.", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        action = request.form.get("action")
        optional_text_response = request.form.get("optional_text_response")
        new_date = request.form.get("new_date")

        # Validate the action
        action_map = {
            "accept": ProposalStatus.accepted,
            "reject": ProposalStatus.rejected,
            "reschedule": ProposalStatus.reschedule,
            "ignore": ProposalStatus.ignored
        }

        if action not in action_map:
            flash("Invalid action")
            return redirect(url_for("proposals.respond_to_proposal", proposal_id=proposal_id))

        # If rescheduling, validate and create a new proposal
        if action == "reschedule":
            if not new_date:
                flash("Please select a new date for rescheduling.", "danger")
                return redirect(url_for("proposals.respond_to_proposal", proposal_id=proposal_id))

            try:
                new_proposed_date = datetime.strptime(new_date, "%Y-%m-%d").date()
                if new_proposed_date <= datetime.today().date():
                    flash("Invalid date. Please select a future date.", "danger")
                    return redirect(url_for("proposals.respond_to_proposal", proposal_id=proposal_id))
            except ValueError:
                flash("Invalid date format.", "danger")
                return redirect(url_for("proposals.respond_to_proposal", proposal_id=proposal_id))

            # Check if there are already proposals for the selected date (Same as before, but, with the recipient being the proposer)
            query = db.select(DateProposal).where(
                DateProposal.date_time == new_proposed_date,
                DateProposal.recipient_id == proposal.proposer_id,  # The recipient is the one proposing the new date
                DateProposal.proposer_id == proposal.recipient_id,
                DateProposal.status.in_([ProposalStatus.proposed, ProposalStatus.accepted, ProposalStatus.reschedule])
            )
            existing_proposal = db.session.execute(query).scalar_one_or_none()
            if existing_proposal:
                flash(f"There is already a proposal for {new_proposed_date}. Please choose a different date.", "danger")
                return redirect(url_for("proposals.respond_to_proposal", proposal_id=proposal_id))

            # Mark the current proposal as rescheduled
            proposal.status = ProposalStatus.reschedule
            proposal.optional_text_response = optional_text_response
            proposal.response_timestamp = datetime.utcnow()

            # Create a new proposal with the rescheduled date
            new_proposal = DateProposal(
                proposer_id=proposal.recipient_id,
                recipient_id=proposal.proposer_id,
                date_time=new_proposed_date,
                status=ProposalStatus.proposed,
                optional_text_proposal=proposal.optional_text_proposal,
            )
            db.session.add(new_proposal)

            db.session.commit()
            flash("Proposal rescheduled!", "success")
            return redirect(url_for("proposals.received_proposals"))
        
        # Handle other actions (accept/reject)
        proposal.status = action_map[action]
        proposal.optional_text_response = optional_text_response
        proposal.response_timestamp = datetime.utcnow()

        db.session.commit()
        flash(f"Proposal has been {action}ed!", "success")
        return redirect(url_for("proposals.received_proposals"))


    return render_template("respond_to_proposal.html", proposal=proposal, ProposalStatus=ProposalStatus)



@proposals.route('/sent_proposals', methods=['GET'])
@flask_login.login_required
def sent_proposals():
    user = current_user

    # Query proposals sent by the user, including response details
    query = db.select(DateProposal).where(DateProposal.proposer_id == user.id)
    proposals = db.session.execute(query).scalars().all()

    #If recipient ignored the proposal, the proposal is marked as proposed:
    for proposal in proposals:
        if proposal.status == ProposalStatus.ignored:
            proposal.status = ProposalStatus.proposed
    

    return render_template('sent_proposals.html', proposals=proposals)



@proposals.route('/received_proposals', methods=['GET'])
@flask_login.login_required
def received_proposals():
    user = current_user

    # Query proposals received by the user that are not rejected or ignored
    query = db.select(DateProposal).where(
        (DateProposal.recipient_id == user.id) &
        (DateProposal.status.notin_([ProposalStatus.rejected, ProposalStatus.ignored]))
    )
    proposals = db.session.execute(query).scalars().all()

    return render_template('received_proposals.html', proposals=proposals, ProposalStatus=ProposalStatus)
