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
    default_hash = security.get_password_hash("password")
    print("Password hash ready.")

    print("Reading all sheets...")
    all_data = {}
    all_names = set()
    for sheet_name, month_label in MONTH_SHEETS.items():
        df = load_sheet(sheet_name)
        all_data[month_label] = df
        for name in df["COOPERATOR'S FULL NAME"].astype(str).str.strip():
            if name and name.lower() != "nan":
                all_names.add(name)
    print(f"  Found {len(all_names)} unique member names.")

    db = SessionLocal()

    existing = {m.full_name: m for m in db.query(Member).all()}
    new_members = []
    for name in all_names:
        if name not in existing:
            m = Member(
                member_id=f"NO_ID_{str(uuid.uuid4())[:6]}",
                full_name=name,
                password_hash=default_hash,
            )
            new_members.append(m)
            existing[name] = m

    if new_members:
        db.bulk_save_objects(new_members)
        db.flush()
        print(f"  Created {len(new_members)} new member records.")

    db.commit()
    member_map = {m.full_name: m.member_id
                  for m in db.query(Member.full_name, Member.member_id).all()}

    annual_totals = {}
    transaction_rows = []

    for month_label, df in all_data.items():
        print(f"  Processing {month_label} ({len(df)} rows)...")
        for _, row in df.iterrows():
            name = str(row.get("COOPERATOR'S FULL NAME", "")).strip()
            mid = member_map.get(name)
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
    print(f"  Members        : {len(member_map)}")
    print(f"  Annual records : {len(annual_totals)}")
    print(f"  Transactions   : {len(transaction_rows)}")

if __name__ == "__main__":
    print("Starting ZIMCO Bursary 2026 Import (Jan - Mar, April excluded) ...")
    import_bursary_data()
    print("Done!")
