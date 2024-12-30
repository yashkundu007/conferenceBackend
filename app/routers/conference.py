from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..models.conference import Conference
from ..schemas.conferenceCreate import ConferenceCreate
from ..dependency import get_db

router = APIRouter()


@router.post("/conferences/")
def create_conference(conference: ConferenceCreate, db: Session = Depends(get_db)):
    # Check if conference name is unique
    existing_conference = db.query(Conference).filter(Conference.name == conference.name).first()
    if existing_conference:
        raise HTTPException(status_code=400, detail="Conference name already exists.")
    

    # Create and add the conference to the database
    new_conference = Conference(
        name=conference.name,
        location=conference.location,
        topics=conference.topics,
        start_timestamp=conference.start_timestamp,
        end_timestamp=conference.end_timestamp,
        available_slots=conference.available_slots
    )
    db.add(new_conference)
    db.commit()
    db.refresh(new_conference)

    return {
        "message": "Conference created successfully.",
        "conference": {
            "name": new_conference.name,
            "location": new_conference.location,
            "topics": new_conference.topics.split(","),
            "start_timestamp": new_conference.start_timestamp,
            "end_timestamp": new_conference.end_timestamp,
            "available_slots": new_conference.available_slots
        }
    }