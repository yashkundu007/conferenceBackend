from pydantic import BaseModel, Field, field_validator, root_validator
from datetime import datetime, timedelta


def is_alphanumeric_with_spaces(s):
    without_spaces = s.replace(" ", "")
    return without_spaces.isalnum()

class ConferenceCreate(BaseModel):
    name: str = Field(..., pattern="^[a-zA-Z0-9 ]+$", description="Alphanumeric string with spaces allowed.")
    location: str = Field(..., pattern="^[a-zA-Z0-9 ]+$", description="Alphanumeric string with spaces allowed.")
    topics: str = Field(..., description="Comma-separated alphanumeric strings with spaces allowed, maximum 10 topics.")
    start_timestamp: datetime
    end_timestamp: datetime
    available_slots: int = Field(..., gt=0, description="Integer greater than 0")

    @field_validator("topics", mode='before')
    def validate_topics(cls, value):
        topics = [topic.strip() for topic in value.split(",") if topic.strip()]
        if len(topics) > 10:
            raise ValueError("Maximum 10 topics allowed.")
        if not all(is_alphanumeric_with_spaces(topic) for topic in topics):
            raise ValueError("Topics must be alphanumeric with spaces allowed.")
        return value
    
    @root_validator(pre=True)
    def check_end_timestamp(cls, values):
        start_timestamp = values.get('start_timestamp')
        end_timestamp = values.get('end_timestamp')
        
        if start_timestamp and end_timestamp:
            if isinstance(start_timestamp, str):
                start_timestamp = datetime.fromisoformat(start_timestamp)
            if isinstance(end_timestamp, str):
                end_timestamp = datetime.fromisoformat(end_timestamp)

            if end_timestamp <= start_timestamp:
                raise ValueError("End timestamp must be greater than start timestamp.")
            if end_timestamp - start_timestamp > timedelta(hours=12):
                raise ValueError("The time difference between start and end must not exceed 12 hours.")
        
        return values
