from database import SessionLocal
import models

db = SessionLocal()
user = db.query(models.Member).filter(models.Member.member_id == "COOP_001").first()

print("\n=== ZIMCO DATABASE X-RAY ===")
if user:
    print(f"Member ID: {user.member_id}")
    print(f"Full Name: {user.full_name}")
    print(f"Has Password Hash?: {'YES - It is secured' if user.password_hash else 'NO - IT IS EMPTY'}")
else:
    print("ERROR: User COOP_001 does not exist in the database at all.")
print("============================\n")
