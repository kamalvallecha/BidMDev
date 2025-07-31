
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_connection_string():
    return os.environ['DATABASE_URL']

def read_csv_with_encoding(file_path):
    """Try reading CSV with different encodings"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"Successfully read {file_path} with {encoding} encoding")
            return df
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"File {file_path} not found!")
            return None
    
    print(f"Could not read {file_path} with any encoding")
    return None

def import_bids_only():
    """Import only bids data from Data Uploads/bids.csv"""
    try:
        print("Starting bids import...")
        print("=" * 40)
        
        # Read the bids CSV file
        file_path = 'Data Uploads/bids.csv'
        df = read_csv_with_encoding(file_path)
        
        if df is None:
            print("Error: Could not read bids.csv file")
            return
        
        print(f"Found {len(df)} rows in bids.csv")
        print("Columns:", list(df.columns))
        
        # Create database connection
        engine = create_engine(get_db_connection_string())
        
        # Remove the 'id' column if it exists (database will auto-generate it)
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
            print("Removed 'id' column - database will auto-generate it")
        
        # Import to bids table
        df.to_sql('bids', engine, if_exists='append', index=False)
        
        print("=" * 40)
        print("Bids imported successfully!")
        print(f"Imported {len(df)} records to bids table")
        
    except Exception as e:
        print(f"Error during bids import: {str(e)}")
        raise e

if __name__ == "__main__":
    import_bids_only()
