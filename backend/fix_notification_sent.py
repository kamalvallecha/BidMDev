#!/usr/bin/env python3
"""
Script to fix the missing notification_sent column in partner_links table.
This resolves the error: "column pl.notification_sent does not exist"
"""

import psycopg2
import sys
import os

# Add the backend directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
except ImportError:
    print("Error: Could not import config. Make sure you're running this from the backend directory.")
    sys.exit(1)

def fix_notification_sent_column():
    """Add the missing notification_sent column to partner_links table"""
    
    conn = None
    cur = None
    
    try:
        # Connect to the database
        conn = psycopg2.connect(Config.DATABASE_URL)
        cur = conn.cursor()
        
        print("Connected to database successfully.")
        
        # Check if the column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'partner_links' 
            AND column_name = 'notification_sent'
        """)
        
        column_exists = cur.fetchone()
        
        if column_exists:
            print("✓ notification_sent column already exists in partner_links table")
        else:
            print("Adding notification_sent column to partner_links table...")
            
            # Add the column
            cur.execute("""
                ALTER TABLE partner_links 
                ADD COLUMN notification_sent BOOLEAN DEFAULT FALSE
            """)
            
            print("✓ Added notification_sent column to partner_links table")
        
        # Update any existing records to have notification_sent = false
        cur.execute("""
            UPDATE partner_links 
            SET notification_sent = false 
            WHERE notification_sent IS NULL
        """)
        
        updated_count = cur.rowcount
        if updated_count > 0:
            print(f"✓ Updated {updated_count} existing records to have notification_sent = false")
        else:
            print("✓ No existing records needed updating")
        
        # Commit the changes
        conn.commit()
        print("✓ Database changes committed successfully")
        
        # Verify the column exists and has the correct structure
        cur.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'partner_links' 
            AND column_name = 'notification_sent'
        """)
        
        column_info = cur.fetchone()
        if column_info:
            print(f"✓ Column verification successful:")
            print(f"  - Column name: {column_info[0]}")
            print(f"  - Data type: {column_info[1]}")
            print(f"  - Default value: {column_info[2]}")
            print(f"  - Nullable: {column_info[3]}")
        else:
            print("✗ Column verification failed - column not found")
            return False
        
        print("\n🎉 Migration completed successfully!")
        print("The 'check_expiring_links' function should now work without errors.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during migration: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("Partner Links Notification Column Migration")
    print("=" * 60)
    
    success = fix_notification_sent_column()
    
    if success:
        print("\n✅ Migration successful! You can now restart your application.")
    else:
        print("\n❌ Migration failed! Please check the error messages above.")
        sys.exit(1) 