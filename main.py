from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/list")
def list_all(db: Session = Depends(get_db)):
    records = db.query(models.Interest).order_by(models.Interest.id.desc()).all()
    return records
