import psycopg2
from werkzeug.security import generate_password_hash
from config import Config

def update_vm_password():
    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        # Generate new password hash
        new_password = "admin"
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update vm user's password
        cur.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'vm@example.com'
        """, (hashed_password,))
        
        conn.commit()
        print("VM password updated successfully")
        
    except Exception as e:
        print(f"Error updating VM password: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_vm_password() 