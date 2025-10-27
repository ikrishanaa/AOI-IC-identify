"""
Migration script to change image_ref column from VARCHAR(512) to TEXT
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/inspection_db")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Alter the column type
    conn.execute(text("ALTER TABLE inspection_jobs ALTER COLUMN image_ref TYPE TEXT;"))
    conn.commit()
    print("✓ Successfully changed image_ref column to TEXT")
