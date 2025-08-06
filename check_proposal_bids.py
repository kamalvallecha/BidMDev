import psycopg2
from psycopg2.extras import RealDictCursor

def check_proposal_bids():
    try:
        # Connect to database
        conn = psycopg2.connect('postgresql://postgres:root123@localhost:5432/BidM')
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== ALL BIDS IN DATABASE ===")
        print("=" * 80)
        
        # Get all bids
        cur.execute("""
            SELECT b.id, b.bid_number, b.study_name, b.status, b.created_by,
                   c.client_name, vm.vm_name, vm.team, s.sales_person
            FROM bids b
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN vendor_managers vm ON b.vm_contact = vm.id
            LEFT JOIN sales s ON b.sales_contact = s.id
            ORDER BY b.bid_number DESC
        """)
        
        all_bids = cur.fetchall()
        
        for bid in all_bids:
            print(f"Bid ID: {bid['id']}")
            print(f"  Bid Number: {bid['bid_number']}")
            print(f"  Study Name: {bid['study_name']}")
            print(f"  Status: {bid['status']}")
            print(f"  Created By: {bid['created_by']}")
            print(f"  Client: {bid['client_name']}")
            print(f"  VM: {bid['vm_name']} (Team: {bid['team']})")
            print(f"  Sales: {bid['sales_person']}")
            print("-" * 40)
        
        print(f"\nTotal bids in database: {len(all_bids)}")
        
        print("\n=== BID ACCESS RECORDS ===")
        print("=" * 80)
        
        # Get all bid access records
        cur.execute("""
            SELECT bid_id, user_id, team
            FROM bid_access
            ORDER BY bid_id
        """)
        
        access_records = cur.fetchall()
        
        for record in access_records:
            print(f"Bid ID: {record['bid_id']}, User ID: {record['user_id']}, Team: {record['team']}")
        
        print(f"\nTotal access records: {len(access_records)}")
        
        print("\n=== USER INFORMATION ===")
        print("=" * 80)
        
        # Get user information for Kamal Vallecha
        cur.execute("""
            SELECT id, name, email, role, team
            FROM users
            WHERE name ILIKE '%kamal%' OR email ILIKE '%kamal%'
        """)
        
        kamal_user = cur.fetchone()
        if kamal_user:
            print(f"Kamal Vallecha User Info:")
            print(f"  ID: {kamal_user['id']}")
            print(f"  Name: {kamal_user['name']}")
            print(f"  Email: {kamal_user['email']}")
            print(f"  Role: {kamal_user['role']}")
            print(f"  Team: {kamal_user['team']}")
        else:
            print("Kamal Vallecha user not found")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_proposal_bids() 