from fastapi import FastAPI
from .db import  engine, Base
from .routers.user import router as UserRouter
from .routers.conference import router as ConferenceRouter
from .routers.booking import router as BookingRouter


# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(UserRouter)
app.include_router(ConferenceRouter)
app.include_router(BookingRouter)



