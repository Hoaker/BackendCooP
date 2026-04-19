from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    sex = Column(String, nullable=True)
    status = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    entry_date = Column(String, nullable=True)
    email = Column(String, nullable=True)
    department = Column(String, nullable=True)
    bank_acc_no = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="Member")
    admin_level = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    next_of_kin_name = Column(String, nullable=True)
    next_of_kin_phone = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    records = relationship("AnnualRecord", back_populates="owner")
    transactions = relationship("Transaction", back_populates="owner")


class AnnualRecord(Base):
    __tablename__ = "annual_records"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, ForeignKey("members.member_id"))
    fiscal_year = Column(Integer)
    ordinary_savings = Column(Float, default=0.0)
    special_savings = Column(Float, default=0.0)
    investment_portion = Column(Float, default=0.0)
    loan_disbursement = Column(Float, default=0.0)
    commodity_purchase = Column(Float, default=0.0)
    muslim_community = Column(Float, default=0.0)   # NEW
    owner = relationship("Member", back_populates="records")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, ForeignKey("members.member_id"))
    account_type = Column(String)
    date = Column(String)
    description = Column(String)
    amount = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    owner = relationship("Member", back_populates="transactions")
