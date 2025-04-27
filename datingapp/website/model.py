from website import db
import flask_login
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, func, Date
from datetime import datetime, date
from typing import List, Optional
from enum import Enum
import pathlib
from flask import current_app

class LikingAssociation(db.Model):
    liker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    liked_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)

class BlockingAssociation(db.Model):
    blocker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)

class User(db.Model, flask_login.UserMixin):
    id : Mapped[int] = mapped_column(primary_key=True)
    username : Mapped[str] = mapped_column(
        String(100), unique=True
    )
    first_name : Mapped[str] = mapped_column(
        String(100)
    )
    last_name: Mapped[str] = mapped_column(
        String(100)
    )
    email : Mapped[str] = mapped_column(
        String(128), unique=True
    )
    password : Mapped[str] = mapped_column(
        String(128)
    )

    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False)
    matches: Mapped["MatchingPreference"] = relationship("MatchingPreference", back_populates="user", uselist=False)
    sent_proposals: Mapped[List["DateProposal"]] = relationship(
        "DateProposal", back_populates="proposer", foreign_keys="DateProposal.proposer_id"
    )
    received_proposals: Mapped[List["DateProposal"]] = relationship(
        "DateProposal", back_populates="recipient", foreign_keys="DateProposal.recipient_id"
    )
    liking: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liker_id == id,
        secondaryjoin=LikingAssociation.liked_id == id,
        back_populates="likers",
    )
    likers: Mapped[List["User"]] = relationship(
        secondary=LikingAssociation.__table__,
        primaryjoin=LikingAssociation.liked_id == id,
        secondaryjoin=LikingAssociation.liker_id == id,
        back_populates="liking",
    )
    blocking: Mapped[List["User"]] = relationship(
        secondary=BlockingAssociation.__table__,
        primaryjoin=BlockingAssociation.blocker_id == id,
        secondaryjoin=BlockingAssociation.blocked_id == id,
        back_populates="blockers",
    )
    blockers: Mapped[List["User"]] = relationship(
        secondary=BlockingAssociation.__table__,
        primaryjoin=BlockingAssociation.blocked_id == id,
        secondaryjoin=BlockingAssociation.blocker_id == id,
        back_populates="blocking",
    )
    created_events: Mapped[List["Event"]] = relationship("Event", back_populates="creator")
    registered_events: Mapped[List["Event"]] = relationship("EventParticipant", back_populates="user")



class Photo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped["UserProfile"] = relationship(back_populates="photo")
    file_extension: Mapped[str] = mapped_column(String(8))

class GenderPreference(Enum):
    Male = 1
    Female = 2
    Other = 3
    
class UserProfile(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'), unique=True
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="profile", single_parent=True
    )
    gender: Mapped[GenderPreference]
    birth: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(512))
    photo_id: Mapped[int] = mapped_column(ForeignKey("photo.id"), nullable=True)
    photo: Mapped[Optional["Photo"]] = relationship(back_populates="profile")
  

def photo_filename(photo):
    "Generates the file path for a photo."
    path = (
        pathlib.Path(current_app.root_path)
        / "static"
        / "photos"
        / f"photo-{photo.id}.{photo.file_extension}"
    )
    return path

class MatchingPreference(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id : Mapped[int] = mapped_column(
        ForeignKey('user.id'), unique=True
    )
    user : Mapped["User"] = relationship(
        "User", back_populates="matches",
        single_parent=True
    )
    gender_preference: Mapped[GenderPreference]
    min_age: Mapped[int] = mapped_column()
    max_age: Mapped[int] = mapped_column()


class ProposalStatus(Enum):
    proposed = 1
    accepted = 2
    rejected = 3
    ignored = 4
    reschedule = 5

class DateProposal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    proposer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    proposer: Mapped["User"] = relationship(
        "User", foreign_keys=[proposer_id], back_populates="sent_proposals"
    )
    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    recipient: Mapped["User"] = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_proposals"
    )
    date_time: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ProposalStatus]
    
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    optional_text_proposal: Mapped[Optional[str]] = mapped_column(
        String(100)
    )
    optional_text_response: Mapped[Optional[str]] = mapped_column(
        String(100)
    )

class Event(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(512))
    location: Mapped[str] = mapped_column(String(150))
    event_date: Mapped[datetime] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey('user.id'))
    creator: Mapped["User"] = relationship("User", back_populates="created_events")
    participants: Mapped[List["EventParticipant"]] = relationship("EventParticipant", back_populates="event")

class EventParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    event_id: Mapped[int] = mapped_column(ForeignKey('event.id'))
    event: Mapped["Event"] = relationship("Event", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="registered_events")


