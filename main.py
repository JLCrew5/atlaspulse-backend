from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
import resend, os

# Load API key from environment
resend.api_key = os.getenv("RESEND_API_KEY")

models.Base.metadata.create_all(bind=engine)

def build_user_email(funding):
    if funding == "yes":
        return """
        <h2>Welcome, Early Backer!</h2>
        <p>Thank you for being interested in financially supporting AtlasPulse.</p>
        <p>You’ll receive private updates, early previews, and details on Backer tiers.</p>
        """

    if funding == "maybe":
        return """
        <h2>Thanks for Joining!</h2>
        <p>You’re marked as “Maybe” for early backing.</p>
        <p>I’ll send updates so you can decide when you're ready.</p>
        """

    return """
        <h2>Welcome to AtlasPulse!</h2>
        <p>Thanks for joining the early-access list.</p>
        <p>You’ll get meaningful updates and feature previews as we progress.</p>
    """


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

    # ---------------------------
    # SEND ADMIN NOTIFICATION
    # ---------------------------
    try:
        resend.Emails.send({
            "from": "AtlasPulse <noreply@atlaspulse.io>",
            "to": "johnny5458283@gmail.com",
            "subject": f"New AtlasPulse Signup — {data.name}",
            "html": f"""
                <h2>New Signup</h2>
                <p><strong>Name:</strong> {data.name}</p>
                <p><strong>Email:</strong> {data.email}</p>
                <p><strong>Role:</strong> {data.role}</p>
                <p><strong>Property:</strong> {data.property}</p>
                <p><strong>Funding Interest:</strong> {data.funding}</p>
                <p><strong>Message:</strong><br>{data.message or "No message"}</p>
            """
        })
    except Exception as e:
        print("❌ Error sending admin email:", e)

    # ---------------------------
    # SEND AUTO-REPLY TO USER
    # ---------------------------
    try:
        thank_you_html = build_user_email(data.funding)

        resend.Emails.send({
            "from": "AtlasPulse <hello@atlaspulse.io>",
            "to": data.email,
            "subject": "Thanks for joining AtlasPulse",
            "html": thank_you_html
        })
    except Exception as e:
        print("❌ Error sending user email:", e)

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
