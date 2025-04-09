from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta  # Import timedelta separately
from config import Config
import json
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from typing import List
from pydantic import BaseModel
from dataclasses import dataclass
from werkzeug.security import check_password_hash, generate_password_hash  # Add generate_password_hash
import jwt
from constants import ROLES_AND_PERMISSIONS  # Add this import

app = Flask(__name__)
# Simplify CORS to the most basic configuration
CORS(app, origins=["http://localhost:5173"], allow_headers=["Content-Type", "Authorization"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], supports_credentials=True)

# Add this dataclass for the response structure
@dataclass
class PartnerLOIData:
    partner_name: str
    loi: int
    country: str
    allocation: int
    n_delivered: int
    cpi: float

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT
        )
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise e

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if request.method == 'GET':
            cur.execute("""
                SELECT id, email, name, employee_id, role, team, created_at, updated_at 
                FROM users 
                ORDER BY id
            """)
            users = cur.fetchall()
            
            return jsonify([{
                'id': user[0],
                'email': user[1],
                'name': user[2],
                'employee_id': user[3],
                'role': user[4],
                'team': user[5],
                'created_at': user[6].strftime('%Y-%m-%d %H:%M:%S') if user[6] else None,
                'updated_at': user[7].strftime('%Y-%m-%d %H:%M:%S') if user[7] else None
            } for user in users])

        elif request.method == 'POST':
            data = request.json
            password_hash = create_password_hash(data['password'])
            
            cur.execute("""
                INSERT INTO users (email, name, employee_id, password_hash, role, team)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (data['email'], data['name'], data['employee_id'], password_hash, data['role'], data['team']))
            
            new_user_id = cur.fetchone()[0]
            conn.commit()
            
            return jsonify({'id': new_user_id, 'message': 'User created successfully'}), 201

    except Exception as e:
        print(f"Error handling users: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/vms', methods=['GET'])
def get_vms():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM vendor_managers ORDER BY id')
        vms = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(vms)
    except Exception as e:
        print(f"Error in get_vms: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vms', methods=['POST'])
def create_vm():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO vendor_managers (
                vm_id, vm_name, contact_person, 
                reporting_manager, team, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            ) RETURNING id
        """, (
            data['vm_id'],
            data['vm_name'],
            data['contact_person'],
            data['reporting_manager'],
            data['team']
        ))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            "id": new_id,
            "message": "VM created successfully"
        }), 201
        
    except Exception as e:
        print(f"Error creating VM: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/sales', methods=['GET'])
def get_sales():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM sales ORDER BY id')
        sales = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(sales)
    except Exception as e:
        print(f"Error in get_sales: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales', methods=['POST'])
def create_sale():
    try:
        data = request.json
        print("Received sales data:", data)
        
        required_fields = ['sales_id', 'sales_person', 'contact_person', 'reporting_manager', 'region']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if sales ID already exists
        cur.execute('SELECT id FROM sales WHERE sales_id = %s', (data['sales_id'],))
        if cur.fetchone():
            return jsonify({"error": "Sales ID already exists"}), 400

        # Create region enum if it doesn't exist
        cur.execute('''
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'region') THEN
                    CREATE TYPE region AS ENUM ('north', 'south', 'east', 'west');
                END IF;
            END $$;
        ''')

        # Insert new sales record
        cur.execute('''
            INSERT INTO sales (
                sales_id, 
                sales_person, 
                contact_person, 
                reporting_manager, 
                region, 
                created_at, 
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s::region, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (
            data['sales_id'],
            data['sales_person'],
            data['contact_person'],
            data['reporting_manager'],
            data['region'].lower()
        ))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': new_id, 'message': 'Sales record created successfully'}), 201
        
    except Exception as e:
        print(f"Error in create_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/partners', methods=['GET'])
def get_partners():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM partners ORDER BY id')
        partners = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(partners)
    except Exception as e:
        print(f"Error in get_partners: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add this function to generate partner ID
def generate_partner_id():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get the current maximum numeric value using raw string for regex
        cur.execute(r"""
            SELECT MAX(CAST(SUBSTRING(partner_id FROM 'C5i_Partner_(\d+)') AS INTEGER))
            FROM partners
            WHERE partner_id LIKE 'C5i_Partner_%'
        """)
        
        max_num = cur.fetchone()[0]
        next_num = 1 if max_num is None else max_num + 1
        
        return f"C5i_Partner_{next_num}"
    except Exception as e:
        print(f"Error generating partner ID: {str(e)}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/partners', methods=['POST'])
def create_partner():
    try:
        data = request.json
        partner_id = generate_partner_id()
        
        # Convert specialized and geographic_coverage to proper PostgreSQL arrays
        specialized = data.get('specialized', [])
        geographic_coverage = data.get('geographic_coverage', [])

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO partners (
                partner_id, partner_name, contact_person, 
                contact_email, contact_phone, website, 
                company_address, specialized, geographic_coverage
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            partner_id,
            data['partner_name'],
            data['contact_person'],
            data['contact_email'],
            data['contact_phone'],
            data.get('website', ''),
            data['company_address'],
            specialized,  # psycopg2 will handle the array conversion
            geographic_coverage  # psycopg2 will handle the array conversion
        ))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            "id": new_id, 
            "partner_id": partner_id,
            "message": "Partner created successfully"
        }), 201
        
    except Exception as e:
        print(f"Error creating partner: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM clients ORDER BY id')
        clients = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(clients)
    except Exception as e:
        print(f"Error in get_clients: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.json
        print("Received client data:", data)
        
        required_fields = ['client_id', 'client_name', 'contact_person', 'email', 'phone', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if client already exists
        cur.execute('SELECT id FROM clients WHERE client_id = %s OR email = %s', 
                   (data['client_id'], data['email']))
        if cur.fetchone():
            return jsonify({"error": "Client ID or email already exists"}), 400

        # Insert new client
        cur.execute('''
            INSERT INTO clients (
                client_id, 
                client_name, 
                contact_person, 
                email,
                phone,
                country,
                created_at, 
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (
            data['client_id'],
            data['client_name'],
            data['contact_person'],
            data['email'],
            data['phone'],
            data['country']
        ))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': new_id, 'message': 'Client created successfully'}), 201
        
    except Exception as e:
        print(f"Error in create_client: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.json
        print(f"Updating client {client_id} with data:", data)
        
        required_fields = ['client_id', 'client_name', 'contact_person', 'email', 'phone', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if client exists
        cur.execute('SELECT id FROM clients WHERE id = %s', (client_id,))
        if not cur.fetchone():
            return jsonify({"error": f"Client with ID {client_id} not found"}), 404
        
        # Check if email or client_id already exists for different client
        cur.execute('SELECT id FROM clients WHERE (client_id = %s OR email = %s) AND id != %s', 
                   (data['client_id'], data['email'], client_id))
        if cur.fetchone():
            return jsonify({"error": "Client ID or email already exists for another client"}), 400

        # Update client
        cur.execute('''
            UPDATE clients SET
                client_id = %s, 
                client_name = %s, 
                contact_person = %s, 
                email = %s,
                phone = %s,
                country = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        ''', (
            data['client_id'],
            data['client_name'],
            data['contact_person'],
            data['email'],
            data['phone'],
            data['country'],
            client_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Client updated successfully'})
        
    except Exception as e:
        print(f"Error updating client: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First check if client exists
        cur.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
        if not cur.fetchone():
            return jsonify({"error": f"Client with ID {client_id} not found"}), 404
        
        # Delete the client
        cur.execute("DELETE FROM clients WHERE id = %s", (client_id,))
        conn.commit()
        
        return jsonify({"message": "Client deleted successfully"})
        
    except Exception as e:
        print(f"Error deleting client: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids', methods=['GET'])
def get_bids():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get all bids with joined data
        cur.execute("""
            SELECT 
                b.id,
                b.bid_number,
                TO_CHAR(b.bid_date, 'YYYY-MM-DD') as bid_date,
                b.study_name,
                b.methodology,
                b.status,
                c.client_name as client,
                s.sales_person as sales_contact_name,
                vm.vm_name as vm_contact_name
            FROM bids b
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN sales s ON b.sales_contact = s.id
            LEFT JOIN vendor_managers vm ON b.vm_contact = vm.id
            ORDER BY b.id DESC
        """)
        
        bids = cur.fetchall()
        
        # Format the response
        formatted_bids = []
        for bid in bids:
            formatted_bid = {
                'id': bid['id'],
                'bid_number': bid['bid_number'],
                'bid_date': bid['bid_date'],
                'study_name': bid['study_name'],
                'methodology': bid['methodology'],
                'client': bid['client'],
                'status': bid['status'],
                'sales_contact_name': bid['sales_contact_name'],
                'vm_contact_name': bid['vm_contact_name']
            }
            formatted_bids.append(formatted_bid)

        return jsonify(formatted_bids)

    except Exception as e:
        print(f"Error fetching bids: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids', methods=['POST'])
def create_bid():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Start a transaction
        cur.execute("BEGIN")
        
        try:
            data = request.json
            print("Received bid data:", data)
            
            # Get next bid number
            cur.execute("SELECT MAX(CAST(bid_number AS INTEGER)) FROM bids")
            current_max = cur.fetchone()[0]
            next_bid_number = str(40000 if current_max is None else current_max + 1)

            # Insert main bid
            cur.execute("""
                INSERT INTO bids (
                    bid_number, bid_date, study_name, methodology,
                    sales_contact, vm_contact, client, project_requirement,
                    status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, 
                    'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING id
            """, (
                next_bid_number,
                data['bid_date'],
                data['study_name'],
                data['methodology'],
                data['sales_contact'],
                data['vm_contact'],
                data['client'],
                data['project_requirement']
            ))
            
            bid_id = cur.fetchone()[0]

            # Insert target audiences
            for audience in data['target_audiences']:
                cur.execute("""
                    INSERT INTO bid_target_audiences (
                        bid_id, audience_name, ta_category, broader_category,
                        exact_ta_definition, mode, sample_required, ir, comments
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    bid_id,
                    audience['name'],
                    audience['ta_category'],
                    audience['broader_category'],
                    audience['exact_ta_definition'],
                    audience['mode'],
                    audience['sample_required'],
                    audience['ir'],
                    audience.get('comments', '')
                ))
                audience_id = cur.fetchone()[0]

                # Insert country samples for this audience
                if 'country_samples' in audience:
                    for country, sample_size in audience['country_samples'].items():
                        # Handle both dictionary and direct integer values
                        if isinstance(sample_size, dict):
                            # If it's a dictionary, get the first value
                            sample_value = next(iter(sample_size.values()), 0)
                        else:
                            # If it's a direct integer value
                            sample_value = sample_size

                        cur.execute("""
                            INSERT INTO bid_audience_countries (
                                bid_id, audience_id, country, sample_size
                            ) VALUES (%s, %s, %s, %s)
                            ON CONFLICT (bid_id, audience_id, country) 
                            DO UPDATE SET sample_size = EXCLUDED.sample_size
                        """, (bid_id, audience_id, country, int(sample_value)))

            # Insert partner responses without audience responses
            for partner_id in data.get('partners', []):
                for loi in data.get('loi', []):
                    cur.execute("""
                        INSERT INTO partner_responses (
                            bid_id, partner_id, loi, status, currency,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, 'draft', 'USD',
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """, (bid_id, partner_id, int(loi)))

            # Commit the transaction
            conn.commit()
            
            return jsonify({
                "message": "Bid created successfully",
                "bid_id": bid_id,
                "bid_number": next_bid_number
            }), 201

        except Exception as e:
            cur.execute("ROLLBACK")
            print(f"Database error: {str(e)}")
            raise e
            
    except Exception as e:
        print(f"Error creating bid: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>', methods=['GET'])
def get_bid(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get main bid data
        cur.execute("""
            SELECT 
                b.*,
                c.client_name,
                s.sales_person,
                vm.vm_name,
                ARRAY_AGG(DISTINCT bac.country) as countries
            FROM bids b
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN sales s ON b.sales_contact = s.id
            LEFT JOIN vendor_managers vm ON b.vm_contact = vm.id
            LEFT JOIN bid_audience_countries bac ON b.id = bac.bid_id
            WHERE b.id = %s
            GROUP BY b.id, c.client_name, s.sales_person, vm.vm_name
        """, (bid_id,))
        
        bid = cur.fetchone()
        if not bid:
            return jsonify({"error": "Bid not found"}), 404

        if bid['bid_date']:
            bid['bid_date'] = bid['bid_date'].strftime('%Y-%m-%d')

        # Get target audiences with sample sizes
        cur.execute("""
            SELECT 
                bta.id,
                bta.audience_name as name,
                bta.ta_category,
                bta.broader_category,
                bta.exact_ta_definition,
                bta.mode,
                bta.sample_required,
                bta.ir,
                bta.comments,
                bac.country,
                bac.sample_size
            FROM bid_target_audiences bta
            LEFT JOIN bid_audience_countries bac ON bta.id = bac.audience_id
            WHERE bta.bid_id = %s
        """, (bid_id,))
        
        rows = cur.fetchall()

        # Format target audiences with their sample sizes
        target_audiences = {}
        for row in rows:
            audience_id = row['id']
            if audience_id not in target_audiences:
                target_audiences[audience_id] = {
                    'id': row['id'],
                    'uniqueId': f"audience-{audience_id}",  # Add unique identifier
                    'name': row['name'],
                    'ta_category': row['ta_category'],
                    'broader_category': row['broader_category'],
                    'exact_ta_definition': row['exact_ta_definition'],
                    'mode': row['mode'],
                    'sample_required': row['sample_required'],
                    'ir': row['ir'],
                    'comments': row['comments'],
                    'country_samples': {}
                }
            if row['country']:
                target_audiences[audience_id]['country_samples'][row['country']] = row['sample_size']

        # Get partners and LOIs with full partner details
        cur.execute("""
            SELECT DISTINCT 
                pr.partner_id,
                p.partner_name,
                pr.loi
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = %s
        """, (bid_id,))
        
        partner_lois = cur.fetchall()
        partners = []
        seen_partners = set()
        
        for row in partner_lois:
            if row['partner_id'] not in seen_partners:
                partners.append({
                    'id': row['partner_id'],
                    'partner_name': row['partner_name']
                })
                seen_partners.add(row['partner_id'])
                
        lois = list(set([r['loi'] for r in partner_lois]))

        response = {
            **bid,
            'target_audiences': list(target_audiences.values()),
            'partners': partners,
            'loi': lois
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error getting bid: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>', methods=['PUT'])
def update_bid(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        data = request.json
        
        # Start transaction
        cur.execute("BEGIN")
        
        # 1. Update main bid details
        cur.execute("""
            UPDATE bids SET 
            bid_date = %s,
            study_name = %s,
            methodology = %s,
            sales_contact = %s,
            vm_contact = %s,
            client = %s,
            project_requirement = %s,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            data['bid_date'],
            data['study_name'],
            data['methodology'],
            data['sales_contact'],
            data['vm_contact'],
            data['client'],
            data['project_requirement'],
            bid_id
        ))
        print("Updated main bid details")

        # 2. Get existing audience IDs
        cur.execute("""
            SELECT id FROM bid_target_audiences 
            WHERE bid_id = %s
            ORDER BY id
        """, (bid_id,))
        existing_audience_ids = [row[0] for row in cur.fetchall()]
        print("Existing audience IDs:", existing_audience_ids)

        # 3. Update or insert target audiences
        for idx, audience in enumerate(data['target_audiences']):
            print(f"Processing audience {idx}: {audience}")
            if idx < len(existing_audience_ids):
                # Update existing audience
                audience_id = existing_audience_ids[idx]
                cur.execute("""
                    UPDATE bid_target_audiences SET 
                    audience_name = %s,
                    ta_category = %s,
                    broader_category = %s,
                    exact_ta_definition = %s,
                    mode = %s,
                    sample_required = %s,
                    ir = %s,
                    comments = %s,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND bid_id = %s
                """, (
                    audience['name'],
                    audience['ta_category'],
                    audience['broader_category'],
                    audience['exact_ta_definition'],
                    audience['mode'],
                    audience['sample_required'],
                    audience['ir'],
                    audience.get('comments', ''),
                    audience_id,
                    bid_id
                ))
                print(f"Updated audience ID: {audience_id}")
            else:
                # Insert new audience
                cur.execute("""
                    INSERT INTO bid_target_audiences (
                        bid_id,
                        audience_name,
                        ta_category,
                        broader_category,
                        exact_ta_definition,
                        mode,
                        sample_required,
                        ir,
                        comments
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    bid_id,
                    audience['name'],
                    audience['ta_category'],
                    audience['broader_category'],
                    audience['exact_ta_definition'],
                    audience['mode'],
                    audience['sample_required'],
                    audience['ir'],
                    audience.get('comments', '')
                ))
                audience_id = cur.fetchone()[0]
                existing_audience_ids.append(audience_id)
                print(f"Inserted new audience ID: {audience_id}")

            # Update or insert country samples
            if 'country_samples' in audience:
                # First, remove old country samples for this audience
                cur.execute("""
                    DELETE FROM bid_audience_countries 
                    WHERE audience_id = %s
                """, (audience_id,))
                print(f"Deleted old country samples for audience ID: {audience_id}")

                # Then insert new country samples
                for country, sample_size in audience['country_samples'].items():
                    try:
                        print(f"Inserting country {country} with sample size {sample_size}")
                        # Check if record already exists (despite the DELETE)
                        cur.execute("""
                            SELECT 1 FROM bid_audience_countries 
                            WHERE bid_id = %s AND audience_id = %s AND country = %s
                        """, (bid_id, audience_id, country))
                        
                        exists = cur.fetchone()
                        if exists:
                            # Update existing record
                            print(f"Country record exists, updating: {country}")
                            cur.execute("""
                                UPDATE bid_audience_countries
                                SET sample_size = %s
                                WHERE bid_id = %s AND audience_id = %s AND country = %s
                            """, (int(sample_size), bid_id, audience_id, country))
                        else:
                            # Insert new record
                            print(f"Country record does not exist, inserting: {country}")
                            cur.execute("""
                                INSERT INTO bid_audience_countries (
                                    bid_id, audience_id, country, sample_size
                                ) VALUES (%s, %s, %s, %s)
                            """, (bid_id, audience_id, country, int(sample_size)))
                        print(f"Successfully processed country {country}")
                    except Exception as country_error:
                        print(f"Error processing country {country}: {str(country_error)}")
                        raise

        # 4. Update partner responses for new audiences
        partners = data.get('partners', [])
        lois = data.get('loi', [])
        print(f"Processing partners: {partners} and LOIs: {lois}")

        if partners and lois:
            # Get all audiences and countries
            cur.execute("""
                SELECT bta.id as audience_id, bac.country
                FROM bid_target_audiences bta
                JOIN bid_audience_countries bac ON bta.id = bac.audience_id
                WHERE bta.bid_id = %s
            """, (bid_id,))
            
            audience_countries = cur.fetchall()
            print(f"Found audience_countries: {audience_countries}")

            # Update partner responses
            for partner in partners:
                for loi in lois:
                    print(f"Processing partner {partner}, LOI {loi}")
                    # Create or update partner_response
                    try:
                        # Check if partner response exists first
                        cur.execute("""
                            SELECT id FROM partner_responses 
                            WHERE bid_id = %s AND partner_id = %s AND loi = %s
                        """, (bid_id, partner, loi))
                        
                        existing_response = cur.fetchone()
                        
                        if existing_response:
                            # Use existing response ID
                            partner_response_id = existing_response[0]
                            print(f"Using existing partner_response_id: {partner_response_id}")
                        else:
                            # Create new response
                            cur.execute("""
                                INSERT INTO partner_responses 
                                (bid_id, partner_id, loi, status, currency, created_at)
                                VALUES (%s, %s, %s, 'draft', 'USD', CURRENT_TIMESTAMP)
                                RETURNING id
                            """, (bid_id, partner, loi))
                            
                            result = cur.fetchone()
                            partner_response_id = result[0]
                            print(f"Created partner_response_id: {partner_response_id}")
                        
                        # Create audience responses with 0 commitment (not NULL)
                        for ac in audience_countries:
                            # Check if record already exists
                            cur.execute("""
                                SELECT 1 FROM partner_audience_responses 
                                WHERE bid_id = %s AND partner_response_id = %s 
                                AND audience_id = %s AND country = %s
                            """, (bid_id, partner_response_id, ac[0], ac[1]))
                            
                            if not cur.fetchone():
                                # Only insert if doesn't exist
                                try:
                                    print(f"Inserting partner_audience_response for audience {ac[0]}, country {ac[1]}")
                                    cur.execute("""
                                        INSERT INTO partner_audience_responses 
                                        (bid_id, partner_response_id, audience_id, country, 
                                         commitment, cpi, timeline_days, comments)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (
                                        bid_id,
                                        partner_response_id,
                                        ac[0],  # audience_id
                                        ac[1],  # country
                                        0,      # default commitment
                                        0,      # default cpi
                                        0,      # default timeline_days
                                        ''      # empty comments
                                    ))
                                    print(f"Successfully inserted partner_audience_response")
                                except Exception as par_error:
                                    print(f"Error inserting partner_audience_response: {str(par_error)}")
                                    raise
                    except Exception as partner_error:
                        print(f"Error processing partner {partner}, LOI {loi}: {str(partner_error)}")
                        raise

        conn.commit()
        print("Successfully updated bid and country samples")
        return jsonify({"message": "Bid updated successfully"}), 200
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error updating bid: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/partner-responses', methods=['GET'])
def get_partner_responses(bid_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        print(f"Getting partner responses for bid {bid_id}")

        # First get ordered list of audience IDs
        cur.execute("""
            SELECT id, audience_name 
            FROM bid_target_audiences 
            WHERE bid_id = %s 
            ORDER BY created_at
        """, (bid_id,))
        
        # Create mapping from audience ID to formatted audience key (uniqueId)
        audience_mapping = {}
        audiences = cur.fetchall()
        print(f"Found {len(audiences)} audiences for bid {bid_id}")
        for idx, row in enumerate(audiences):
            # The frontend expects "audience-{id}" format
            audience_mapping[row['id']] = f"audience-{row['id']}"
            print(f"Mapped audience ID {row['id']} to {audience_mapping[row['id']]}")

        # First, get all partner PMF values directly from partner_responses
        cur.execute("""
            SELECT DISTINCT partner_id, pmf, currency
            FROM partner_responses
            WHERE bid_id = %s AND pmf IS NOT NULL
        """, (bid_id,))
        
        # Initialize settings with PMF values
        settings = {}
        for row in cur.fetchall():
            if row['partner_id'] not in settings:
                settings[row['partner_id']] = {
                    'currency': row['currency'] or 'USD',
                    'pmf': float(row['pmf']) if row['pmf'] is not None else 0
                }
                print(f"Found PMF {row['pmf']} for partner {row['partner_id']}")

        # Get all partner responses with audience data
        cur.execute("""
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                pr.currency,
                pr.pmf,
                pr.status,
                par.audience_id,
                par.country,
                par.commitment,
                par.cpi,
                par.timeline_days,
                par.comments
            FROM partner_responses pr
            LEFT JOIN partner_audience_responses par ON pr.id = par.partner_response_id
            WHERE pr.bid_id = %s
        """, (bid_id,))
        
        rows = cur.fetchall()
        print(f"Found {len(rows)} partner response rows")
        
        # Debug: print all audience IDs from partner responses
        audience_ids_in_responses = [row['audience_id'] for row in rows if row['audience_id'] is not None]
        print(f"Audience IDs in responses: {audience_ids_in_responses}")
        print(f"Available audience mapping keys: {list(audience_mapping.keys())}")

        # Initialize responses
        responses = {}
        
        for pr in rows:
            key = f"{pr['partner_id']}-{pr['loi']}"
            if key not in responses:
                responses[key] = {
                    'partner_id': pr['partner_id'],
                    'loi': pr['loi'],
                    'status': pr['status'] or 'draft',
                    'currency': pr['currency'] or 'USD',
                    'pmf': float(pr['pmf']) if pr['pmf'] is not None else 0,
                    'audiences': {}
                }
            
            # Add or update partner settings if not already set
            if pr['partner_id'] not in settings and pr['pmf'] is not None:
                settings[pr['partner_id']] = {
                    'currency': pr['currency'] or 'USD',
                    'pmf': float(pr['pmf']) if pr['pmf'] is not None else 0
                }
                print(f"Set PMF {pr['pmf']} for partner {pr['partner_id']}")
                
            # Add audience data if this row has audience information
            if pr['audience_id'] is not None:
                # Use direct audience ID mapping
                audience_key = f"audience-{pr['audience_id']}"
                
                if audience_key not in responses[key]['audiences']:
                    responses[key]['audiences'][audience_key] = {
                        'timeline': pr['timeline_days'] or 0,
                        'comments': pr['comments'] or '',
                    }
                
                if pr['country']:
                    responses[key]['audiences'][audience_key][pr['country']] = {
                        'commitment': pr['commitment'] or 0,
                        'cpi': float(pr['cpi']) if pr['cpi'] is not None else 0
                    }

        print(f"Returning responses structure: {responses}")
        print(f"Returning settings structure: {settings}")
        return jsonify({
            'responses': responses,
            'settings': settings
        })

    except Exception as e:
        print(f"Error getting partner responses: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/bids/infield', methods=['GET'])
def get_infield_bids():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Fixed query with correct column names
        cur.execute("""
            SELECT DISTINCT ON (b.id)
                b.id,
                bpo.po_number,
                b.bid_number,
                b.study_name,
                c.client_name,
                b.methodology as mode,
                s.sales_person as sales_contact,  -- Changed from s.name to s.sales_person
                v.vm_name as vm_contact,
                b.status
            FROM bids b
            LEFT JOIN bid_po_numbers bpo ON b.id = bpo.bid_id
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN sales s ON b.sales_contact = s.id
            LEFT JOIN vendor_managers v ON b.vm_contact = v.id
            WHERE b.status = 'infield'
            ORDER BY b.id, b.updated_at DESC
        """)
        
        bids = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(bids)
        
    except Exception as e:
        print(f"Error fetching infield bids: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bids/<bid_id>/po', methods=['POST'])
def add_po_number(bid_id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO bid_po_numbers (bid_id, po_number)
            VALUES (%s, %s)
            RETURNING id
        """, (bid_id, data['po_number']))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'PO number added successfully'})
    except Exception as e:
        print(f"Error adding PO number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bids/<bid_number>/move-to-closure', methods=['POST'])
def move_to_closure(bid_number):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"Moving bid {bid_number} to closure...")
        
        # Update bid status using bid_number
        cur.execute("""
            UPDATE bids 
            SET status = 'closure'
            WHERE bid_number = %s
            RETURNING id, bid_number, status
        """, (bid_number,))
        
        result = cur.fetchone()
        print(f"Update result: {result}")
        
        if not result:
            return jsonify({"error": f"Bid {bid_number} not found"}), 404
            
        conn.commit()
        
        return jsonify({
            'id': result[0],
            'bid_number': result[1],
            'status': result[2],
            'message': 'Bid moved to closure successfully'
        })
    except Exception as e:
        print(f"Error moving bid to closure: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/field-data', methods=['GET'])
def get_field_data(bid_id):
    try:
        print(f"Fetching field data for bid: {bid_id}")  # Debug log
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get partners
        cur.execute("""
            SELECT DISTINCT p.id, p.partner_name
            FROM partners p
            JOIN partner_responses pr ON p.id = pr.partner_id
            WHERE pr.bid_id = %s
            ORDER BY p.partner_name
        """, (bid_id,))
        partners = cur.fetchall()
        print(f"Found partners: {partners}")  # Debug log

        # Get LOI options
        cur.execute("""
            SELECT DISTINCT loi
            FROM partner_responses
            WHERE bid_id = %s
            ORDER BY loi
        """, (bid_id,))
        loi_options = [{'loi': row['loi']} for row in cur.fetchall()]
        print(f"Found LOI options: {loi_options}")  # Debug log

        # Get audiences with their countries and responses
        cur.execute("""
            SELECT 
                bta.id,
                bta.audience_name,
                bta.ta_category,
                bac.country,
                bac.sample_size,
                pr.partner_id,
                pr.loi,
                par.commitment,
                par.cpi,
                par.allocation
            FROM bid_target_audiences bta
            JOIN bid_audience_countries bac ON bta.id = bac.audience_id
            LEFT JOIN partner_responses pr ON pr.bid_id = bta.bid_id
            LEFT JOIN partner_audience_responses par ON (
                par.partner_response_id = pr.id 
                AND par.audience_id = bta.id 
                AND par.country = bac.country
            )
            WHERE bta.bid_id = %s
            ORDER BY bta.id, bac.country
        """, (bid_id,))
        rows = cur.fetchall()
        print(f"Found {len(rows)} audience rows")  # Debug log

        # Structure audiences data
        audiences = []
        current_audience = None
        
        for row in rows:
            if not current_audience or current_audience['id'] != row['id']:
                current_audience = {
                    'id': row['id'],
                    'audience_name': row['audience_name'],
                    'ta_category': row['ta_category'],
                    'countries': []
                }
                audiences.append(current_audience)
            
            if row['country'] not in [c['country'] for c in current_audience['countries']]:
                current_audience['countries'].append({
                    'country': row['country'],
                    'sample_size': row['sample_size']
                })

        # Get responses separately
        responses = []
        for row in rows:
            if row['partner_id'] and row['loi']:
                responses.append({
                    'partner_id': row['partner_id'],
                    'audience_id': row['id'],
                    'country': row['country'],
                    'loi': row['loi'],
                    'commitment': row['commitment'] or 0,
                    'cpi': float(row['cpi']) if row['cpi'] is not None else 0,
                    'allocation': row['allocation'] or 0
                })

        result = {
            'partners': partners,
            'loi_options': loi_options,
            'audiences': audiences,
            'responses': responses
        }
        print(f"Returning data: {result}")  # Debug log
        return jsonify(result)

    except Exception as e:
        print(f"Error getting field data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/field-allocations', methods=['GET', 'POST'])
def update_field_allocation(bid_id):
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # First get all audiences for this bid
            cur.execute("""
                SELECT 
                    bta.id,
                    bta.audience_name,
                    bta.ta_category,
                    bac.country,
                    bac.sample_size as required,
                    pr.partner_id,
                    pr.loi,
                    par.commitment,
                    par.cpi,
                    par.allocation
                FROM bid_target_audiences bta
                JOIN bid_audience_countries bac ON bta.id = bac.audience_id
                LEFT JOIN partner_responses pr ON pr.bid_id = bta.bid_id
                LEFT JOIN partner_audience_responses par ON (
                    par.partner_response_id = pr.id 
                    AND par.audience_id = bta.id 
                    AND par.country = bac.country
                )
                WHERE bta.bid_id = %s
                ORDER BY bta.id, bac.country
            """, (bid_id,))

            rows = cur.fetchall()

            # Structure the response
            audiences = {}
            for row in rows:
                audience_id = row['id']
                if audience_id not in audiences:
                    audiences[audience_id] = {
                        'id': audience_id,
                        'name': row['audience_name'],
                        'ta_category': row['ta_category'],
                        'countries': {}
                    }
                
                country = row['country']
                if country not in audiences[audience_id]['countries']:
                    audiences[audience_id]['countries'][country] = {
                        'required': row['required'],
                        'partners': {}
                    }

                if row['partner_id'] and row['loi']:
                    partner_key = f"{row['partner_id']}-{row['loi']}"
                    audiences[audience_id]['countries'][country]['partners'][partner_key] = {
                        'commitment': row['commitment'] or 0,
                        'cpi': float(row['cpi']) if row['cpi'] is not None else 0,
                        'allocation': row['allocation'] or 0
                    }

            return jsonify(list(audiences.values()))

        except Exception as e:
            print(f"Error getting field allocations: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    elif request.method == 'POST':
        try:
            data = request.json
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Get response_id for the specific partner and LOI
            cur.execute("""
                SELECT id FROM partner_responses 
                WHERE bid_id = %s AND partner_id = %s AND loi = %s
            """, (bid_id, data['partner_id'], data['loi']))
            
            response = cur.fetchone()
            if response:
                response_id = response[0]
                
                # Update allocation without updated_at
                cur.execute("""
                    UPDATE partner_audience_responses 
                    SET allocation = %s
                    WHERE partner_response_id = %s 
                    AND audience_id = %s 
                    AND country = %s
                    RETURNING id
                """, (
                    data['allocation'],
                    response_id,
                    data['audience_id'],
                    data['country']
                ))
                
                updated_id = cur.fetchone()[0]
                conn.commit()
                return jsonify({'id': updated_id, 'message': 'Allocation updated successfully'})
            else:
                return jsonify({"error": "Partner response not found"}), 404
                
        except Exception as e:
            print(f"Error updating allocation: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

@app.route('/api/bids/closure', methods=['GET'])
def get_closure_bids():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Modified query removing field_close_date and fixing aggregations
        cur.execute("""
            SELECT DISTINCT ON (b.id)
                b.id,
                bpo.po_number,
                b.bid_number,
                b.study_name,
                c.client_name,
                COALESCE(metrics.total_delivered, 0) as total_n_delivered,
                COALESCE(metrics.total_rejects, 0) as quality_rejects,
                COALESCE(metrics.avg_loi, 0) as avg_loi,
                COALESCE(metrics.avg_ir, 0) as avg_ir,
                b.status
            FROM bids b
            LEFT JOIN bid_po_numbers bpo ON b.id = bpo.bid_id
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN (
                SELECT 
                    bid_id,
                    SUM(n_delivered) as total_delivered,
                    SUM(quality_rejects) as total_rejects,
                    AVG(final_loi) as avg_loi,
                    AVG(final_ir) as avg_ir
                FROM partner_audience_responses
                GROUP BY bid_id
            ) metrics ON b.id = metrics.bid_id
            WHERE b.status = 'closure'
            ORDER BY b.id, b.updated_at DESC
        """)
        
        bids = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(bids)
        
    except Exception as e:
        print(f"Error fetching closure bids: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bids/closure/<int:bid_id>', methods=['GET'])
def get_closure_bid_details(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get unique partner-LOI combinations with their allocation status
        cur.execute("""
            SELECT DISTINCT 
                p.id as partner_id,
                p.partner_name,
                pr.loi,
                CASE WHEN EXISTS (
                    SELECT 1 
                    FROM partner_audience_responses par 
                    WHERE par.partner_response_id = pr.id 
                    AND par.allocation > 0
                ) THEN true ELSE false END as has_allocation
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = %s
            ORDER BY p.partner_name, pr.loi
        """, (bid_id,))
        
        partners_result = cur.fetchall()
        
        # Get audience details with metrics - Modified to handle new countries
        cur.execute("""
            WITH partner_metrics AS (
                SELECT 
                    par.audience_id,
                    par.country,
                    par.commitment as required,
                    par.allocation,
                    COALESCE(par.n_delivered, 0) as n_delivered,  -- Set NULL to 0
                    par.final_loi,
                    par.final_ir,
                    par.final_timeline,
                    par.quality_rejects,
                    par.communication_rating,
                    par.engagement_rating,
                    par.problem_solving_rating,
                    par.additional_feedback,
                    pr.loi,
                    p.partner_name,
                    pr.id as partner_response_id
                FROM partner_audience_responses par
                JOIN partner_responses pr ON par.partner_response_id = pr.id
                JOIN partners p ON pr.partner_id = p.id
                WHERE pr.bid_id = %s
            )
            SELECT 
                bta.id as audience_id,
                bta.audience_name,
                bta.ta_category as ta_category,
                bc.country,
                COALESCE(pm.required, 0) as required,
                COALESCE(pm.allocation, 0) as allocation,
                COALESCE(pm.n_delivered, 0) as n_delivered,  -- Set NULL to 0
                pm.final_loi,
                pm.final_ir,
                pm.final_timeline,
                pm.quality_rejects,
                pm.communication_rating,
                pm.engagement_rating,
                pm.problem_solving_rating,
                pm.additional_feedback,
                pm.partner_name,
                pm.loi
            FROM bid_target_audiences bta
            JOIN bid_audience_countries bc ON bta.id = bc.audience_id
            LEFT JOIN partner_metrics pm ON 
                pm.audience_id = bta.id AND
                pm.country = bc.country
            WHERE bta.bid_id = %s
            ORDER BY bta.id, bc.country, pm.partner_name, pm.loi
        """, (bid_id, bid_id))
        
        audiences_result = cur.fetchall()
        
        # Format response data
        response_data = {
            'partners': {},
            'audiences': {}
        }
        
        # Process partners with allocation info
        for partner in partners_result:
            if partner['partner_name'] not in response_data['partners']:
                response_data['partners'][partner['partner_name']] = {
                    'id': partner['partner_id'],
                    'lois': [],
                    'has_allocation': {}
                }
            response_data['partners'][partner['partner_name']]['lois'].append(partner['loi'])
            response_data['partners'][partner['partner_name']]['has_allocation'][partner['loi']] = partner['has_allocation']
        
        # Process audiences
        for row in audiences_result:
            audience_id = row['audience_id']
            if audience_id not in response_data['audiences']:
                response_data['audiences'][audience_id] = {
                    'name': row['audience_name'],
                    'category': row['ta_category'],
                    'countries': {},
                    'metrics': {}
                }
            
            # Add country data with zero for new countries
            if row['country'] not in response_data['audiences'][audience_id]['countries']:
                response_data['audiences'][audience_id]['countries'][row['country']] = {
                    'required': row['required'],
                    'allocation': row['allocation'],
                    'delivered': 0  # Set to 0 for new countries
                }
            
            # Add metrics data only if we have partner info
            if row['partner_name'] and row['loi']:
                partner_key = f"{row['partner_name']}_{row['loi']}"
                if partner_key not in response_data['audiences'][audience_id]['metrics']:
                    response_data['audiences'][audience_id]['metrics'][partner_key] = {
                        'finalLOI': row['final_loi'],
                        'finalIR': row['final_ir'],
                        'finalTimeline': row['final_timeline'],
                        'qualityRejects': row['quality_rejects'],
                        'communication': row['communication_rating'],
                        'engagement': row['engagement_rating'],
                        'problemSolving': row['problem_solving_rating'],
                        'additionalFeedback': row['additional_feedback']
                    }
        
        cur.close()
        conn.close()
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error fetching closure bid details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bids/<int:bid_id>/audiences', methods=['GET'])
def get_bid_audiences(bid_id):
    try:
        partner = request.args.get('partner')
        loi = request.args.get('loi')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"Fetching data for bid {bid_id}, partner {partner}, LOI {loi}")  # Debug log
        
        # Modified query to only get records where allocation > 0
        cur.execute("""
            WITH valid_responses AS (
                SELECT 
                    bta.id,
                    bta.audience_name as category,
                    par.country as country_name,
                    par.commitment as required,
                    par.allocation,
                    par.n_delivered as delivered,
                    par.field_close_date,
                    pr.id as partner_response_id,
                    par.final_loi as "finalLOI",
                    par.final_ir as "finalIR",
                    par.final_timeline as "finalTimeline",
                    par.quality_rejects as "qualityRejects",
                    par.communication_rating as "communication",
                    par.engagement_rating as "engagement",
                    par.problem_solving_rating as "problemSolving",
                    par.additional_feedback as "additionalFeedback"
                FROM bid_target_audiences bta
                JOIN partner_audience_responses par ON par.audience_id = bta.id
                JOIN partner_responses pr ON pr.id = par.partner_response_id
                JOIN partners p ON pr.partner_id = p.id
                WHERE par.bid_id = %s 
                AND p.partner_name = %s
                AND pr.loi = %s
                AND par.allocation > 0  -- Only get records with allocation > 0
            )
            SELECT *
            FROM valid_responses vr
            WHERE EXISTS (
                -- Only include audiences that have at least one country with allocation > 0
                SELECT 1 
                FROM valid_responses vr2 
                WHERE vr2.id = vr.id
            )
            ORDER BY vr.id, vr.country_name
        """, (bid_id, partner, loi))
        
        rows = cur.fetchall()
        print(f"Found {len(rows)} rows")  # Debug log
        
        # Group by audience
        audiences = {}
        for row in rows:
            audience_id = row['id']
            if audience_id not in audiences:
                audiences[audience_id] = {
                    'id': audience_id,
                    'category': row['category'],
                    'field_close_date': row['field_close_date'].isoformat() if row['field_close_date'] else None,
                    'metrics': {
                        'finalLOI': row['finalLOI'],
                        'finalIR': row['finalIR'],
                        'finalTimeline': row['finalTimeline'],
                        'qualityRejects': row['qualityRejects'],
                        'communication': row['communication'],
                        'engagement': row['engagement'],
                        'problemSolving': row['problemSolving'],
                        'additionalFeedback': row['additionalFeedback']
                    },
                    'countries': []
                }
            
            # Only add countries with allocation > 0
            if row['allocation'] > 0:
                audiences[audience_id]['countries'].append({
                    'name': row['country_name'],
                    'required': row['required'],
                    'allocation': row['allocation'],
                    'delivered': row['delivered']
                })
        
        # Filter out audiences with no countries (all had allocation = 0)
        result = [audience for audience in audiences.values() if audience['countries']]
        print(f"Returning data: {result}")  # Debug log
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching audiences: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/closure', methods=['POST'])
def save_closure_data(bid_id):
    try:
        data = request.json
        partner = data.get('partner')
        loi = data.get('loi')
        form_data = data.get('data')
        
        conn = get_db_connection()
        cur = conn.cursor()

        # Get partner_response_id for this partner and LOI
        cur.execute("""
            SELECT pr.id 
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = %s AND p.partner_name = %s AND pr.loi = %s
        """, (bid_id, partner, loi))
        
        partner_response_id = cur.fetchone()[0]

        # Update partner_audience_responses table
        for key, value in form_data.items():
            if key.startswith('metrics_'):
                # Parse the metrics key format: metrics_audienceId_partner_loi
                parts = key.split('_')
                if len(parts) >= 4 and parts[2] == partner and int(parts[3]) == int(loi):
                    audience_id = parts[1]
                    metrics = value
                    
                    # Convert empty strings to None for numeric fields
                    final_loi = int(metrics.get('finalLOI')) if metrics.get('finalLOI') not in ['', None] else None
                    final_ir = float(metrics.get('finalIR')) if metrics.get('finalIR') not in ['', None] else None
                    final_timeline = int(metrics.get('finalTimeline')) if metrics.get('finalTimeline') not in ['', None] else None
                    quality_rejects = int(metrics.get('qualityRejects')) if metrics.get('qualityRejects') not in ['', None] else None
                    communication = int(metrics.get('communication')) if metrics.get('communication') not in ['', None] else None
                    engagement = int(metrics.get('engagement')) if metrics.get('engagement') not in ['', None] else None
                    problem_solving = int(metrics.get('problemSolving')) if metrics.get('problemSolving') not in ['', None] else None
                    
                    cur.execute("""
                        UPDATE partner_audience_responses par
                        SET 
                            final_loi = %s,
                            final_ir = %s,
                            final_timeline = %s,
                            quality_rejects = %s,
                            communication_rating = %s,
                            engagement_rating = %s,
                            problem_solving_rating = %s,
                            additional_feedback = %s
                        WHERE partner_response_id = %s 
                        AND audience_id = %s
                        AND allocation > 0
                    """, (
                        final_loi,
                        final_ir,
                        final_timeline,
                        quality_rejects,
                        communication,
                        engagement,
                        problem_solving,
                        metrics.get('additionalFeedback'),
                        partner_response_id,
                        audience_id
                    ))
            else:
                # Handle delivered numbers for this partner/LOI
                audience_id, country = key.split('_')
                delivered = value.get('delivered')
                
                # Convert empty string to None for n_delivered
                n_delivered = int(delivered) if delivered not in ['', None] else None
                
                cur.execute("""
                    UPDATE partner_audience_responses par
                    SET n_delivered = %s
                    WHERE partner_response_id = %s 
                    AND audience_id = %s 
                    AND country = %s
                    AND allocation > 0
                """, (n_delivered, partner_response_id, audience_id, country))

        conn.commit()
        return jsonify({"message": "Closure data saved successfully"}), 200
        
    except Exception as e:
        print(f"Error saving closure data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<int:bid_id>/closure-data', methods=['GET'])
def get_closure_data(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get metrics data with LOI-specific information
        cur.execute("""
            WITH audience_metrics AS (
                SELECT 
                    par.audience_id,
                    pr.partner_id,
                    pr.loi,
                    par.n_delivered,
                    par.final_loi,
                    par.final_ir,
                    par.final_timeline,
                    par.quality_rejects,
                    par.communication_rating,
                    par.engagement_rating,
                    par.problem_solving_rating,
                    par.additional_feedback
                FROM partner_audience_responses par
                JOIN partner_responses pr ON par.partner_response_id = pr.id
                WHERE pr.bid_id = %s
            )
            SELECT 
                am.*,
                p.partner_name,
                bta.name as audience_name,
                bta.category as audience_category,
                bc.country,
                bc.required,
                par.allocation
            FROM audience_metrics am
            JOIN partners p ON am.partner_id = p.id
            JOIN bid_target_audiences bta ON am.audience_id = bta.id
            JOIN bid_audience_countries bc ON bta.id = bc.audience_id
            LEFT JOIN partner_audience_responses par ON 
                am.audience_id = par.audience_id AND
                am.partner_id = par.partner_id AND
                bc.country = par.country
            WHERE par.allocation > 0
            ORDER BY am.audience_id, p.partner_name, am.loi, bc.country
        """, (bid_id,))
        
        rows = cur.fetchall()
        
        # Organize the data
        closure_data = {}
        for row in rows:
            audience_key = str(row['audience_id'])
            partner_key = f"{row['partner_name']}_{row['loi']}"
            country = row['country']
            
            # Initialize audience if not exists
            if audience_key not in closure_data:
                closure_data[audience_key] = {
                    'name': row['audience_name'],
                    'category': row['audience_category'],
                    'countries': {},
                    'metrics': {}
                }
            
            # Add country data
            if country not in closure_data[audience_key]['countries']:
                closure_data[audience_key]['countries'][country] = {
                    'required': row['required'],
                    'allocation': row['allocation'],
                    'delivered': row['n_delivered'] if row['n_delivered'] is not None else ''
                }
            
            # Add metrics data
            if partner_key not in closure_data[audience_key]['metrics']:
                closure_data[audience_key]['metrics'][partner_key] = {
                    'finalLOI': row['final_loi'],
                    'finalIR': row['final_ir'],
                    'finalTimeline': row['final_timeline'],
                    'qualityRejects': row['quality_rejects'],
                    'communication': row['communication_rating'],
                    'engagement': row['engagement_rating'],
                    'problemSolving': row['problem_solving_rating'],
                    'additionalFeedback': row['additional_feedback']
                }
        
        cur.close()
        conn.close()
        
        return jsonify(closure_data)
        
    except Exception as e:
        print(f"Error fetching closure data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bids/ready-for-invoice', methods=['GET'])
def get_ready_for_invoice_bids():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            WITH bid_metrics AS (
                SELECT 
                    par.bid_id,
                    SUM(par.n_delivered) as total_delivered,
                    AVG(COALESCE(par.final_loi, par.timeline_days)) as avg_final_loi,
                    AVG(par.cpi) as avg_initial_cpi,
                    AVG(par.final_ir) as avg_final_ir,
                    AVG(COALESCE(par.final_cpi, par.cpi)) as avg_final_cpi,
                    SUM(COALESCE(par.final_cost, par.cpi * par.n_delivered)) as total_final_cost,
                    SUM(par.allocation) as total_allocation
                FROM partner_audience_responses par
                WHERE par.n_delivered > 0
                GROUP BY par.bid_id
            )
            SELECT DISTINCT ON (b.id)
                bpo.po_number,
                b.bid_number,
                b.study_name,
                c.client_name,
                ROUND(COALESCE(bm.avg_initial_cpi, 0)::numeric, 2) as avg_initial_cpi,
                COALESCE(bm.total_allocation, 0) as allocation,
                COALESCE(bm.total_delivered, 0) as n_delivered,
                ROUND(COALESCE(bm.avg_final_loi, 0)::numeric, 2) as avg_final_loi,
                ROUND(COALESCE(bm.avg_final_ir, 0)::numeric, 2) as avg_final_ir,
                ROUND(COALESCE(bm.avg_final_cpi, 0)::numeric, 2) as avg_final_cpi,
                ROUND(COALESCE(bm.total_final_cost, 0)::numeric, 2) as invoice_amount,
                b.status
            FROM bids b
            LEFT JOIN bid_po_numbers bpo ON b.id = bpo.bid_id
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN bid_metrics bm ON b.id = bm.bid_id
            WHERE b.status IN ('ready_for_invoice', 'invoiced')
            ORDER BY b.id, b.updated_at DESC
        """)
        
        bids = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(bids)
        
    except Exception as e:
        print(f"Error fetching ready for invoice bids: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoice/<int:bid_id>/partner-data', methods=['GET'])
def get_partner_loi_data(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get bid id from bid_number
        cur.execute("SELECT id FROM bids WHERE bid_number = %s", (str(bid_id),))
        bid = cur.fetchone()
        if not bid:
            return jsonify({"error": f"Bid {bid_id} not found"}), 404
        actual_bid_id = bid[0]

        # Get PO number
        cur.execute("""
            SELECT po_number 
            FROM bid_po_numbers 
            WHERE bid_id = %s
        """, (actual_bid_id,))
        po_result = cur.fetchone()
        po_number = po_result[0] if po_result else ''

        # Get saved invoice details for all partners and LOIs
        cur.execute("""
            SELECT 
                p.partner_name,
                pr.loi,
                pr.invoice_date,
                pr.invoice_sent,
                pr.invoice_serial,
                pr.invoice_number,
                pr.invoice_amount,
                pr.id as response_id
            FROM partner_responses pr
            JOIN partners p ON p.id = pr.partner_id
            WHERE pr.bid_id = %s
            AND EXISTS (
                SELECT 1 
                FROM partner_audience_responses par 
                WHERE par.partner_response_id = pr.id 
                AND par.n_delivered > 0
            )
        """, (actual_bid_id,))
        
        # Create a map of partner_name+loi to invoice details
        invoice_details_map = {}
        for row in cur.fetchall():
            key = f"{row[0]}_{row[1]}"  # partner_name_loi as key
            invoice_details_map[key] = {
                'invoice_date': row[2].strftime('%Y-%m-%d') if row[2] else '',
                'invoice_sent': row[3].strftime('%Y-%m-%d') if row[3] else '',
                'invoice_serial': row[4] or '',
                'invoice_number': row[5] or '',
                'invoice_amount': str(row[6]) if row[6] else '0.00'
            }
        
        # Get deliverables data
        cur.execute("""
            WITH partner_lois AS (
                SELECT 
                    p.id as partner_id,
                    p.partner_name,
                    pr.id as response_id,
                    pr.loi,
                    pr.invoice_date,
                    pr.invoice_sent,
                    pr.invoice_serial,
                    pr.invoice_number,
                    pr.invoice_amount
                FROM partners p
                JOIN partner_responses pr ON pr.partner_id = p.id
                WHERE pr.bid_id = %s
                AND EXISTS (
                    SELECT 1 
                    FROM partner_audience_responses par 
                    WHERE par.partner_response_id = pr.id 
                    AND par.n_delivered > 0
                )
            )
            SELECT 
                pl.partner_name,
                pl.loi,
                pl.invoice_date,
                pl.invoice_sent,
                pl.invoice_serial,
                pl.invoice_number,
                pl.invoice_amount,
                par.audience_id,
                par.country,
                par.allocation,
                par.n_delivered,
                par.cpi as initial_cpi,
                COALESCE(par.final_cpi, par.cpi) as final_cpi,
                COALESCE(par.initial_cost, (par.cpi * par.allocation)) as initial_cost,
                COALESCE(par.final_cost, (par.final_cpi * par.n_delivered)) as final_cost
            FROM partner_lois pl
            JOIN partner_audience_responses par ON par.partner_response_id = pl.response_id
            WHERE par.n_delivered > 0
            ORDER BY pl.partner_name, pl.loi, par.audience_id, par.country
        """, (actual_bid_id,))

        results = cur.fetchall()
        if not results:
            return jsonify({"error": "No partner data found for this bid"}), 404

        # Group deliverables by partner and LOI
        deliverables_by_partner = {}
        for row in results:
            partner_name = row[0]
            loi = row[1]
            key = f"{partner_name}_{loi}"
            
            if key not in deliverables_by_partner:
                deliverables_by_partner[key] = []
            
            deliverables_by_partner[key].append({
                "partner_name": partner_name,
                "loi": loi,
                "audience_id": row[7],
                "country": row[8],
                "allocation": row[9],
                "n_delivered": row[10] if row[10] is not None else 0,
                "initial_cpi": float(row[11]) if row[11] is not None else 0.0,
                "final_cpi": float(row[12]) if row[12] is not None else 0.0,
                "initial_cost": float(row[13]) if row[13] is not None else 0.0,
                "final_cost": float(row[14]) if row[14] is not None else 0.0,
                "savings": float(row[13] - row[14]) if row[13] is not None and row[14] is not None else 0.0
            })

        response_data = {
            "po_number": po_number,
            "partner_data": {
                key: {
                    **invoice_details_map.get(key, {
                        'invoice_date': '',
                        'invoice_sent': '',
                        'invoice_serial': '',
                        'invoice_number': '',
                        'invoice_amount': '0.00'
                    }),
                    "deliverables": deliverables
                }
                for key, deliverables in deliverables_by_partner.items()
            }
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in get_partner_loi_data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/invoice/<int:bid_id>/<string:partner_name>/<int:loi>/details', methods=['GET'])
def get_invoice_details(bid_id, partner_name, loi):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                par.audience_id,
                par.country,
                par.allocation::INTEGER,
                par.n_delivered::INTEGER as "nDelivered",
                COALESCE(par.cpi::NUMERIC, 0) as "initialCPI",
                COALESCE(par.final_cpi::NUMERIC, 0) as "finalCPI",
                COALESCE(par.n_delivered::NUMERIC * par.cpi::NUMERIC, 0) as "initialCost",
                COALESCE(par.final_cost::NUMERIC, 0) as "finalCost",
                COALESCE((par.n_delivered::NUMERIC * par.cpi::NUMERIC) - par.final_cost::NUMERIC, 0) as savings,
                bpn.po_number
            FROM partner_audience_responses par
            JOIN partner_responses pr ON par.partner_response_id = pr.id
            JOIN partners p ON pr.partner_id = p.id
            JOIN bids b ON pr.bid_id = b.id
            LEFT JOIN bid_po_numbers bpn ON b.id = bpn.bid_id
            WHERE b.bid_number = %s::VARCHAR 
            AND p.partner_name = %s 
            AND pr.loi = %s
            AND par.n_delivered > 0
        """, (bid_id, partner_name, loi))
        
        deliverables = cur.fetchall()
        po_number = deliverables[0]['po_number'] if deliverables else None
        
        return jsonify({
            "deliverables": deliverables,
            "po_number": po_number
        })

    except Exception as e:
        print(f"Error in get_invoice_details: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/invoice/<int:bid_number>/save', methods=['POST'])
def save_invoice_data(bid_number):
    conn = None
    cur = None
    try:
        data = request.json
        print(f"Received invoice data: {data}")
        conn = get_db_connection()
        cur = conn.cursor()

        # Start transaction
        cur.execute("BEGIN")
        
        # First, get the actual bid_id from the bid_number
        cur.execute("SELECT id FROM bids WHERE bid_number = %s", (str(bid_number),))
        bid_row = cur.fetchone()
        if not bid_row:
            raise Exception(f"Bid with number {bid_number} not found")
        
        bid_id = bid_row[0]
        print(f"Found bid_id {bid_id} for bid_number {bid_number}")

        # Update invoice details in partner_responses only if they are provided and not empty/null
        if all(key in data['invoice_data'] and data['invoice_data'][key] for key in ['invoice_date', 'invoice_sent', 'invoice_serial', 'invoice_number']):
            cur.execute("""
                UPDATE partner_responses pr
                SET 
                    invoice_date = %s::DATE,
                    invoice_sent = %s::DATE,
                    invoice_serial = %s,
                    invoice_number = %s,
                    invoice_amount = %s::DECIMAL,
                    updated_at = CURRENT_TIMESTAMP
                FROM partners p
                WHERE pr.bid_id = %s
                AND p.partner_name = %s
                AND pr.partner_id = p.id
                AND pr.loi = %s
            """, (
                data['invoice_data']['invoice_date'],
                data['invoice_data']['invoice_sent'],
                data['invoice_data']['invoice_serial'],
                data['invoice_data']['invoice_number'],
                data['invoice_data']['invoice_amount'],
                bid_id,
                data['partner_name'],
                data['loi']
            ))

        # Get partner_id from partner_name
        cur.execute("""
            SELECT id FROM partners WHERE partner_name = %s
        """, (data['partner_name'],))
        
        partner_row = cur.fetchone()
        if not partner_row:
            raise Exception(f"Partner '{data['partner_name']}' not found")
        
        partner_id = partner_row[0]
        
        # Get partner_response_id
        cur.execute("""
            SELECT id FROM partner_responses 
            WHERE bid_id = %s AND partner_id = %s AND loi = %s
        """, (bid_id, partner_id, data['loi']))
        
        response_row = cur.fetchone()
        if not response_row:
            # If partner_response doesn't exist, create it
            print(f"Creating new partner_response for bid_id={bid_id}, partner_id={partner_id}, loi={data['loi']}")
            cur.execute("""
                INSERT INTO partner_responses 
                (bid_id, partner_id, loi, status, currency, pmf, created_at)
                VALUES (%s, %s, %s, 'pending', 'USD', 0, CURRENT_TIMESTAMP)
                RETURNING id
            """, (bid_id, partner_id, data['loi']))
            response_row = cur.fetchone()
            if not response_row:
                raise Exception("Failed to create partner_response record")
        
        partner_response_id = response_row[0]

        # Update partner_audience_responses for each deliverable
        for deliverable in data['deliverables']:
            print(f"Updating deliverable: {deliverable}")
            
            # Check if partner_audience_response exists
            cur.execute("""
                SELECT id FROM partner_audience_responses
                WHERE partner_response_id = %s
                AND audience_id = %s
                AND country = %s
            """, (
                partner_response_id,
                deliverable['audience_id'],
                deliverable['country']
            ))
            
            par_row = cur.fetchone()
            
            if par_row:
                # Update existing record
                cur.execute("""
                    UPDATE partner_audience_responses
                    SET 
                        final_cpi = %s,
                        final_cost = %s,
                        initial_cost = COALESCE(initial_cost, n_delivered * cpi),
                        savings = COALESCE(n_delivered * cpi, 0) - %s
                    WHERE id = %s
                """, (
                    deliverable['final_cpi'],
                    deliverable['final_cost'],
                    deliverable['final_cost'],
                    par_row[0]
                ))
            else:
                # Create a new record
                print(f"Creating new partner_audience_response for response_id={partner_response_id}, audience_id={deliverable['audience_id']}, country={deliverable['country']}")
                cur.execute("""
                    INSERT INTO partner_audience_responses 
                    (bid_id, partner_response_id, audience_id, country, 
                     cpi, final_cpi, final_cost, n_delivered, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    bid_id,
                    partner_response_id,
                    deliverable['audience_id'],
                    deliverable['country'],
                    0,  # Initial CPI
                    deliverable['final_cpi'],
                    deliverable['final_cost'],
                    deliverable['final_cost'] / deliverable['final_cpi'] if deliverable['final_cpi'] > 0 else 0
                ))

        conn.commit()
        return jsonify({"message": "Data saved successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error saving invoice data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/bids/next-number', methods=['GET'])
def get_next_bid_number():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get the highest bid number
        cur.execute("""
            SELECT COALESCE(MAX(CAST(bid_number AS INTEGER)), 39999) 
            FROM bids
        """)
        current_max = cur.fetchone()[0]
        
        # Generate next bid number
        next_bid_number = str(current_max + 1)
        
        return jsonify({"next_bid_number": next_bid_number})
    
    except Exception as e:
        print(f"Error getting next bid number: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/status', methods=['POST'])
def update_bid_status(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = request.json
        status = data.get('status')
        po_number = data.get('po_number')

        # Start transaction
        cur.execute("BEGIN")

        # Standardize status values
        status_mapping = {
            'infield': 'infield',
            'in_field': 'infield',
            'in-field': 'infield',
            'draft': 'draft',
            'completed': 'completed',
            'invoiced': 'invoiced'
        }

        # Map the incoming status to standardized value
        standardized_status = status_mapping.get(status.lower(), status)

        # Update bid status
        cur.execute("""
            UPDATE bids 
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (standardized_status, bid_id))

        # Insert or update PO number in bid_po_numbers table
        if po_number:
            cur.execute("""
                INSERT INTO bid_po_numbers (bid_id, po_number, created_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (bid_id) DO UPDATE 
                SET po_number = EXCLUDED.po_number,
                    updated_at = CURRENT_TIMESTAMP
            """, (bid_id, po_number))

        conn.commit()
        return jsonify({"message": "Bid status updated successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error updating bid status: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/invoice-data', methods=['GET'])
def get_invoice_data(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # First get only valid partners and their LOIs where there's actual data
        cur.execute("""
            WITH valid_combinations AS (
                SELECT DISTINCT 
                    p.id as partner_id,
                    p.partner_name,
                    pr.loi
                FROM partners p
                JOIN partner_responses pr ON p.id = pr.partner_id
                JOIN partner_audience_responses par ON pr.id = par.partner_response_id
                WHERE pr.bid_id = %s
                AND (par.allocation > 0 OR par.n_delivered > 0)
                GROUP BY p.id, p.partner_name, pr.loi
                HAVING BOOL_OR(par.allocation > 0 OR par.n_delivered > 0)
            )
            SELECT 
                partner_id,
                partner_name,
                array_agg(loi ORDER BY loi) as valid_lois
            FROM valid_combinations
            GROUP BY partner_id, partner_name
            ORDER BY partner_name
        """, (bid_id,))
        
        partner_data = cur.fetchall()

        # Structure partners and their valid LOIs
        partners = []
        partner_lois = {}
        
        for row in partner_data:
            partners.append({
                'id': row['partner_id'],
                'partner_name': row['partner_name']
            })
            partner_lois[row['partner_id']] = row['valid_lois']

        # Get bid details
        cur.execute("""
            SELECT 
                b.study_name,
                b.status,
                b.bid_number,
                bpn.po_number
            FROM bids b
            LEFT JOIN bid_po_numbers bpn ON b.id = bpn.bid_id
            WHERE b.id = %s
        """, (bid_id,))
        bid_details = cur.fetchone()

        # Get audience data only for valid combinations
        if partners:  # Only get audience data if we have valid partners
            cur.execute("""
                SELECT 
                    bta.id as audience_id,
                    bta.audience_name,
                    bta.ta_category,
                    pr.partner_id,
                    pr.loi,
                    par.country,
                    par.allocation,
                    par.n_delivered,
                    par.cpi as initial_cpi,
                    par.final_cpi,
                    COALESCE(par.initial_cost, par.allocation * par.cpi) as initial_cost,
                    COALESCE(par.final_cost, par.n_delivered * COALESCE(par.final_cpi, par.cpi)) as final_cost
                FROM bid_target_audiences bta
                JOIN partner_responses pr ON pr.bid_id = bta.bid_id
                JOIN partner_audience_responses par ON (
                    par.partner_response_id = pr.id 
                    AND par.audience_id = bta.id
                )
                WHERE bta.bid_id = %s
                AND (par.allocation > 0 OR par.n_delivered > 0)
                AND EXISTS (
                    SELECT 1 
                    FROM unnest(%s::int[]) valid_partner_id 
                    WHERE valid_partner_id = pr.partner_id
                )
                AND EXISTS (
                    SELECT 1 
                    FROM (
                        SELECT DISTINCT partner_id, unnest(valid_lois) as loi 
                        FROM valid_combinations
                    ) vc 
                    WHERE vc.partner_id = pr.partner_id 
                    AND vc.loi = pr.loi
                )
                ORDER BY bta.id, pr.partner_id, pr.loi, par.country
            """, (bid_id, [p['id'] for p in partners]))
            
            rows = cur.fetchall()
        else:
            rows = []

        # Group data by audience
        audiences = []
        current_audience = None
        
        for row in rows:
            if not current_audience or current_audience['id'] != row['audience_id']:
                current_audience = {
                    'id': row['audience_id'],
                    'name': row['audience_name'],
                    'ta_category': row['ta_category'],
                    'deliverables': []
                }
                audiences.append(current_audience)

            current_audience['deliverables'].append({
                'partner_id': row['partner_id'],
                'loi': row['loi'],
                'country': row['country'],
                'allocation': row['allocation'] or 0,
                'n_delivered': row['n_delivered'] or 0,
                'initial_cpi': float(row['initial_cpi']) if row['initial_cpi'] else 0,
                'final_cpi': float(row['final_cpi']) if row['final_cpi'] else 0,
                'initial_cost': float(row['initial_cost']) if row['initial_cost'] else 0,
                'final_cost': float(row['final_cost']) if row['final_cost'] else 0
            })

        response = {
            'partners': partners,
            'partner_lois': partner_lois,
            'bid_number': bid_details['bid_number'] if bid_details else None,
            'po_number': bid_details['po_number'] if bid_details else None,
            'status': bid_details['status'] if bid_details else None,
            'study_name': bid_details['study_name'] if bid_details else None,
            'audiences': audiences
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error getting invoice data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    print("Dashboard endpoint called")  # Debug log
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total bids
        cur.execute("SELECT COUNT(*) as total FROM bids")
        total_bids = cur.fetchone()['total']
        print(f"Total bids: {total_bids}")  # Debug log
        
        # Get active bids (assuming 'active' means in draft or infield status)
        cur.execute("""
            SELECT COUNT(*) as active 
            FROM bids 
            WHERE status IN ('draft', 'infield')
        """)
        active_bids = cur.fetchone()['active']
        
        # Calculate total savings
        cur.execute("""
            SELECT COALESCE(SUM(initial_cost - final_cost), 0) as savings
            FROM partner_audience_responses
            WHERE initial_cost IS NOT NULL AND final_cost IS NOT NULL
        """)
        total_savings = cur.fetchone()['savings']
        
        # Calculate average turnaround time
        cur.execute("""
            SELECT AVG(EXTRACT(DAY FROM (updated_at - created_at))) as avg_time
            FROM bids
            WHERE status = 'completed'
        """)
        avg_turnaround = cur.fetchone()['avg_time'] or 0
        
        # Get bids by status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM bids
            GROUP BY status
        """)
        status_counts = cur.fetchall()
        
        # Status mapping
        status_mapping = {
            'draft': 'Draft',
            'infield': 'In Field',
            'in_field': 'In Field',
            'closure': 'Closure',
            'ready_for_invoice': 'Ready to Invoice',
            'completed': 'Completed',
            'invoiced': 'Completed'  # Consider invoiced as completed
        }
        
        bids_by_status = {
            "Draft": 0,
            "Partner Response": 0,
            "In Field": 0,
            "Closure": 0,
            "Ready to Invoice": 0,
            "Completed": 0
        }
        
        for row in status_counts:
            status = row['status'].lower()
            count = row['count']
            mapped_status = status_mapping.get(status, status.capitalize())
            if mapped_status in bids_by_status:
                bids_by_status[mapped_status] += count

        # Create the dashboard data dictionary
        dashboard_data = {
            "total_bids": total_bids,
            "active_bids": active_bids,
            "total_savings": float(total_savings),
            "avg_turnaround_time": round(float(avg_turnaround), 1),
            "bids_by_status": bids_by_status
        }
        
        print(f"Sending dashboard data: {dashboard_data}")  # Debug log
        return jsonify(dashboard_data)
        
    except Exception as e:
        print(f"Error in dashboard endpoint: {str(e)}")  # Debug log
        return jsonify({
            "total_bids": 0,
            "active_bids": 0,
            "total_savings": 0,
            "avg_turnaround_time": 0,
            "bids_by_status": {
                "Draft": 0,
                "Partner Response": 0,
                "In Field": 0,
                "Closure": 0,
                "Ready to Invoice": 0,
                "Completed": 0
            }
        }), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/ready-for-invoice', methods=['GET'])
def get_ready_for_invoice():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            WITH partner_loi_stats AS (
                SELECT 
                    pr.partner_id,
                    p.partner_name AS audience_Partner,
                    pr.loi,  -- Changed from par.loi to pr.loi
                    par.country,
                    par.commitment,
                    par.cpi,
                    par.timeline_d,
                    par.comments,
                    par.allocation,
                    par.n_delivered
                FROM partner_audience_responses par
                JOIN partner_responses pr ON par.partner_response_id = pr.id
                JOIN partners p ON pr.partner_id = p.id
            )
            SELECT 
                pls.*,
                CASE 
                    WHEN pls.n_delivered = 0  -- Changed condition to only check n_delivered
                    THEN 'No respondents delivered for this LOI'
                    ELSE NULL 
                END as message
            FROM partner_loi_stats pls
            ORDER BY pls.audience_Partner, pls.loi;
        """)
        
        results = cur.fetchall()
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in get_ready_for_invoice: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Add this at the beginning of your main.py, after the imports
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        print("Starting database initialization...")  # Debug log

        # Create users table if it doesn't exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Add new columns if they don't exist
        cur.execute("""
        DO $$ 
        BEGIN
            -- Add employee_id column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'employee_id'
            ) THEN
                ALTER TABLE users ADD COLUMN employee_id VARCHAR(50) UNIQUE;
            END IF;

            -- Add team column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'team'
            ) THEN
                ALTER TABLE users ADD COLUMN team VARCHAR(50) DEFAULT 'Operations' NOT NULL;
            END IF;
        END $$;
        """)
        print("Users table and columns verified")  # Debug log

        # Check if the table is empty, if so insert default admin user
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]

        if user_count == 0:
            # Insert default admin user only if table is empty
            default_password = "password"  # Set a default password
            hashed_password = generate_password_hash(default_password)
            
            cur.execute("""
                INSERT INTO users (email, name, password_hash, role, team, employee_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('admin@example.com', 'Admin User', hashed_password, 'admin', 'Operations', 'EMP001'))
            
            print("Default admin user created")  # Debug log

        conn.commit()
        print("Database initialization completed successfully")  # Debug log

    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/closure', methods=['PUT'])
def update_closure(bid_id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()

        print(f"Updating closure data for bid {bid_id}, partner {data['partner']}, LOI {data['loi']}")

        # Update field close date and metrics for each audience per partner
        for audience in data['audienceData']:
            metrics = audience.get('metrics', {})
            field_close_date = audience.get('field_close_date')
            
            # Get n_delivered values from the countries array
            n_delivered_values = {
                country['name']: country['delivered']
                for country in audience.get('countries', [])
            }

            print(f"N delivered values: {n_delivered_values}")
            
            # First, check if a record exists
            cur.execute("""
                SELECT par.id, par.country 
                FROM partner_audience_responses par
                JOIN partner_responses pr ON par.partner_response_id = pr.id
                JOIN partners p ON pr.partner_id = p.id
                WHERE par.bid_id = %s 
                AND par.audience_id = %s
                AND p.partner_name = %s
                AND pr.loi = %s
                AND par.allocation > 0
            """, (bid_id, audience['id'], data['partner'], data['loi']))
            
            records = cur.fetchall()
            
            if records:
                print(f"Updating records for audience {audience['id']}")
                print(f"Field close date: {field_close_date}")
                print(f"Metrics: {metrics}")
                
                # Update each country record
                for record_id, country in records:
                    n_delivered = n_delivered_values.get(country)
                    print(f"Updating n_delivered for country {country}: {n_delivered}")
                    
                    cur.execute("""
                        UPDATE partner_audience_responses par
                        SET 
                            field_close_date = %s::date,
                            n_delivered = %s,
                            final_loi = %s,
                            final_ir = %s,
                            final_timeline = %s,
                            quality_rejects = %s,
                            communication_rating = %s,
                            engagement_rating = %s,
                            problem_solving_rating = %s,
                            additional_feedback = %s
                        WHERE par.id = %s
                    """, (
                        field_close_date,
                        n_delivered,
                        metrics.get('finalLOI'),
                        metrics.get('finalIR'),
                        metrics.get('finalTimeline'),
                        metrics.get('qualityRejects'),
                        metrics.get('communication'),
                        metrics.get('engagement'),
                        metrics.get('problemSolving'),
                        metrics.get('additionalFeedback'),
                        record_id
                    ))
                    print(f"Updated metrics and n_delivered for audience {audience['id']}, country {country}")
            else:
                print(f"No record found for audience {audience['id']}")

        conn.commit()
        return jsonify({"message": "Closure data updated successfully"})

    except Exception as e:
        print(f"Error updating closure: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/invoice', methods=['PUT'])
def update_bid_invoice_status(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Update bid status to 'invoiced' (standardized status)
        cur.execute("""
            UPDATE bids 
            SET status = 'invoiced'
            WHERE id = %s
        """, (bid_id,))

        conn.commit()
        return jsonify({"message": "Bid status updated to invoiced successfully"})

    except Exception as e:
        print(f"Error updating bid invoice status: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_number>', methods=['GET'])
def get_bid_by_number(bid_number):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, bid_number, status
            FROM bids
            WHERE bid_number = %s
        """, (bid_number,))
        
        bid = cur.fetchone()
        
        if not bid:
            return jsonify({"error": "Bid not found"}), 404
            
        return jsonify(bid)
        
    except Exception as e:
        print(f"Error getting bid: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_number>/move-to-infield', methods=['POST'])
def move_to_infield(bid_number):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"Moving bid {bid_number} to infield...")
        
        # Update bid status using bid_number
        cur.execute("""
            UPDATE bids 
            SET status = 'infield'
            WHERE bid_number = %s
            RETURNING id, bid_number, status
        """, (bid_number,))
        
        result = cur.fetchone()
        print(f"Update result: {result}")
        
        if not result:
            return jsonify({"error": f"Bid {bid_number} not found"}), 404
            
        conn.commit()
        
        return jsonify({
            'id': result[0],
            'bid_number': result[1],
            'status': result[2],
            'message': 'Bid moved to infield successfully'
        })
    except Exception as e:
        print(f"Error moving bid to infield: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users 
            SET email = %s,
                name = %s,
                employee_id = %s,
                role = %s,
                team = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (
            data['email'],
            data['name'],
            data['employee_id'],
            data['role'],
            data['team'],
            user_id
        ))
        
        updated_id = cur.fetchone()
        if not updated_id:
            return jsonify({"error": "User not found"}), 404
            
        conn.commit()
        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        print(f"Error updating user: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/partners', methods=['PUT'])
def update_bid_partners(bid_id):
    try:
        if str(bid_id).startswith('temp_'):
            return jsonify({"message": "Partner responses saved in session"}), 200

        bid_id = int(bid_id)
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        data = request.json
        partners = data.get('partners', [])
        lois = data.get('lois', [])

        # Start transaction
        cur.execute("BEGIN")

        # Get existing partner responses to preserve data
        cur.execute("""
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                pr.currency,
                pr.pmf,
                par.audience_id,
                par.country,
                par.commitment,
                par.cpi,
                par.timeline_days,
                par.comments
            FROM partner_responses pr
            LEFT JOIN partner_audience_responses par ON pr.id = par.partner_response_id
            WHERE pr.bid_id = %s
        """, (bid_id,))
        
        # Store existing data in a dictionary for lookup
        existing_data = {}
        existing_partners = set()  # Track existing partner-LOI combinations
        for row in cur.fetchall():
            key = f"{row['partner_id']}-{row['loi']}-{row.get('audience_id')}-{row.get('country')}"
            existing_data[key] = row
            existing_partners.add(f"{row['partner_id']}-{row['loi']}")

        # Update partner responses
        for partner in partners:
            for loi in lois:
                # Create or update partner_response
                cur.execute("""
                    INSERT INTO partner_responses 
                    (bid_id, partner_id, loi, status, currency, pmf, created_at)
                    VALUES (%s, %s, %s, 'draft', 'USD', 0, CURRENT_TIMESTAMP)
                    ON CONFLICT (bid_id, partner_id, loi) 
                    DO UPDATE SET 
                        updated_at = CURRENT_TIMESTAMP,
                        pmf = partner_responses.pmf  -- Preserve existing PMF value
                    RETURNING id
                """, (bid_id, partner, loi))
                
                partner_response_id = cur.fetchone()['id']

                # Only create audience responses for existing partner-LOI combinations
                partner_key = f"{partner}-{loi}"
                if partner_key in existing_partners:
                    for key, data in existing_data.items():
                        if (f"{partner}-{loi}" in key and 
                            data.get('audience_id') and 
                            data.get('country')):
                            
                            cur.execute("""
                                INSERT INTO partner_audience_responses 
                                (bid_id, partner_response_id, audience_id, country, 
                                 commitment, cpi, timeline_days, comments)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (bid_id, partner_response_id, audience_id, country) 
                                DO UPDATE SET 
                                    commitment = EXCLUDED.commitment,
                                    cpi = EXCLUDED.cpi,
                                    timeline_days = EXCLUDED.timeline_days,
                                    comments = EXCLUDED.comments
                            """, (
                                bid_id,
                                partner_response_id,
                                data['audience_id'],
                                data['country'],
                                data.get('commitment', 0),  # Default to 0 if NULL
                                data.get('cpi', 0),
                                data.get('timeline_days', 0),
                                data.get('comments', '')
                            ))

        conn.commit()
        return jsonify({"message": "Partner responses updated successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error updating partner responses: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/partners-lois', methods=['GET'])
def get_bid_partners_lois(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get partners and LOIs from the main bid table
        cur.execute("""
            SELECT partners, loi
            FROM bids
            WHERE id = %s
        """, (bid_id,))
        
        bid_data = cur.fetchone()
        if not bid_data:
            return jsonify({"error": "Bid not found"}), 404

        # Get the full list of partners and LOIs from the bid
        partners = bid_data.get('partners', [])
        lois = bid_data.get('loi', [])

        return jsonify({
            "partners": partners,
            "lois": lois
        })

    except Exception as e:
        print(f"Error fetching partners and LOIs: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<bid_id>/responses', methods=['GET'])
def get_bid_responses(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # First get ordered list of audience IDs
        cur.execute("""
            SELECT id 
            FROM bid_target_audiences 
            WHERE bid_id = %s 
            ORDER BY id
        """, (bid_id,))
        
        audience_ids = [row['id'] for row in cur.fetchall()]

        # First get all partner responses (including those without audience responses)
        # This ensures we get PMF values for all partner-LOI combinations
        cur.execute("""
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                pr.currency,
                pr.pmf,
                pr.status
            FROM partner_responses pr
            WHERE pr.bid_id = %s
        """, (bid_id,))
        
        partner_responses = cur.fetchall()

        # Initialize responses with basic data
        responses = {}
        settings = {}
        
        for pr in partner_responses:
            key = f"{pr['partner_id']}-{pr['loi']}"
            responses[key] = {
                'partner_id': pr['partner_id'],
                'loi': pr['loi'],
                'status': pr['status'] or 'draft',
                'currency': pr['currency'] or 'USD',
                'pmf': float(pr['pmf']) if pr['pmf'] is not None else 0,
                'audiences': {}
            }
            
            if pr['partner_id'] not in settings:
                settings[pr['partner_id']] = {
                    'currency': pr['currency'] or 'USD',
                    'pmf': float(pr['pmf']) if pr['pmf'] is not None else 0
                }

        # Now get audience responses
        cur.execute("""
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                par.audience_id,
                par.country,
                par.commitment,
                par.cpi,
                par.timeline_days,
                par.comments,
                bta.id as target_audience_id
            FROM partner_responses pr
            LEFT JOIN partner_audience_responses par ON pr.id = par.partner_response_id
            LEFT JOIN bid_target_audiences bta ON par.audience_id = bta.id
            WHERE pr.bid_id = %s
            ORDER BY bta.id
        """, (bid_id,))
        
        audience_rows = cur.fetchall()

        # Add audience responses to the initialized structure
        for row in audience_rows:
            if row['target_audience_id']:
                key = f"{row['partner_id']}-{row['loi']}"
                audience_index = audience_ids.index(row['target_audience_id'])
                audience_key = f"audience-{audience_index}"
                
                if audience_key not in responses[key]['audiences']:
                        responses[key]['audiences'][audience_key] = {
                            'timeline': row['timeline_days'] or 0,
                        'comments': row['comments'] or '',
                        }
                    
                if row['country']:
                        responses[key]['audiences'][audience_key][row['country']] = {
                            'commitment': row['commitment'] or 0,
                            'cpi': float(row['cpi']) if row['cpi'] is not None else 0
                        }

        return jsonify({
            'responses': responses,
            'settings': settings
        })

    except Exception as e:
        print(f"Error getting bid responses: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/invoice/<int:bid_id>/submit', methods=['POST', 'OPTIONS'])
def submit_invoice(bid_id):
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.status_code = 200
        return response
        
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First, get the actual bid_id from the bid_number
        cur.execute("SELECT id FROM bids WHERE bid_number = %s", (str(bid_id),))
        bid_row = cur.fetchone()
        if not bid_row:
            raise Exception(f"Bid with number {bid_id} not found")
        
        actual_bid_id = bid_row[0]

        # Update bid status to 'invoiced'
        cur.execute("""
            UPDATE bids 
            SET status = 'invoiced',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (actual_bid_id,))

        conn.commit()
        response = jsonify({"message": "Invoice submitted successfully"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        return response, 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error submitting invoice: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Add this function to add the field_close_date column
def add_field_close_date_column():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Add field_close_date column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                FROM information_schema.columns 
                WHERE table_name = 'partner_audience_responses' 
                AND column_name = 'field_close_date'
                ) THEN
                    ALTER TABLE partner_audience_responses
                ADD COLUMN field_close_date DATE;
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("Added field_close_date column")
        
    except Exception as e:
        print(f"Error adding field_close_date column: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def standardize_invoice_status():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Update any 'completed' or similar statuses to 'invoiced' where appropriate
        cur.execute("""
            UPDATE bids 
            SET status = 'invoiced'
            WHERE status IN ('completed', ' completed', 'Completed', ' Completed')
            AND id IN (
                SELECT DISTINCT bid_id 
                FROM partner_audience_responses 
                WHERE n_delivered IS NOT NULL
            )
        """)

        conn.commit()
        print("Invoice statuses standardized successfully")

    except Exception as e:
        print(f"Error standardizing invoice statuses: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Add a global OPTIONS route handler
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route('/api/bids/<bid_id>/partner-responses', methods=['PUT'])
def update_partner_responses(bid_id):
    try:
        if str(bid_id).startswith('temp_'):
            return jsonify({"message": "Partner responses saved in session"}), 200

        bid_id = int(bid_id)
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        data = request.json
        print("Received partner response data:", data)
        responses = data.get('responses', {})

        # Start transaction
        cur.execute("BEGIN")

        # First get the audience mapping
        cur.execute("""
            SELECT id, audience_name 
            FROM bid_target_audiences 
            WHERE bid_id = %s
            ORDER BY created_at
        """, (bid_id,))
        
        audience_mapping = {}
        for row in cur.fetchall():
            audience_mapping[f"audience-{row['id']}"] = row['id']
            
        print("Audience mapping:", audience_mapping)

        # For each response, update or insert
        for key, response in responses.items():
            partner_id = response.get('partner_id')
            loi = response.get('loi')
            
            # Check if partner response exists
            cur.execute("""
                SELECT id FROM partner_responses 
                WHERE bid_id = %s AND partner_id = %s AND loi = %s
            """, (bid_id, partner_id, loi))
            
            existing = cur.fetchone()
            
            if existing:
                partner_response_id = existing['id']
                # Update existing partner response
                cur.execute("""
                    UPDATE partner_responses 
                    SET status = %s, currency = %s, pmf = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    response.get('status', 'pending'),
                    response.get('currency', 'USD'),
                    response.get('pmf', 0),
                    partner_response_id
                ))
            else:
                # Insert new partner response
                cur.execute("""
                    INSERT INTO partner_responses 
                    (bid_id, partner_id, loi, status, currency, pmf, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id
                """, (
                    bid_id,
                    partner_id,
                    loi,
                    response.get('status', 'pending'),
                    response.get('currency', 'USD'),
                    response.get('pmf', 0)
                ))
                partner_response_id = cur.fetchone()['id']

            # Update audience responses
            audiences = response.get('audiences', {})
            for audience_key, audience_data in audiences.items():
                # Get the correct audience ID from mapping
                audience_id = audience_mapping.get(audience_key)
                if not audience_id:
                    print(f"Warning: No mapping found for {audience_key}")
                    continue

                # Get timeline and comments from audience data
                timeline = audience_data.get('timeline', 0)
                comments = audience_data.get('comments', '')
                
                # Process each country's data
                for country, country_data in audience_data.items():
                    # Skip non-country keys
                    if country in ['timeline', 'comments']:
                        continue

                    commitment = country_data.get('commitment', 0)
                    cpi = country_data.get('cpi', 0)

                    # Check if audience response exists
                    cur.execute("""
                        SELECT id FROM partner_audience_responses 
                        WHERE bid_id = %s AND partner_response_id = %s 
                        AND audience_id = %s AND country = %s
                    """, (bid_id, partner_response_id, audience_id, country))
                    
                    existing_response = cur.fetchone()

                    if existing_response:
                        # Update existing response
                        cur.execute("""
                            UPDATE partner_audience_responses 
                            SET commitment = %s,
                                cpi = %s,
                                timeline_days = %s,
                                comments = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            commitment,
                            cpi,
                            timeline,
                            comments,
                            existing_response['id']
                        ))
                    else:
                        # Insert new response
                        cur.execute("""
                            INSERT INTO partner_audience_responses 
                            (bid_id, partner_response_id, audience_id, country, 
                             commitment, cpi, timeline_days, comments, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (
                            bid_id,
                            partner_response_id,
                            audience_id,
                            country,
                            commitment,
                            cpi,
                            timeline,
                            comments
                        ))

        conn.commit()
        return jsonify({"message": "Partner responses updated successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error updating partner responses: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/partners/<int:partner_id>', methods=['PUT'])
def update_partner(partner_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        data = request.json
        print(f"Updating partner {partner_id} with data: {data}")
        
        # Update partner information
        cur.execute("""
            UPDATE partners
            SET partner_name = %s,
                contact_person = %s,
                contact_email = %s,
                contact_phone = %s,
                website = %s,
                company_address = %s,
                specialized = %s,
                geographic_coverage = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, partner_id, partner_name, contact_person, contact_email, 
                     contact_phone, website, company_address, specialized, 
                     geographic_coverage, created_at, updated_at
        """, (
            data.get('partner_name'),
            data.get('contact_person'),
            data.get('contact_email'),
            data.get('contact_phone'),
            data.get('website'),
            data.get('company_address'),
            data.get('specialized'),
            data.get('geographic_coverage'),
            partner_id
        ))
        
        updated_partner = cur.fetchone()
        conn.commit()
        
        if not updated_partner:
            return jsonify({"error": f"Partner with ID {partner_id} not found"}), 404
        
        return jsonify(updated_partner)
        
    except Exception as e:
        print(f"Error updating partner: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/partners/<int:partner_id>', methods=['DELETE'])
def delete_partner(partner_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First check if partner exists
        cur.execute("SELECT id FROM partners WHERE id = %s", (partner_id,))
        if not cur.fetchone():
            return jsonify({"error": f"Partner with ID {partner_id} not found"}), 404
        
        # Delete the partner
        cur.execute("DELETE FROM partners WHERE id = %s", (partner_id,))
        conn.commit()
        
        return jsonify({"message": "Partner deleted successfully"})
        
    except Exception as e:
        print(f"Error deleting partner: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/vms/<int:vm_id>', methods=['PUT'])
def update_vm(vm_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        data = request.json
        print(f"Updating VM {vm_id} with data: {data}")
        
        # Update VM information
        cur.execute("""
            UPDATE vendor_managers
            SET vm_id = %s,
                vm_name = %s,
                contact_person = %s,
                reporting_manager = %s,
                team = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at
        """, (
            data.get('vm_id'),
            data.get('vm_name'),
            data.get('contact_person'),
            data.get('reporting_manager'),
            data.get('team'),
            vm_id
        ))
        
        updated_vm = cur.fetchone()
        conn.commit()
        
        if not updated_vm:
            return jsonify({"error": f"VM with ID {vm_id} not found"}), 404
        
        return jsonify(updated_vm)
        
    except Exception as e:
        print(f"Error updating VM: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/vms/<int:vm_id>', methods=['DELETE'])
def delete_vm(vm_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First check if VM exists
        cur.execute("SELECT id FROM vendor_managers WHERE id = %s", (vm_id,))
        if not cur.fetchone():
            return jsonify({"error": f"VM with ID {vm_id} not found"}), 404
        
        # Delete the VM
        cur.execute("DELETE FROM vendor_managers WHERE id = %s", (vm_id,))
        conn.commit()
        
        return jsonify({"message": "VM deleted successfully"})
        
    except Exception as e:
        print(f"Error deleting VM: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Add this to your initialization code
if __name__ == '__main__':
    init_db()
    add_field_close_date_column()
    standardize_invoice_status()  # Add this line
    
@app.route('/api/sales/<int:sales_id>', methods=['PUT'])
def update_sales(sales_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        data = request.json
        print(f"Updating sales {sales_id} with data: {data}")
        
        # Update sales information
        cur.execute("""
            UPDATE sales
            SET sales_id = %s,
                sales_person = %s,
                contact_person = %s,
                reporting_manager = %s,
                region = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at
        """, (
            data.get('sales_id'),
            data.get('sales_person'),
            data.get('contact_person'),
            data.get('reporting_manager'),
            data.get('region'),
            sales_id
        ))
        
        updated_sales = cur.fetchone()
        conn.commit()
        
        if not updated_sales:
            return jsonify({"error": f"Sales with ID {sales_id} not found"}), 404
        
        return jsonify(updated_sales)
        
    except Exception as e:
        print(f"Error updating sales: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/sales/<int:sales_id>', methods=['DELETE'])
def delete_sales(sales_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First check if sales exists
        cur.execute("SELECT id FROM sales WHERE id = %s", (sales_id,))
        if not cur.fetchone():
            return jsonify({"error": f"Sales with ID {sales_id} not found"}), 404
        
        # Delete the sales
        cur.execute("DELETE FROM sales WHERE id = %s", (sales_id,))
        conn.commit()
        
        return jsonify({"message": "Sales deleted successfully"})
        
    except Exception as e:
        print(f"Error deleting sales: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/debug/routes', methods=['GET'])
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        # Get login data from request
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        print(f"Login attempt with email: {email}")
        
        # For demonstration purposes, you can add basic validation
        # In a real application, you would verify against a database
        if email == 'admin@example.com' and password == 'admin':
            # Return a success response with a token and user data
            user_data = {
                'id': 1,
                'email': email,
                'name': 'Admin User',
                'role': 'admin'
            }
            print(f"Login successful, returning user data: {user_data}")
            return jsonify({
                'token': 'sample-jwt-token',
                'user': user_data
            })
        else:
            print(f"Login failed for email: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Move app.run to the end after all routes are defined
if __name__ == '__main__':
    app.run(debug=True, port=5000)