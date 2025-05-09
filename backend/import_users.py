
import os
import pandas as pd
from sqlalchemy import create_engine
from config import Config

def import_users():
    try:
        print("Starting users import...")
        engine = create_engine(Config.DATABASE_URL)

        # Import users data
        users_df = pd.read_csv('users.csv')
        users_df.to_sql('users', engine, if_exists='append', index=False)
        print("Users data imported successfully")

    except Exception as e:
        print(f"Error importing users data: {str(e)}")

if __name__ == "__main__":
    import_users()
