import psycopg2
from config import Config

def add_quant_methodology():
    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        # Add 'quant' to the methodology enum type
        cur.execute("""
            ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'quant';
        """)
        
        conn.commit()
        print("Successfully added 'quant' to methodology enum")
        
    except Exception as e:
        print(f"Error adding methodology: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_quant_methodology() 