"""
Data Extraction Script for Demand Forecasting.
Extracts transactional order lines aggregated to weekly demand from NeonDB (ecom schema)
and caches the result in data/raw/weekly_demand.csv.
"""

import os
import sys
from pathlib import Path
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Resolve repository root
ROOT_DIR = Path(__file__).resolve().parent.parent

def extract_weekly_demand() -> pd.DataFrame:
    # Load environment variables
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "neondb")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        if not (host and user and password):
            raise ValueError("DATABASE_URL or DB connection variables not configured in .env")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

    sql_file = ROOT_DIR / "sql" / "extract_weekly_demand.sql"
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found at {sql_file}")

    with open(sql_file, "r", encoding="utf-8") as f:
        query = f.read()

    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)
    try:
        print("Executing weekly demand extraction query...")
        df = pd.read_sql_query(query, conn)
        print(f"Extracted {len(df):,} aggregated records.")
        
        # Ensure output directory exists
        out_dir = ROOT_DIR / "data" / "raw"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "weekly_demand.csv"
        
        df.to_csv(out_path, index=False)
        print(f"Successfully saved to {out_path}")
        
        if not df.empty:
            print(f"Date range: {df['week_start'].min()} to {df['week_start'].max()}")
            print(f"Total categories: {df['category_name'].nunique()}")
            print(f"Total units demanded: {df['units_demanded'].sum():,}")
        return df
    finally:
        conn.close()

if __name__ == "__main__":
    extract_weekly_demand()
