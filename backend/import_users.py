import os
import psycopg2
from werkzeug.security import generate_password_hash
from config import Config

def import_users():
    try:
        print("Starting users import...")
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()

        # Create users table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                employee_id VARCHAR(50) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                team VARCHAR(50) DEFAULT 'Operations' NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default admin user
        default_password = "admin"
        hashed_password = generate_password_hash(default_password, method='pbkdf2:sha256')

        # Check if admin user exists
        cur.execute("SELECT id FROM users WHERE email = 'admin@example.com'")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users (email, name, password_hash, role, team, employee_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('admin@example.com', 'Admin User', hashed_password, 'admin', 'Operations', 'EMP001'))

        conn.commit()
        print("Users initialized successfully")

    except Exception as e:
        print(f"Error importing users data: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_users()