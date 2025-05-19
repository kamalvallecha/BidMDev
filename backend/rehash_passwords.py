
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def rehash_passwords():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all users that need password reset
        cur.execute("SELECT id, email, password_hash FROM users")
        users = cur.fetchall()
        
        # Set a default password for everyone
        default_password = "Course5@123"
        new_password_hash = generate_password_hash(default_password, method='sha256')
        
        # Update all users
        for user in users:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_password_hash, user['id'])
            )
            print(f"Reset password for {user['email']}")
        
        conn.commit()
        print("Password reset completed successfully")
        
    except Exception as e:
        print(f"Error resetting passwords: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    rehash_passwords()
