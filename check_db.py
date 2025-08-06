import psycopg2
from psycopg2.extras import RealDictCursor

def check_pass_status():
    try:
        # Connect to database
        conn = psycopg2.connect('postgresql://postgres:root123@localhost:5432/BidM')
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # First, let's see all partner responses for bid 37
        print("All partner responses for bid 37:")
        print("=" * 80)
        cur.execute("""
            SELECT 
                pr.id as response_id,
                pr.partner_id,
                pr.loi,
                p.partner_name,
                pr.created_at
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = 37
            ORDER BY pr.partner_id, pr.loi
        """)
        
        responses = cur.fetchall()
        for resp in responses:
            print(f"Response ID: {resp['response_id']}, Partner: {resp['partner_name']} (ID: {resp['partner_id']}), LOI: {resp['loi']}, Created: {resp['created_at']}")
        
        print("\n" + "=" * 80)
        print("All partner_audience_responses for bid 37:")
        print("=" * 80)
        
        # Now check all partner_audience_responses for bid 37
        cur.execute("""
            SELECT 
                par.pass,
                par.commitment,
                par.commitment_type,
                par.cpi,
                par.country,
                par.audience_id,
                pr.partner_id,
                pr.loi,
                bta.ta_category,
                p.partner_name
            FROM partner_audience_responses par 
            JOIN partner_responses pr ON par.partner_response_id = pr.id 
            JOIN bid_target_audiences bta ON par.audience_id = bta.id
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = 37
            ORDER BY pr.partner_id, pr.loi, par.country
        """)
        
        rows = cur.fetchall()
        
        for row in rows:
            print(f"Country: {row['country']}")
            print(f"  Pass: {row['pass']}")
            print(f"  Commitment: {row['commitment']}")
            print(f"  Commitment Type: {row['commitment_type']}")
            print(f"  CPI: {row['cpi']}")
            print(f"  Partner: {row['partner_name']} (ID: {row['partner_id']})")
            print(f"  LOI: {row['loi']}")
            print(f"  Audience ID: {row['audience_id']}")
            print(f"  Audience: {row['ta_category']}")
            print("-" * 40)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pass_status() 