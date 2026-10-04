import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import engine, get_session

def fix_d3():
    db = next(get_session())
    
    # Run direct SQL to bypass SQLAlchemy flush ordering issues
    print("Fixing D3 by pointing villages to the MIN district_id for each uppercase name...")
    
    # 1. Update villages to point to the canonical district ID (min ID per state_id/upper_name)
    update_sql = """
    WITH CanonicalDistricts AS (
        SELECT state_id, UPPER(name) as upper_name, MIN(id) as canonical_id
        FROM districts
        GROUP BY state_id, UPPER(name)
    )
    UPDATE villages v
    SET district_id = cd.canonical_id
    FROM districts d
    JOIN CanonicalDistricts cd ON d.state_id = cd.state_id AND UPPER(d.name) = cd.upper_name
    WHERE v.district_id = d.id AND v.district_id != cd.canonical_id;
    """
    db.execute(text(update_sql))
    
    # 2. Delete the duplicate districts (those whose IDs are not the canonical IDs)
    delete_sql = """
    WITH CanonicalDistricts AS (
        SELECT MIN(id) as canonical_id
        FROM districts
        GROUP BY state_id, UPPER(name)
    )
    DELETE FROM districts
    WHERE id NOT IN (SELECT canonical_id FROM CanonicalDistricts);
    """
    res = db.execute(text(delete_sql))
    print(f"Deleted {res.rowcount} duplicate districts.")
    
    # 3. Uppercase all remaining districts
    uppercase_sql = """
    UPDATE districts SET name = UPPER(name);
    """
    db.execute(text(uppercase_sql))
    
    db.commit()
    print("Database D3 fixed via raw SQL!")

if __name__ == "__main__":
    fix_d3()
