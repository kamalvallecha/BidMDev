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

        # List of encodings to try
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        partners_df = None

        # Try different encodings
        for encoding in encodings:
            try:
                partners_df = pd.read_csv('partners_upload.csv', encoding=encoding)
                print(f"Successfully read CSV with {encoding} encoding")
                break
            except UnicodeDecodeError:
                print(f"Failed to read with {encoding} encoding, trying next...")
                continue

        if partners_df is None:
            raise Exception("Could not read the CSV file with any of the attempted encodings")

        # Create database connection
        try:
            engine = create_engine(get_db_connection_string())
            print("Database connection established")
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            return

        # Select and rename columns to match schema
        partners_df = partners_df[[
            'partner_id',
            'partner_name',
            'contact_person',
            'contact_email',
            'contact_phone',
            'website',
            'company_address',
            'specialized',
            'geographic_coverage'
        ]]
        
        # Fill missing company_address and contact_phone with 'NA'
        partners_df['company_address'] = partners_df['company_address'].fillna('NA')
        partners_df['contact_phone'] = partners_df['contact_phone'].fillna('NA')
        
        # Convert string arrays to proper PostgreSQL arrays
        partners_df['specialized'] = partners_df['specialized'].apply(lambda x: '{' + ','.join(str(x).split(',')) + '}' if pd.notna(x) else None)
        partners_df['geographic_coverage'] = partners_df['geographic_coverage'].apply(lambda x: '{' + ','.join(str(x).split(',')) + '}' if pd.notna(x) else None)

        # Import data
        try:
            partners_df.to_sql('partners', engine, if_exists='append', index=False)
            print("Partners data imported successfully")
        except Exception as e:
            print(f"Error importing to database: {str(e)}")
            return

    except Exception as e:
        print(f"Error in import process: {str(e)}")

if __name__ == "__main__":
    import_partners()