import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_connection_string():
    return os.environ['DATABASE_URL']

def import_partners():
    try:
        print("Starting partners import...")
        engine = create_engine(get_db_connection_string())

        # Import partners data
        partners_df = pd.read_csv('partners_upload.csv')
        partners_df.to_sql('partners', engine, if_exists='append', index=False)
        print("Partners data imported successfully")

    except Exception as e:
        print(f"Error importing partners data: {str(e)}")

if __name__ == "__main__":
    import_partners()