from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from ..db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    interested_topics = Column(Text, nullable=False)

    # Relationship with bookings
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
