
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
        
        # List of encodings to try
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        # Function to try reading CSV with different encodings
        def read_csv_with_encoding(file_name):
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_name, encoding=encoding)
                    print(f"Successfully read {file_name} with {encoding} encoding")
                    return df
                except UnicodeDecodeError:
                    print(f"Failed to read {file_name} with {encoding} encoding, trying next...")
                    continue
            raise Exception(f"Could not read {file_name} with any of the attempted encodings")

        # Import partners data
        partners_df = read_csv_with_encoding('partners.csv')
        partners_df.to_sql('partners', engine, if_exists='append', index=False)
        print("Partners data imported successfully")

        # Import sales data
        sales_df = read_csv_with_encoding('sales.csv')
        sales_df.to_sql('sales', engine, if_exists='append', index=False)
        print("Sales data imported successfully")

        # Import clients data
        clients_df = read_csv_with_encoding('clients.csv')
        clients_df.to_sql('clients', engine, if_exists='append', index=False)
        print("Clients data imported successfully")

    except Exception as e:
        print(f"Error importing data: {str(e)}")

if __name__ == "__main__":
    import_data()
