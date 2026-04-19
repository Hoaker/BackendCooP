from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
import security

# Initialize the FastAPI app
app = FastAPI(title="ZIMCO Cooperative API")

# Setup CORS to allow your Google Stitch React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allows any frontend (localhost:5173, etc.)
    allow_credentials=False,  # Set to False so the wildcard '*' works without crashing
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database Dependency - Opens and closes the connection safely per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# PYDANTIC MODELS (Data Validation)
# ==========================================
class SetupAccountData(BaseModel):
    coop_id: str
    password: str

class LoginData(BaseModel):
    coop_id: str
    password: str

class ChangePasswordData(BaseModel):
    coop_id: str
    old_password: str
    new_password: str

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/")
def read_root():
    return {"message": "ZIMCO Backend Server is Running securely!"}

# 1. SETUP ACCOUNT (Run this once per user to claim their imported profile)
@app.post("/api/auth/setup")
def setup_account(data: SetupAccountData, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.member_id == data.coop_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="COOP_ID not found in database.")
    
    if member.password_hash:
        raise HTTPException(status_code=400, detail="Account already has a password.")

    # Hash the password and save it
    member.password_hash = security.get_password_hash(data.password)
    db.commit()
    
    return {"message": f"Password successfully set for {member.full_name}"}

# 2. LOGIN (Verifies password and returns the JWT token)
@app.post("/api/auth/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.member_id == data.coop_id).first()
    
    # Check if user exists and password matches
    if not member or not member.password_hash:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
        
    if not security.verify_password(data.password, member.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    # Generate the access token
    access_token = security.create_access_token(
        data={"sub": member.member_id, "role": member.role}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "coop_id": member.member_id,
        "role": member.role,
        "admin_level": member.admin_level
    }


# 3. CHANGE PASSWORD (Allows users to update their default surname password)
@app.post("/api/auth/change-password")
def change_password(data: ChangePasswordData, db: Session = Depends(get_db)):
    # Find the member in the database
    member = db.query(models.Member).filter(models.Member.member_id == data.coop_id).first()
    
    if not member or not member.password_hash:
        raise HTTPException(status_code=404, detail="Member not found.")
        
    # Verify their old password (e.g., their surname) is correct
    if not security.verify_password(data.old_password, member.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect current password.")

    # Hash the new password and update the database
    member.password_hash = security.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Password successfully updated!"}

# 4. GET MEMBER PROFILE (Fetches biodata, financial summary, and ledger)
@app.get("/api/members/{member_id}")
def get_member_profile(member_id: str, db: Session = Depends(get_db)):
    # Search for the member
    member = db.query(models.Member).filter(models.Member.member_id == member_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in ZIMCO database")
    
    # Structure the data cleanly for the frontend
    return {
        "profile": {
            "coop_id": member.member_id,
            "name": member.full_name,
            "department": member.department,
            "phone": member.phone_number,
            "email": member.email,
            "bank_name": member.bank_name,
            "status": member.status,
            "role": member.role,
            "admin_level": member.admin_level,
            "next_of_kin_name": member.next_of_kin_name,
            "next_of_kin_phone": member.next_of_kin_phone,
            "profile_picture_url": member.profile_picture_url
        },
        "financial_summary": member.records, # The final yearly balances
        "transaction_history": member.transactions # The detailed ledger with dates
    }
