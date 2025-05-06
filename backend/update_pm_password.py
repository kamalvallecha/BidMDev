import psycopg2
from werkzeug.security import generate_password_hash
from config import Config

def update_pm_password():
    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        # Generate new password hash
        new_password = "admin"
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update pm user's password
        cur.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'pm@example.com'
        """, (hashed_password,))
        
        conn.commit()
        print("PM password updated successfully")
        
    except Exception as e:
        print(f"Error updating PM password: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_pm_password() 