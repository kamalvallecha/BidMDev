
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_connection_string():
    return os.environ['DATABASE_URL']

def import_data():
    try:
        print("Starting data import...")
        engine = create_engine(get_db_connection_string())

        # Import partners data
        partners_df = pd.read_csv('partners.csv')
        partners_df.to_sql('partners', engine, if_exists='append', index=False)
        print("Partners data imported successfully")

        # Import sales data
        sales_df = pd.read_csv('sales.csv')
        sales_df.to_sql('sales', engine, if_exists='append', index=False)
        print("Sales data imported successfully")

        # Import clients data
        clients_df = pd.read_csv('clients.csv')
        clients_df.to_sql('clients', engine, if_exists='append', index=False)
        print("Clients data imported successfully")

    except Exception as e:
        print(f"Error importing data: {str(e)}")

if __name__ == "__main__":
    import_data()
