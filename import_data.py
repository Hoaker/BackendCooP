import pandas as pd
import uuid
from database import SessionLocal
from models import Member, AnnualRecord, Transaction
import security

FILE_PATH = "BURSARY_DEDUCTION_FILE_(2026)_1776417752172.xlsx"
FISCAL_YEAR = 2026

MONTH_SHEETS = {
    "Jan `26 (Dr)": "January 2026",
    "Feb '26 (Dr)": "February 2026",
    "Mar 26 (Dr)":  "March 2026",
}

ACCOUNT_COLUMN_MAP = {
    "OrdSav":  "ordinary_savings",
    "SpecSav": "special_savings",
    "InvAcc":  "investment_portion",
    "LoanRem": "loan_disbursement",
    "CommPur": "commodity_purchase",
    "MusComm": "muslim_community",
}

def safe_float(value):
    try:
        val = float(value)
        return 0.0 if pd.isna(val) else val
    except (ValueError, TypeError):
        return 0.0

def load_sheet(sheet_name):
    df = pd.read_excel(FILE_PATH, sheet_name=sheet_name, header=2)
    real_headers = df.iloc[0].fillna("").astype(str).str.strip().tolist()
    df.columns = real_headers
    df = df.iloc[1:].reset_index(drop=True)
    name_col = "COOPERATOR'S FULL NAME"
    df = df[df[name_col].astype(str).str.strip().replace("nan", "") != ""]
    df = df[~df[name_col].astype(str).str.lower().str.contains(
        r"total|nan|cooperator", na=True, regex=True
    )]
    return df.reset_index(drop=True)
    
def import_bursary_data():
    db = SessionLocal()
    
    # 1. LOAD THE IDs FROM THE MEMBER LIST FILE
    print("Reading Member List for IDs...")
    list_df = pd.read_excel("List of ZIMCO member.xlsx") 
    
    # Create a map: {"FULL NAME": "COOP_ID"}
    # We store the names in uppercase for easier matching
    name_to_id = {
        str(row["FULL NAME"]).strip().upper(): str(row["COOP_ID"]).strip()
        for _, row in list_df.iterrows()
    }
    print(f" Found {len(name_to_id)} IDs in the member list.")

    # 2. LOAD THE BURSARY DATA
    print("Reading Bursary sheets...")
    all_data = {}
    for sheet_name, month_label in MONTH_SHEETS.items():
        df = load_sheet(sheet_name)
        all_data[month_label] = df

    # 3. SYNC MEMBERS TO DATABASE & SET PASSWORDS
    existing = {m.full_name: m for m in db.query(Member).all()}
    for full_name, coop_id in name_to_id.items():
        if full_name not in existing:
            # First word of the name is the surname/password
            surname = full_name.split()[0].lower()
            new_m = Member(
                member_id=coop_id,
                full_name=full_name,
                password_hash=security.get_password_hash(surname)
            )
            db.add(new_m)
    
    db.commit()
    print("Database members synchronized.")
    
    # Refresh member map for transaction processing
    member_map = {m.full_name: m.member_id for m in db.query(Member.full_name, Member.member_id).all()}

    annual_totals = {}
    transaction_rows = []

    # 4. PROCESS TRANSACTIONS WITH COMPONENT MATCHING
    for month_label, df in all_data.items():
        print(f"  Processing {month_label} ({len(df)} rows)...")
        for _, row in df.iterrows():
            bursary_name = str(row.get("COOPERATOR'S FULL NAME", "")).strip().upper()
            if not bursary_name or bursary_name == "NAN":
                continue
                
            # Attempt Fuzzy/Component Match
            mid = None
            # First try exact match
            mid = member_map.get(bursary_name)
            
            # If no exact match, try matching based on name components (Surname + First Name)
            if not mid:
                bursary_parts = set(bursary_name.split())
                for list_name, list_id in name_to_id.items():
                    list_parts = set(list_name.split())
                    # If at least 2 parts of the name match, we consider it a hit
                    if len(bursary_parts.intersection(list_parts)) >= 2:
                        mid = list_id
                        break
            
            if not mid:
                continue

            if mid not in annual_totals:
                annual_totals[mid] = {col: 0.0 for col in ACCOUNT_COLUMN_MAP.values()}
            
            for excel_col, db_col in ACCOUNT_COLUMN_MAP.items():
                amount = safe_float(row.get(excel_col, 0))
                if amount <= 0:
                    continue
                annual_totals[mid][db_col] += amount
                transaction_rows.append({
                    "member_id": mid,
                    "account_type": db_col,
                    "date": month_label,
                    "description": f"Monthly Deduction - {month_label}",
                    "amount": amount,
                    "balance": annual_totals[mid][db_col],
                })

    print(f"Saving annual records for {len(annual_totals)} members...")
    existing_records = {
        r.member_id: r for r in db.query(AnnualRecord).filter(
            AnnualRecord.fiscal_year == FISCAL_YEAR
        ).all()
    }
    
    new_records = []
    for mid, totals in annual_totals.items():
        if mid in existing_records:
            rec = existing_records[mid]
            for col, val in totals.items():
                setattr(rec, col, (getattr(rec, col) or 0.0) + val)
        else:
            new_records.append(AnnualRecord(
                member_id=mid, fiscal_year=FISCAL_YEAR, **totals
            ))
            
    if new_records:
        db.bulk_save_objects(new_records)
    db.flush()

    print(f"Saving {len(transaction_rows)} transaction entries...")
    if transaction_rows:
        db.bulk_insert_mappings(Transaction, transaction_rows)

    db.commit()
    db.close()
    print(f"\n=== Import Complete ===")
    print(f"  Members Summary : {len(name_to_id)} identified from files.")
    print(f"  Annual Records  : {len(annual_totals)} members updated.")
    print(f"  Transactions    : {len(transaction_rows)} records saved.")

if __name__ == "__main__":
    print("Starting ZIMCO Bursary 2026 Import...")
    import_bursary_data()
    print("Done!")
