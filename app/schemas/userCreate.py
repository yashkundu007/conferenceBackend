from pydantic import BaseModel, Field, field_validator
from typing import List

def is_alphanumeric_with_spaces(s):
    without_spaces = s.replace(" ", "")
    return without_spaces.isalnum()

class UserCreate(BaseModel):
    user_id: str = Field(..., pattern="^[a-zA-Z0-9]+$", description="Alphanumeric string with no special characters.")
    interested_topics: str = Field(..., description="Comma-separated alphanumeric strings with spaces allowed, maximum 50 topics.")
    

    @field_validator("interested_topics", mode='before')
    def validate_interested_topics(cls, value):
        topics = [topic.strip() for topic in value.split(",") if topic.strip()]
        if len(topics) > 50:
            raise ValueError("Maximum 50 topics allowed.")
        if not all(is_alphanumeric_with_spaces(topic) for topic in topics):
            raise ValueError("Topics must be alphanumeric with spaces allowed.")
        return value
    

if __name__ == '__main__':
    user = UserCreate(
        user_id="user123",
        interested_topics="Python, Data Science, Machine Learning, AI, Deep Learning"
    )
       