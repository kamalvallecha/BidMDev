
import os
import psycopg2
from config import Config

def import_schema():
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(Config.DATABASE_URL)
        conn.autocommit = True  # Important for creating types
        cur = conn.cursor()
        
        print("Reading schema.sql...")
        with open('schema.sql', 'r') as file:
            sql_script = file.read()
            
        print("Executing schema.sql...")
        cur.execute(sql_script)
        print("Schema imported successfully!")
        
    except Exception as e:
        print(f"Error importing schema: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_schema()
