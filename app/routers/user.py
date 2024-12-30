from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.userCreate import UserCreate
from ..dependency import get_db

router = APIRouter()


@router.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.user_id == user.user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="UserID already exists.")
    
    # Create and add the user to the database
    new_user = User(
        user_id=user.user_id,
        interested_topics=user.interested_topics
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully.",
        "user": {
            "user_id": new_user.user_id,
            "interested_topics": new_user.interested_topics
        }
    }