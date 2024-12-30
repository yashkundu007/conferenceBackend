from pydantic import BaseModel

class BookingCreate(BaseModel):
    conference_name: str
    user_id: str
