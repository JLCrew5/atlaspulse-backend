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
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:30px 0;font-family:Arial,Helvetica,sans-serif;">
  <tr>
    <td align="center">
      <img src="https://atlaspulse.io/logo.png" alt="AtlasPulse Logo"
           style="width:160px;margin-bottom:20px;border-radius:8px;" />

      <table width="600" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:12px;padding:24px;color:#f1f5f9;">
        <tr>
          <td style="font-size:24px;font-weight:bold;color:#38bdf8;padding-bottom:10px;">
            New Signup Received
          </td>
        </tr>

        <tr>
          <td style="font-size:15px;line-height:1.6;">
            <strong>Name:</strong> {data.name}<br>
            <strong>Email:</strong> {data.email}<br>
            <strong>Role:</strong> {data.role or "Not provided"}<br>
            <strong>Property:</strong> {data.property or "Not provided"}<br>
            <strong>Funding Interest:</strong> {data.funding}<br><br>

            <strong>Message:</strong><br>
            <div style="background:#0f172a;padding:12px;border-radius:8px;margin-top:6px;color:#e2e8f0;">
              {data.message or "No message provided."}
            </div>
          </td>
        </tr>

        <tr>
          <td style="padding-top:20px;font-size:12px;color:#94a3b8;text-align:center;">
            Internal notification – sent automatically by the AtlasPulse signup form.
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""
        })
    except Exception as e:
        print("❌ Error sending admin email:", e)

    # ---------------------------
    # SEND AUTO-REPLY TO USER
    # ---------------------------
    try:
        resend.Emails.send({
            "from": "AtlasPulse <hello@atlaspulse.io>",
            "to": data.email,
            "subject": "Welcome to AtlasPulse — You're In!",
            "html": f"""
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#0f172a;padding:30px 0;font-family:Arial,Helvetica,sans-serif;color:#e5e7eb;">
  <tr>
    <td align="center">
      <img src="https://atlaspulse.io/logo.png" alt="AtlasPulse Logo"
           style="width:180px;margin-bottom:22px;border-radius:8px;" />

      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#1e293b;border-radius:14px;padding:26px;color:#f1f5f9;text-align:left;">
        <tr>
          <td style="font-size:24px;font-weight:bold;color:#38bdf8;margin-bottom:12px;">
            Welcome to AtlasPulse!
          </td>
        </tr>

        <tr>
          <td style="font-size:15px;line-height:1.6;color:#e2e8f0;">
            Thanks for joining the early access list — I’m excited you’re here.
            <br><br>
            AtlasPulse is being built for real casino floors, with real operators guiding every
            feature. Your interest helps shape the platform and gives you a front-row seat as it
            evolves.
          </td>
        </tr>

        <tr>
          <td style="padding-top:20px;">
            <div style="background:#0f172a;padding:16px;border-radius:12px;border:1px solid rgba(148,163,184,0.25);">
              <p style="margin:0 0 8px;"><strong>Your Name:</strong> {data.name}</p>
              <p style="margin:6px 0;"><strong>Your Role:</strong> {data.role or "Not provided"}</p>
              <p style="margin:6px 0;"><strong>Property:</strong> {data.property or "Not provided"} </p>
            </div>
          </td>
        </tr>

        <tr>
          <td style="padding-top:20px;font-size:15px;color:#9ca3af;line-height:1.6;">
            <strong>What happens next?</strong><br>
            • You’ll receive meaningful development updates (not spam)<br>
            • Early previews of new features<br>
            • Invitations for private testing when available<br>
            • Details about becoming an early backer (optional)
          </td>
        </tr>

        <tr>
          <td style="padding-top:26px;font-size:14px;color:#38bdf8;text-align:center;">
            — The AtlasPulse Team
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""
        })
    except Exception as e:
        print("❌ Error sending user email:", e)

    return {"status": "ok", "id": entry.id}




# Dependency for DB session ok
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

@app.get("/")
def root():
    return {"status": "ok", "message": "AtlasPulse backend is live"}
