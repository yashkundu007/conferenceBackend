from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..models.booking import Booking, BookingStatus
from ..models.user import User
from ..models.conference import Conference
from ..schemas.bookingCreate import BookingCreate
from datetime import timedelta
import datetime
from ..dependency import get_db

router = APIRouter(
    prefix='/bookings'
)

def remove_from_overlapping_waitlists(user_id: str, conference: Conference, db: Session):
    overlapping_waitlist_bookings = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status == BookingStatus.waitlist,
        Booking.conference_name != conference.name,
        (
            (Booking.conference.start_timestamp <= conference.start_timestamp) & 
            (Booking.conference.end_timestamp >= conference.end_timestamp)
        ) |
        (
            (Booking.conference.start_timestamp >= conference.start_timestamp) & 
            (Booking.conference.start_timestamp < conference.end_timestamp)
        ) |
        (
            (Booking.conference.end_timestamp > conference.start_timestamp) & 
            (Booking.conference.end_timestamp <= conference.end_timestamp)
        )
    ).all()

    for booking in overlapping_waitlist_bookings:
        booking.status = BookingStatus.cancelled
        db.commit()
        db.refresh(booking)


@router.post("/create")
def book_conference(booking: BookingCreate, db: Session = Depends(get_db)):
    
    conference = db.query(Conference).filter(Conference.name == booking.conference_name).first()
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found.")

    
    user = db.query(User).filter(User.user_id == booking.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    
    active_booking = db.query(Booking).filter(
        Booking.user_id == booking.user_id,
        Booking.conference_name == conference.name,
        Booking.status != BookingStatus.cancelled
    ).first()

    if active_booking:
        raise HTTPException(
            status_code=400,
            detail=f"User already has an active booking for this conference. Existing booking ID: {active_booking.id}"
        )

   
    overlapping_bookings = db.query(Booking).filter(
        Booking.user_id == booking.user_id,
        # can also do Booking.status != BookingStatus.cancelled here (chose this instead)
        Booking.status == BookingStatus.confirmed,
        (
            (Booking.conference.start_timestamp <= conference.start_timestamp) & 
            (Booking.conference.end_timestamp >= conference.end_timestamp)
        ) |
        (
            (Booking.conference.start_timestamp >= conference.start_timestamp) & 
            (Booking.conference.start_timestamp < conference.end_timestamp)
        ) |
        (
            (Booking.conference.end_timestamp > conference.start_timestamp) & 
            (Booking.conference.end_timestamp <= conference.end_timestamp)
        )
    ).count()

    if overlapping_bookings:
        raise HTTPException(status_code=400, detail="User has overlapping conference bookings.")

    has_waitlist = db.query(Booking).filter(
        Booking.conference_name==booking.conference_name,
        Booking.status==BookingStatus.waitlist,
    ).count()
    
    # TODO add transaction here
    if conference.available_slots > 0 and has_waitlist==0:
        # Confirm the booking
        new_booking = Booking(
            user_id=booking.user_id,
            conference_name=conference.name,
            status=BookingStatus.confirmed,
            booked_at=datetime.datetime.now(datetime.UTC)
        )
        conference.available_slots -= 1  # Reduce the number of available slots
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        remove_from_overlapping_waitlists(booking.user_id, conference, db)
        
        return {"message": "Booking successful.", "booking_id": new_booking.id}
    
    else:
        # Add the user to the waitlist
        new_booking = Booking(
            user_id=booking.user_id,
            conference_name=conference.name,
            status="waitlist",
            booked_at=datetime.datetime.now(datetime.UTC),
            waitlisted_at=datetime.datetime.now(datetime.UTC)
        )
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {"message": "Booking added to waitlist.", "booking_id": new_booking.id}


def add_confirm_expires_to_first_k_waitlists(conference: Conference, db: Session):
    k = conference.available_slots
    waitlist_bookings = db.query(Booking).filter(
        Booking.status == BookingStatus.waitlist,
        Booking.conference_name == conference.name
    ).order_by(Booking.waitlisted_at.asc()).limit(k).all()

    for booking in waitlist_bookings:
        if booking.confirm_expires_at is None:
            booking.confirm_expires_at = datetime.datetime.now(datetime.UTC) + timedelta(hours=1)
            db.commit()
            db.refresh(booking)
    
def move_unconfirmed_waitlists_at_the_end(conference: Conference, db: Session):
    current_time = datetime.datetime.now(datetime.UTC)

    expired_waitlist_bookings = db.query(Booking).filter(
        Booking.status == BookingStatus.waitlist,
        Booking.conference_name == conference.name,
        Booking.waitlist_expires_at < current_time
    ).all()

    for booking in expired_waitlist_bookings:
        booking.waitlisted_at = booking.confirm_expires_at
        booking.conference_id = None
        db.commit()
        db.refresh(booking)
        

@router.post("/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.status == BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Booking already cancelled.")
    
    if booking.status == BookingStatus.confirmed:
        conference = db.query(Conference).filter(Conference.id == booking.conference_id).first()
        conference.available_slots += 1  
        db.commit()

    booking.status = BookingStatus.cancelled

    db.commit()
    db.refresh(booking)

    return {"message": "Booking cancelled successfully.", "booking_id": booking.id}



@router.get("/status")
def get_booking_status(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    conference = booking.conference

     # TODO: both the lines should be a conference wise transaction
    move_unconfirmed_waitlists_at_the_end(conference, db)
    add_confirm_expires_to_first_k_waitlists(conference, db)
    
    
    is_booking_confirmable = (booking.status==BookingStatus.waitlist) and (booking.confirm_expires_at is not None) 
    
    return {"booking_id": booking.id, "status": booking.status.value, 'is_booking_confirmable': is_booking_confirmable}


@router.post("/confirm")
def confirm_waitlist_booking(booking_id: int, db: Session = Depends(get_db)):
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not on waitlist")
    
    if booking.status != BookingStatus.waitlist:
        raise HTTPException(status_code=400, detail="Booking is not in waitlist")

    conference = booking.conference

    # TODO: both the lines should be a conference wise transaction
    move_unconfirmed_waitlists_at_the_end(conference, db)
    add_confirm_expires_to_first_k_waitlists(conference, db)

    # Check if the waitlist expiry time is not null and has passed
    if booking.confirm_expires_at is None:
        raise HTTPException(status_code=400, detail="Waitlist confirmation expired. (More than one hour has occured)")


    booking.status = BookingStatus.confirmed
    booking.waitlisted_at = None
    booking.confirm_expires_at = None
    conference.available_slots -= 1
    db.commit()

    remove_from_overlapping_waitlists(user_id=booking.user_id, conference=booking.conference, db=db)

    return {"message": "Booking confirmed successfully", "booking_id": booking.id}
