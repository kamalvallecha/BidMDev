import psycopg2
from psycopg2.extras import RealDictCursor

def update_pass_status():
    try:
        # Connect to database
        conn = psycopg2.connect('postgresql://postgres:root123@localhost:5432/BidM')
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update pass status for bid 37, LOI 1, B2B audience countries
        cur.execute("""
            UPDATE partner_audience_responses 
            SET pass = true
            WHERE partner_response_id IN (
                SELECT pr.id 
                FROM partner_responses pr 
                WHERE pr.bid_id = 37 AND pr.loi = 1
            )
            AND audience_id IN (
                SELECT bta.id 
                FROM bid_target_audiences bta 
                WHERE bta.bid_id = 37 AND bta.ta_category LIKE '%B2B%'
            )
            AND country IN ('Afghanistan', 'Albania')
        """)
        
        rows_affected = cur.rowcount
        print(f"Updated {rows_affected} rows to set pass = true")
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cur.execute("""
            SELECT 
                par.pass,
                par.commitment,
                par.commitment_type,
                par.cpi,
                par.country,
                pr.partner_id,
                pr.loi,
                bta.ta_category,
                p.partner_name
            FROM partner_audience_responses par 
            JOIN partner_responses pr ON par.partner_response_id = pr.id 
            JOIN bid_target_audiences bta ON par.audience_id = bta.id
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = 37 
            AND pr.loi = 1 
            AND bta.ta_category LIKE '%B2B%'
            ORDER BY par.country
        """)
        
        rows = cur.fetchall()
        
        print("\nUpdated pass status for bid 37, LOI 1, B2B audience:")
        print("=" * 80)
        
        for row in rows:
            print(f"Country: {row['country']}")
            print(f"  Pass: {row['pass']}")
            print(f"  Commitment: {row['commitment']}")
            print(f"  Commitment Type: {row['commitment_type']}")
            print(f"  CPI: {row['cpi']}")
            print(f"  Partner: {row['partner_name']} (ID: {row['partner_id']})")
            print(f"  LOI: {row['loi']}")
            print(f"  Audience: {row['ta_category']}")
            print("-" * 40)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_pass_status() 