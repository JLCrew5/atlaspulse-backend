from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow your atlaspulse.io frontend to submit data
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://atlaspulse.io",
        "https://www.atlaspulse.io",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Interest(BaseModel):
    name: str
    email: str
    role: str | None = None
    property: str | None = None
    message: str | None = None
    funding: str  # yes / maybe / no

@app.post("/api/interest")
def create_interest(data: Interest):
    db = SessionLocal()
    entry = models.Interest(
        name=data.name,
        email=data.email,
        role=data.role,
        property=data.property,
        message=data.message,
        funding=data.funding
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "ok", "id": entry.id}
