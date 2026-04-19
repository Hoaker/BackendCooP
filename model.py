from sqlalchemy import Column, String, Integer, Date, Boolean
from database import Base # This comes from your database setup file
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__ = "members"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, unique=True, index=True, nullable=False) # e.g., ZIM-001
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    department = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    join_date = Column(Date, nullable=True)
    records = relationship("AnnualRecord", back_populates="owner")



class AnnualRecord(Base):
    __tablename__ = "annual_records"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, ForeignKey("members.member_id"))
    fiscal_year = Column(Integer) # 2022, 2023, 2024
    
    # Your 5 specific ZIMCO portions
    ordinary_savings = Column(Integer, default=0)
    special_savings = Column(Integer, default=0)
    investment_portion = Column(Integer, default=0)
    commodity_portion = Column(Integer, default=0)
    loan_disbursement = Column(Integer, default=0)

    # Link back to the Member
    owner = relationship("Member", back_populates="records")