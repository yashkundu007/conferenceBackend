from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from ..db import Base
from enum import Enum as PyEnum


class BookingStatus(PyEnum):
    confirmed = "confirmed"
    waitlist = "waitlist"
    cancelled = "cancelled"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    conference_name = Column(String, ForeignKey("conferences.name"), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.confirmed)
    booked_at = Column(DateTime, nullable=False)
    waitlisted_at = Column(DateTime, nullable=True)
    confirm_expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookings")
    conference = relationship("Conference", back_populates="bookings")
