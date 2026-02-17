import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# 1. Load your .env file
load_dotenv()

# 2. Get the Cloud URL
DB_URL = os.getenv("DATABASE_URL")

def migrate_data():
    if not DB_URL:
        print("❌ Error: DATABASE_URL not found in .env")
        return

    conn = None
    try:
        # --- PATH FIX ---
        base_path = os.path.dirname(__file__)
        csv_path = os.path.join(base_path, 'data', 'locations.csv')
        
        print(f"📖 Looking for CSV at: {csv_path}")
        
        # --- CSV FORMATTING FIX ---
        df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
        print(f"✅ Loaded {len(df)} locations from CSV.")

        # --- CONNECT WITH TIMEOUT & SSL ---
        print("🔗 Connecting to Supabase Cloud...")
        # Adding connect_timeout and sslmode helps bypass local network glitches
        conn = psycopg2.connect(
            DB_URL, 
            connect_timeout=20, 
            sslmode='require'
        )
        cur = conn.cursor()

        # Clean the table
        print("🧹 Cleaning the table for a fresh start...")
        cur.execute("TRUNCATE TABLE locations RESTART IDENTITY;")

        # Insert rows
        print(f"🚀 Uploading data to the cloud...")
        for _, row in df.iterrows():
            insert_query = """
            INSERT INTO locations (name, category, latitude, longitude, entry_fee, city, country, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (
                row['name'], row['category'], row['latitude'], 
                row['longitude'], row['entry_fee'], row['city'], 
                row['country'], row['description']
            ))

        conn.commit()
        print("✅ SUCCESS! Your data is now live in Supabase.")

    except Exception as e:
        print(f"❌ Migration Failed: {e}")
        print("\n💡 Pro-Tip: If you still see 'name resolution' errors, try switching your Wi-Fi or turning off your VPN.")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    migrate_data()