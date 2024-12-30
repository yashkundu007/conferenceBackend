from pydantic import BaseModel

class BookingStatusRequest(BaseModel):
    booking_id: int
