
import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import json

load_dotenv()

def get_db_connection_string():
    return os.environ['DATABASE_URL']

def get_psycopg2_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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
            print(f"File {file_path} not found, skipping...")
            return None
    
    print(f"Could not read {file_path} with any encoding")
    return None

def import_users():
    """Import users data"""
    print("Importing users...")
    file_path = 'Data Uploads/users.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        print("Creating default users...")
        # Create default users if CSV not found
        conn = get_psycopg2_connection()
        cur = conn.cursor()
        
        default_password = "admin"
        hashed_password = generate_password_hash(default_password, method='pbkdf2:sha256')
        
        default_users = [
            ('admin@example.com', 'Admin User', 'ADMIN001', hashed_password, 'admin', 'Administration'),
            ('sales@example.com', 'Sales User', 'SALES001', hashed_password, 'sales', 'Sales'),
            ('vm@example.com', 'VM User', 'VM001', hashed_password, 'VM', 'Vendor Management'),
            ('pm@example.com', 'PM User', 'PM001', hashed_password, 'PM', 'Project Management')
        ]
        
        for user in default_users:
            cur.execute("""
                INSERT INTO users (email, name, employee_id, password_hash, role, team)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, user)
        
        conn.commit()
        cur.close()
        conn.close()
        return
    
    # Process CSV data
    engine = create_engine(get_db_connection_string())
    
    # Hash passwords if they exist in CSV
    if 'password' in df.columns:
        df['password_hash'] = df['password'].apply(
            lambda x: generate_password_hash(str(x), method='pbkdf2:sha256')
        )
        df = df.drop('password', axis=1)
    
    df.to_sql('users', engine, if_exists='append', index=False)
    print("Users imported successfully")

def import_clients():
    """Import clients data"""
    print("Importing clients...")
    file_path = 'Data Uploads/clients.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('clients', engine, if_exists='append', index=False)
    print("Clients imported successfully")

def import_sales():
    """Import sales data"""
    print("Importing sales...")
    file_path = 'Data Uploads/sales.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('sales', engine, if_exists='append', index=False)
    print("Sales imported successfully")

def import_vendor_managers():
    """Import vendor managers data"""
    print("Importing vendor managers...")
    file_path = 'Data Uploads/vendor_managers.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('vendor_managers', engine, if_exists='append', index=False)
    print("Vendor managers imported successfully")

def import_partners():
    """Import partners data"""
    print("Importing partners...")
    file_path = 'Data Uploads/partners.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    # Handle array fields
    if 'specialized' in df.columns:
        df['specialized'] = df['specialized'].apply(
            lambda x: '{' + ','.join(str(x).split(',')) + '}' if pd.notna(x) else None
        )
    
    if 'geographic_coverage' in df.columns:
        df['geographic_coverage'] = df['geographic_coverage'].apply(
            lambda x: '{' + ','.join(str(x).split(',')) + '}' if pd.notna(x) else None
        )
    
    # Fill missing values
    df = df.fillna('NA')
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('partners', engine, if_exists='append', index=False)
    print("Partners imported successfully")

def import_bids():
    """Import bids data"""
    print("Importing bids...")
    file_path = 'Data Uploads/bids.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('bids', engine, if_exists='append', index=False)
    print("Bids imported successfully")

def import_bid_target_audiences():
    """Import bid target audiences data"""
    print("Importing bid target audiences...")
    file_path = 'Data Uploads/bid_target_audiences.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    # Handle boolean fields
    if 'is_best_efforts' in df.columns:
        df['is_best_efforts'] = df['is_best_efforts'].map({'true': True, 'false': False, True: True, False: False})
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('bid_target_audiences', engine, if_exists='append', index=False)
    print("Bid target audiences imported successfully")

def import_bid_audience_countries():
    """Import bid audience countries data"""
    print("Importing bid audience countries...")
    file_path = 'Data Uploads/bid_audience_countries.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('bid_audience_countries', engine, if_exists='append', index=False)
    print("Bid audience countries imported successfully")

def import_bid_partners():
    """Import bid partners data"""
    print("Importing bid partners...")
    file_path = 'Data Uploads/bid_partners.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('bid_partners', engine, if_exists='append', index=False)
    print("Bid partners imported successfully")

def import_bid_po_numbers():
    """Import bid PO numbers data"""
    print("Importing bid PO numbers...")
    file_path = 'Data Uploads/bid_po_numbers.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('bid_po_numbers', engine, if_exists='append', index=False)
    print("Bid PO numbers imported successfully")

def import_partner_responses():
    """Import partner responses data"""
    print("Importing partner responses...")
    file_path = 'Data Uploads/partner_responses.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    # Handle JSON fields
    if 'response_data' in df.columns:
        df['response_data'] = df['response_data'].apply(
            lambda x: json.loads(x) if pd.notna(x) and x != '' else None
        )
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('partner_responses', engine, if_exists='append', index=False)
    print("Partner responses imported successfully")

def import_partner_audience_responses():
    """Import partner audience responses data"""
    print("Importing partner audience responses...")
    file_path = 'Data Uploads/partner_audience_responses.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('partner_audience_responses', engine, if_exists='append', index=False)
    print("Partner audience responses imported successfully")

def import_proposals():
    """Import proposals data"""
    print("Importing proposals...")
    file_path = 'Data Uploads/proposals.csv'
    df = read_csv_with_encoding(file_path)
    
    if df is None:
        return
    
    # Handle JSON fields
    if 'data' in df.columns:
        df['data'] = df['data'].apply(
            lambda x: json.loads(x) if pd.notna(x) and x != '' else None
        )
    
    engine = create_engine(get_db_connection_string())
    df.to_sql('proposals', engine, if_exists='append', index=False)
    print("Proposals imported successfully")

def import_all_data():
    """Import all data in the correct sequence"""
    try:
        print("Starting comprehensive data import...")
        print("=" * 50)
        
        # Core reference tables first
        import_users()
        import_clients()
        import_sales()
        import_vendor_managers()
        import_partners()
        
        print("\nCore reference tables imported successfully")
        print("=" * 50)
        
        # Main business tables
        import_bids()
        import_bid_target_audiences()
        import_bid_audience_countries()
        import_bid_partners()
        import_bid_po_numbers()
        
        print("\nMain business tables imported successfully")
        print("=" * 50)
        
        # Response and transaction tables
        import_partner_responses()
        import_partner_audience_responses()
        import_proposals()
        
        print("\nResponse and transaction tables imported successfully")
        print("=" * 50)
        print("All data imported successfully!")
        
    except Exception as e:
        print(f"Error during import: {str(e)}")
        raise e

if __name__ == "__main__":
    import_all_data()
