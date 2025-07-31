
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
    """Import/Update bids data from Data Uploads/bids.csv with team information"""
    try:
        print("Starting bids import/update...")
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
        
        # Check if we have bid_number column to identify existing records
        if 'bid_number' not in df.columns:
            print("Error: bid_number column not found in CSV")
            return
        
        # Connect directly to execute updates
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        updated_count = 0
        inserted_count = 0
        
        for index, row in df.iterrows():
            bid_number = row['bid_number']
            
            # Check if bid exists
            cur.execute("SELECT id FROM bids WHERE bid_number = %s", (bid_number,))
            existing_bid = cur.fetchone()
            
            if existing_bid:
                # Update existing bid with team information
                update_fields = []
                update_values = []
                
                # Only update fields that exist in CSV and are not None/empty
                for col in df.columns:
                    if col != 'id' and pd.notna(row[col]) and str(row[col]).strip() != '':
                        update_fields.append(f"{col} = %s")
                        update_values.append(row[col])
                
                if update_fields:
                    update_values.append(bid_number)  # for WHERE clause
                    update_query = f"UPDATE bids SET {', '.join(update_fields)} WHERE bid_number = %s"
                    cur.execute(update_query, update_values)
                    updated_count += 1
                    print(f"Updated bid {bid_number}")
            else:
                # Insert new bid
                columns = [col for col in df.columns if col != 'id']
                values = [row[col] if pd.notna(row[col]) else None for col in columns]
                
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"INSERT INTO bids ({', '.join(columns)}) VALUES ({placeholders})"
                cur.execute(insert_query, values)
                inserted_count += 1
                print(f"Inserted new bid {bid_number}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("=" * 40)
        print("Bids processing completed!")
        print(f"Updated {updated_count} existing records")
        print(f"Inserted {inserted_count} new records")
        print(f"Total processed: {len(df)} records")
        
    except Exception as e:
        print(f"Error during bids import/update: {str(e)}")
        raise e

if __name__ == "__main__":
    import_bids_only()
