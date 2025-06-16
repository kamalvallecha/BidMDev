import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from config import Config
import json
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from typing import List
from pydantic import BaseModel
from dataclasses import dataclass
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
from constants import ROLES_AND_PERMISSIONS
import uuid
import secrets
from flask_mail import Message, Mail
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# --- Custom JSON Encoder must be defined before app = Flask(__name__) ---
class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# Initialize Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
CORS(app,
     resources={
         r"/api/*": {
             "origins": ["*"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type", "Authorization"]
         }
     })

# Configure Flask-Mail with error handling
mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')

if not mail_username or not mail_password:
    print("Warning: Email credentials not found in environment variables")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kamalvallecha@gmail.com'
app.config['MAIL_PASSWORD'] = 'slcwiktxtfgfcpkg'
app.config['MAIL_DEFAULT_SENDER'] = 'kamal.vallecha@c5i.ai'
app.config['MAIL_SUPPRESS_SEND'] = False

# Initialize Flask-Mail
mail = Mail(app)

print(
    'Mail configuration:', {
        'username': mail_username,
        'server': app.config['MAIL_SERVER'],
        'port': app.config['MAIL_PORT'],
        'TLS': app.config['MAIL_USE_TLS']
    })

# Initialize the scheduler
scheduler = BackgroundScheduler()

ADMIN_NOTIFICATION_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL')

print('MAIL_USERNAME:', os.getenv('MAIL_USERNAME'))
print('ADMIN_NOTIFICATION_EMAIL:', os.getenv('ADMIN_NOTIFICATION_EMAIL'))


def check_expiring_links():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Find links expiring in the next 3 days
        cur.execute("""
            SELECT pl.*, p.contact_email, p.partner_name, b.bid_number, b.study_name
            FROM partner_links pl
            JOIN partners p ON p.id = pl.partner_id
            JOIN bids b ON b.id = pl.bid_id
            WHERE pl.expires_at BETWEEN NOW() AND NOW() + INTERVAL '3 days'
            AND pl.notification_sent = false
        """)

        expiring_links = cur.fetchall()

        for link in expiring_links:
            try:
                # Send notification email
                msg = Message('Your Partner Response Link is Expiring Soon',
                              sender=app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[link['contact_email']])

                msg.body = f"""
                Dear {link['partner_name']},

                Your access link for bid {link['bid_number']} ({link['study_name']}) will expire in 3 days.

                Current Link: {request.host_url}partner-response/{link['token']}
                Expiry Date: {link['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}

                Please complete your response before the link expires. If you need more time, please contact the bid manager.

                Best regards,
                Bid Management Team
                """

                mail.send(msg)

                # Mark notification as sent
                cur.execute(
                    """
                    UPDATE partner_links 
                    SET notification_sent = true 
                    WHERE id = %s
                """, (link['id'], ))

            except Exception as email_error:
                print(
                    f"Error sending expiration notification: {str(email_error)}"
                )

        conn.commit()

    except Exception as e:
        print(f"Error checking expiring links: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


# Schedule the task to run daily at midnight
scheduler.add_job(check_expiring_links,
                  CronTrigger(hour=0, minute=0),
                  id='check_expiring_links',
                  replace_existing=True)

# Start the scheduler when the app starts
scheduler.start()


def get_db_connection():
    try:
        # Use Replit's DATABASE_URL if available, otherwise fall back to individual env vars
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        else:
            # Fallback to individual environment variables
            return psycopg2.connect(
                host=os.getenv('PGHOST', '127.0.0.1'),
                database=os.getenv('PGDATABASE', 'BidM'),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD', 'root123'),
                port=os.getenv('PGPORT', '5432')
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
                'id':
                user[0],
                'email':
                user[1],
                'name':
                user[2],
                'employee_id':
                user[3],
                'role':
                user[4],
                'team':
                user[5],
                'created_at':
                user[6].strftime('%Y-%m-%d %H:%M:%S') if user[6] else None,
                'updated_at':
                user[7].strftime('%Y-%m-%d %H:%M:%S') if user[7] else None
            } for user in users])

        elif request.method == 'POST':
            data = request.json
            password_hash = generate_password_hash(data['password'],
                                                   method='pbkdf2:sha256')

            # Validate required fields
            required_fields = ['email', 'name', 'password', 'role', 'team']
            for field in required_fields:
                if field not in data:
                    return jsonify(
                        {"error": f"Missing required field: {field}"}), 400

            cur.execute(
                """
                INSERT INTO users (email, name, employee_id, password_hash, role, team)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (data['email'], data['name'], data.get('employee_id'),
                  password_hash, data['role'], data['team']))

            new_user_id = cur.fetchone()[0]
            conn.commit()

            return jsonify({
                'id': new_user_id,
                'message': 'User created successfully'
            }), 201

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
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM vendor_managers ORDER BY id')
        vms = cur.fetchall()
        return jsonify(vms)
    except Exception as e:
        print(f"Error in get_vms: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/vms', methods=['POST'])
def create_vm():
    conn = None
    cur = None
    try:
        data = request.json
        print("Received VM data:", data)  # Debug log

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Clean and validate input data
        vm_data = {
            'vm_id': str(data.get('vm_id', '')).strip(),
            'vm_name': str(data.get('vm_name', '')).strip(),
            'contact_person': str(data.get('contact_person', '')).strip(),
            'reporting_manager': str(data.get('reporting_manager',
                                              '')).strip(),
            'team': str(data.get('team', '')).strip()
        }

        # Check for empty required fields
        for field, value in vm_data.items():
            if not value:
                return jsonify({"error":
                                f"Field {field} cannot be empty"}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check if VM ID already exists
        cur.execute('SELECT id FROM vendor_managers WHERE vm_id = %s',
                    (vm_data['vm_id'], ))
        if cur.fetchone():
            return jsonify({"error": "VM ID already exists"}), 400

        # Insert new VM
        cur.execute(
            """
            INSERT INTO vendor_managers (
                vm_id, vm_name, contact_person,
                reporting_manager, team, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, vm_id, vm_name, contact_person, reporting_manager, team
            """,
            (vm_data['vm_id'], vm_data['vm_name'], vm_data['contact_person'],
             vm_data['reporting_manager'], vm_data['team']))

        new_vm = cur.fetchone()
        conn.commit()

        return jsonify({"message": "VM created successfully", **new_vm}), 201

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
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM sales ORDER BY id')
        sales = cur.fetchall()
        return jsonify(sales)
    except Exception as e:
        print(f"Error in get_sales: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/sales', methods=['POST'])
def create_sale():
    try:
        data = request.json
        print("Received sales data:", data)

        required_fields = [
            'sales_id', 'sales_person', 'contact_person', 'reporting_manager',
            'region'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error":
                                f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if sales ID already exists
        cur.execute('SELECT id FROM sales WHERE sales_id = %s',
                    (data['sales_id'], ))

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
        cur.execute(
            '''
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
        ''', (data['sales_id'], data['sales_person'], data['contact_person'],
              data['reporting_manager'], data['region'].lower()))

        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'id': new_id,
            'message': 'Sales record created successfully'
        }), 201

    except Exception as e:
        print(f"Error in create_sale: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


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

        cur.execute(
            """
            INSERT INTO partners (
                partner_id, partner_name, contact_person, 
                contact_email, contact_phone, website, 
                company_address, specialized, geographic_coverage
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """,
            (
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
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM clients ORDER BY id')
        clients = cur.fetchall()
        return jsonify(clients)
    except Exception as e:
        print(f"Error in get_clients: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.json
        print("Received client data:", data)

        required_fields = [
            'client_id', 'client_name', 'contact_person', 'email', 'phone',
            'country'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error":
                                f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if client already exists
        cur.execute(
            'SELECT id FROM clients WHERE client_id = %s OR email = %s',
            (data['client_id'], data['email']))
        if cur.fetchone():
            return jsonify({"error": "Client ID or email already exists"}), 400

        # Insert new client
        cur.execute(
            '''
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
        ''', (data['client_id'], data['client_name'], data['contact_person'],
              data['email'], data['phone'], data['country']))

        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'id': new_id,
            'message': 'Client created successfully'
        }), 201

    except Exception as e:
        print(f"Error in create_client: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.json
        print(f"Updating client {client_id} with data:", data)

        required_fields = [
            'client_id', 'client_name', 'contact_person', 'email', 'phone',
            'country'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error":
                                f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if client exists
        cur.execute('SELECT id FROM clients WHERE id = %s', (client_id, ))
        if not cur.fetchone():
            return jsonify({"error":
                            f"Client with ID {client_id} not found"}), 404

        # Check if email or client_id already exists for different client
        cur.execute(
            'SELECT id FROM clients WHERE (client_id = %s OR email = %s) AND id != %s',
            (data['client_id'], data['email'], client_id))
        if cur.fetchone():
            return jsonify({
                "error":
                "Client ID or email already exists for another client"
            }), 400

        # Update client
        cur.execute(
            '''
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
        ''', (data['client_id'], data['client_name'], data['contact_person'],
              data['email'], data['phone'], data['country'], client_id))

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
        cur.execute("SELECT id FROM clients WHERE id = %s", (client_id, ))
        if not cur.fetchone():
            return jsonify({"error":
                            f"Client with ID {client_id} not found"}), 404

        # Delete the client
        cur.execute("DELETE FROM clients WHERE id = %s", (client_id, ))
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
        cur.execute('''
            SELECT 
                b.id,
                b.bid_number,
                b.study_name,
                b.bid_date,
                b.status,
                c.client_name AS client_name,
                b.project_requirement,
                b.methodology
            FROM bids b
            LEFT JOIN clients c ON b.client = c.id
            ORDER BY b.id DESC
        ''')
        bids = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(bids)
    except Exception as e:
        print(f"Error in get_bids: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/bids', methods=['POST'])
def create_bid():
    try:
        data = request.json
        print("Received bid data:", data)

        required_fields = [
            'bid_number', 'bid_date', 'study_name', 'methodology',
            'sales_contact', 'vm_contact', 'client', 'project_requirement',
            'countries', 'target_audiences'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error":
                                f"Missing required field: {field}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert new bid record
        cur.execute(
            '''
            INSERT INTO bids (
                bid_number,
                bid_date,
                study_name,
                methodology,
                sales_contact,
                vm_contact,
                client,
                project_requirement,
                status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (data['bid_number'], data['bid_date'], data['study_name'],
              data['methodology'], data['sales_contact'], data['vm_contact'],
              data['client'], data['project_requirement']))

        bid_id = cur.fetchone()[0]

        # Insert target audiences
        for audience in data['target_audiences']:
            cur.execute(
                '''
                INSERT INTO bid_target_audiences (
                    bid_id,
                    audience_name,
                    ta_category,
                    broader_category,
                    exact_ta_definition,
                    mode,
                    sample_required,
                    ir,
                    comments,
                    is_best_efforts
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''',
                (bid_id, audience['name'], audience['ta_category'],
                 audience['broader_category'], audience['exact_ta_definition'],
                 audience['mode'], audience['sample_required'], audience['ir'],
                 audience.get('comments',
                              ''), audience.get('is_best_efforts', False)))
            audience_id = cur.fetchone()[0]

            # Insert country samples for this audience
            for country, sample_data in audience.get('country_samples',
                                                     {}).items():
                cur.execute(
                    '''
                    INSERT INTO bid_audience_countries (
                        bid_id,
                        audience_id,
                        country,
                        sample_size,
                        is_best_efforts
                    ) VALUES (%s, %s, %s, %s, %s)
                ''', (bid_id, audience_id, country, sample_data['sample_size'],
                      sample_data['is_best_efforts']))

        conn.commit()
        return jsonify({
            'bid_id': bid_id,
            'message': 'Bid created successfully'
        }), 201

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error in create_bid: {str(e)}")
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
        cur.execute(
            """
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
        """, (bid_id, ))

        bid = cur.fetchone()
        if not bid:
            return jsonify({"error": "Bid not found"}), 404

        if bid['bid_date']:
            bid['bid_date'] = bid['bid_date'].strftime('%Y-%m-%d')

        # Get target audiences with sample sizes - ordered by creation order
        cur.execute(
            """
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
                bta.is_best_efforts,
                bac.country,
                bac.sample_size,
                bac.is_best_efforts as country_is_best_efforts
            FROM bid_target_audiences bta
            LEFT JOIN bid_audience_countries bac ON bta.id = bac.audience_id
            WHERE bta.bid_id = %s
            ORDER BY bta.id, bac.country
        """, (bid_id, ))

        rows = cur.fetchall()
        print(f"=== BACKEND GET_BID DEBUG for bid_id {bid_id} ===")
        print(f"Raw query result count: {len(rows)}")
        
        # Log all audience IDs found in order
        audience_ids_found = []
        for row in rows:
            if row['id'] not in audience_ids_found:
                audience_ids_found.append(row['id'])
                print(f"Found audience ID {row['id']} with name '{row['name']}'")

        # Format target audiences with their sample sizes
        target_audiences = {}
        for row in rows:
            audience_id = row['id']
            if audience_id not in target_audiences:
                target_audiences[audience_id] = {
                    'id': row['id'],
                    'uniqueId': f"audience-{audience_id}",
                    'name': row['name'],
                    'ta_category': row['ta_category'],
                    'broader_category': row['broader_category'],
                    'exact_ta_definition': row['exact_ta_definition'],
                    'mode': row['mode'],
                    'sample_required': row['sample_required'],
                    'ir': row['ir'],
                    'comments': row['comments'],
                    'is_best_efforts': row['is_best_efforts'],
                    'country_samples': {}
                }
                print(f"Created audience object for ID {audience_id}: {row['name']}")
            if row['country']:
                target_audiences[audience_id]['country_samples'][row['country']] = {
                    'sample_size': row['sample_size'],
                    'is_best_efforts': row['country_is_best_efforts']
                }
                print(f"Added country sample: audience {audience_id}, country {row['country']}, size {row['sample_size']}")

        # Sort audiences by ID to maintain consistent database order, then renumber sequentially
        sorted_audiences = sorted(target_audiences.values(), key=lambda x: x['id'])
        
        # Renumber audiences sequentially based on their sorted database ID order
        for index, audience in enumerate(sorted_audiences):
            audience['name'] = f"Audience - {index + 1}"
            audience['uniqueId'] = f"audience-{index}"
        
        print(f"Final sorted audience order after renumbering: {[f'ID:{a['id']}-{a['name']}' for a in sorted_audiences]}")
        print(f"=== END BACKEND DEBUG ===\n")

        # Get partners and LOIs with full partner details
        cur.execute(
            """
            SELECT DISTINCT 
                pr.partner_id,
                p.partner_name,
                pr.loi
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = %s
        """, (bid_id, ))

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

        lois = list(set([r['loi'] for r in partner_lois])) if partner_lois else []

        response = {
            **bid, 
            'target_audiences': sorted_audiences,
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

        # Use get_json() with force=True to ensure proper parsing
        data = request.get_json(force=True)
        
        # Debug logging
        print("Raw request data:", data)
        print("Request content type:", request.content_type)
        print("Request headers:", dict(request.headers))

        # Start transaction
        cur.execute("BEGIN")

        # 1. Update main bid details
        cur.execute(
            """
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
        """, (data['bid_date'], data['study_name'], data['methodology'],
              data['sales_contact'], data['vm_contact'], data['client'],
              data['project_requirement'], bid_id))
        print("Updated main bid details")

        # 2. Get existing audience IDs
        cur.execute(
            """
            SELECT id FROM bid_target_audiences 
            WHERE bid_id = %s
            ORDER BY id
        """, (bid_id, ))
        existing_audience_ids = set(row[0] for row in cur.fetchall())
        print("Existing audience IDs:", existing_audience_ids)

        # 3. Handle deleted audiences BEFORE updating/inserting new ones
        deleted_audience_ids = data.get('deleted_audience_ids', [])
        print("Received deleted_audience_ids:", deleted_audience_ids)
        print("Type of deleted_audience_ids:", type(deleted_audience_ids))
        print("Length of deleted_audience_ids:", len(deleted_audience_ids))
        print("Full request data keys:", list(data.keys()))
        print("Raw deleted_audience_ids from request:", repr(data.get('deleted_audience_ids')))
        
        # Additional debugging - check if field exists with different casing or format
        for key in data.keys():
            if 'deleted' in key.lower() or 'audience' in key.lower():
                print(f"Found related key: {key} = {data[key]}")
        
        # Force deleted_audience_ids to be a list if it exists but is None
        if 'deleted_audience_ids' in data and data['deleted_audience_ids'] is None:
            deleted_audience_ids = []
            print("Converted None to empty list")
        
        # Auto-detect deleted audiences: if an existing audience is not in the new target_audiences, it should be deleted
        received_audience_ids = set()
        for audience in data['target_audiences']:
            if audience.get('id') and isinstance(audience.get('id'), int):
                received_audience_ids.add(audience['id'])
        
        print(f"Received audience IDs: {received_audience_ids}")
        print(f"Existing audience IDs: {existing_audience_ids}")
        
        auto_deleted_ids = existing_audience_ids - received_audience_ids
        if auto_deleted_ids:
            print(f"Auto-detected deleted audiences: {auto_deleted_ids}")
            deleted_audience_ids.extend(list(auto_deleted_ids))
            print(f"Final deleted_audience_ids after auto-detection: {deleted_audience_ids}")
        else:
            print("No audiences auto-detected for deletion")
        
        if deleted_audience_ids:
            print(f"Processing deletion of {len(deleted_audience_ids)} audiences: {deleted_audience_ids}")
            
            # Delete partner audience responses for deleted audiences first
            cur.execute(
                """
                DELETE FROM partner_audience_responses 
                WHERE audience_id = ANY(%s) AND bid_id = %s
            """, (deleted_audience_ids, bid_id))
            deleted_par_count = cur.rowcount
            print(f"Deleted {deleted_par_count} partner audience responses")
            
            # Delete country samples for deleted audiences
            cur.execute(
                """
                DELETE FROM bid_audience_countries 
                WHERE audience_id = ANY(%s) AND bid_id = %s
            """, (deleted_audience_ids, bid_id))
            deleted_bac_count = cur.rowcount
            print(f"Deleted {deleted_bac_count} bid audience countries")
            
            # Delete the audiences themselves
            cur.execute(
                """
                DELETE FROM bid_target_audiences 
                WHERE id = ANY(%s) AND bid_id = %s
            """, (deleted_audience_ids, bid_id))
            deleted_bta_count = cur.rowcount
            print(f"Deleted {deleted_bta_count} bid target audiences")
            
            print(f"Successfully deleted audiences and related data: {deleted_audience_ids}")
        else:
            print("No audiences to delete")

        # 4. Update or insert target audiences (by ID, not index)
        for audience in data['target_audiences']:
            audience_id = audience.get('id')
            if audience_id and audience_id in existing_audience_ids:
                # Update existing audience by ID
                cur.execute(
                    """
                    UPDATE bid_target_audiences SET 
                    audience_name = %s,
                    ta_category = %s,
                    broader_category = %s,
                    exact_ta_definition = %s,
                    mode = %s,
                    sample_required = %s,
                    ir = %s,
                    comments = %s,
                    is_best_efforts = %s,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND bid_id = %s
                """,
                    (audience['name'], audience['ta_category'],
                     audience['broader_category'],
                     audience['exact_ta_definition'], audience['mode'],
                     audience['sample_required'], audience['ir'],
                     audience.get('comments', ''), audience.get('is_best_efforts', False), audience_id, bid_id))
                print(f"Updated audience ID: {audience_id}")
            else:
                # Insert new audience
                cur.execute(
                    """
                    INSERT INTO bid_target_audiences (
                        bid_id,
                        audience_name,
                        ta_category,
                        broader_category,
                        exact_ta_definition,
                        mode,
                        sample_required,
                        ir,
                        comments,
                        is_best_efforts
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (bid_id, audience['name'], audience['ta_category'],
                     audience['broader_category'],
                     audience['exact_ta_definition'], audience['mode'],
                     audience['sample_required'], audience['ir'],
                     audience.get('comments', ''), audience.get('is_best_efforts', False)))
                audience_id = cur.fetchone()[0]
                print(f"Inserted new audience ID: {audience_id}")

            # Update or insert country samples
            if 'country_samples' in audience:
                # First, remove old country samples for this audience
                cur.execute(
                    """
                    DELETE FROM bid_audience_countries 
                    WHERE audience_id = %s
                """, (audience_id, ))
                print(
                    f"Deleted old country samples for audience ID: {audience_id}")

                # Then insert new country samples
                for country, sample_data in audience['country_samples'].items():
                    try:
                        print(f"Inserting country {country} with sample data {sample_data}")
                        if isinstance(sample_data, dict):
                            sample_size = sample_data.get('sample_size', 0)
                            is_best_efforts = sample_data.get('is_best_efforts', False)
                        else:
                            sample_size = sample_data
                            is_best_efforts = sample_size == 0 and audience.get('is_best_efforts', False)
                        cur.execute(
                            """
                            INSERT INTO bid_audience_countries (
                                bid_id, audience_id, country, sample_size, is_best_efforts
                            ) VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (bid_id, audience_id, country) DO UPDATE SET
                                sample_size = EXCLUDED.sample_size,
                                is_best_efforts = EXCLUDED.is_best_efforts
                            """,
                            (bid_id, audience_id, country, int(sample_size), is_best_efforts)
                        )
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
            cur.execute(
                """
                SELECT bta.id as audience_id, bac.country
                FROM bid_target_audiences bta
                JOIN bid_audience_countries bac ON bta.id = bac.audience_id
                WHERE bta.bid_id = %s
            """, (bid_id, ))

            audience_countries = cur.fetchall()
            print(f"Found audience_countries: {audience_countries}")

            # Update partner responses
            for partner in partners:
                for loi in lois:
                    print(f"Processing partner {partner}, LOI {loi}")
                    # Create or update partner_response
                    try:
                        # Check if partner response exists first
                        cur.execute(
                            """
                            SELECT id FROM partner_responses 
                            WHERE bid_id = %s AND partner_id = %s AND loi = %s
                        """, (bid_id, partner, loi))

                        existing_response = cur.fetchone()

                        if existing_response:
                            # Use existing response ID
                            partner_response_id = existing_response[0]
                            print(
                                f"Using existing partner_response_id: {partner_response_id}"
                            )
                            # Keep existing PMF and currency values when updating
                            cur.execute(
                                """
                                SELECT pmf, currency 
                                FROM partner_responses 
                                WHERE id = %s
                            """, (partner_response_id, ))
                            existing_values = cur.fetchone()

                            # Update timestamp but preserve PMF and currency
                            cur.execute(
                                """
                                UPDATE partner_responses 
                                SET updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (partner_response_id, ))
                        else:
                            # Create new response
                            cur.execute(
                                """
                                INSERT INTO partner_responses 
                                (bid_id, partner_id, loi, status, currency, pmf, created_at)
                                VALUES (%s, %s, %s, 'draft', 'USD', 0, CURRENT_TIMESTAMP)
                                RETURNING id
                            """, (bid_id, partner, loi))

                            result = cur.fetchone()
                            partner_response_id = result[0]
                            print(
                                f"Created partner_response_id: {partner_response_id}"
                            )

                        # Create audience responses with 0 commitment (not NULL)
                        for ac in audience_countries:
                            # Check if record already exists
                            cur.execute(
                                """
                                SELECT 1 FROM partner_audience_responses 
                                WHERE bid_id = %s AND partner_response_id = %s 
                                AND audience_id = %s AND country = %s
                            """, (bid_id, partner_response_id, ac[0], ac[1]))

                            if not cur.fetchone():
                                # Only insert if doesn't exist
                                try:
                                    print(
                                        f"Inserting partner_audience_response for audience {ac[0]}, country {ac[1]}"
                                    )
                                    cur.execute(
                                        """
                                        INSERT INTO partner_audience_responses 
                                        (bid_id, partner_response_id, audience_id, country, 

                                         commitment, cpi, timeline_days, comments, initial_cost)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """,
                                        (
                                            bid_id,
                                            partner_response_id,
                                            ac[0],  # audience_id
                                            ac[1],  # country
                                            0,  # default commitment
                                            0,  # default cpi
                                            0,  # default timeline_days
                                            '',  # empty comments
                                            0  # initial_cost will be updated when n_delivered is set
                                        ))
                                    print(
                                        f"Successfully inserted partner_audience_response"
                                    )
                                except Exception as par_error:
                                    print(
                                        f"Error inserting partner_audience_response: {str(par_error)}"
                                    )
                                    raise
                    except Exception as partner_error:
                        print(
                            f"Error processing partner {partner}, LOI {loi}: {str(partner_error)}"
                        )
                        raise

        # Deleted audiences were already handled above in step 3

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
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get all partner responses with their audience data
        cur.execute(
            """
            WITH audience_responses AS (
                SELECT 
                    pr.id as response_id,
                    pr.partner_id,
                    pr.loi,
                    pr.status,
                    pr.currency,
                    pr.pmf,
                    par.audience_id,
                    par.id as audience_response_id,
                    par.country,
                    par.commitment,
                    par.commitment_type,
                    par.is_best_efforts,
                    par.cpi,
                    par.timeline_days,
                    par.comments,
                    par.n_delivered,
                    par.quality_rejects,
                    par.final_loi,
                    par.final_ir,
                    par.final_timeline,
                    par.final_cpi,
                    par.communication,
                    par.engagement,
                    par.problem_solving
                FROM partner_responses pr
                LEFT JOIN partner_audience_responses par ON par.partner_response_id = pr.id
                WHERE pr.bid_id = %s
            )
            SELECT * FROM audience_responses
        """, (bid_id, ))

        rows = cur.fetchall()

        # Structure the response data
        responses = {}
        settings = {}

        for row in rows:
            key = f"{row['partner_id']}-{row['loi']}"

            # Initialize response if not exists
            if key not in responses:
                responses[key] = {
                    'partner_id': row['partner_id'],
                    'loi': row['loi'],
                    'status': row['status'],
                    'currency': row['currency'],
                    'pmf': float(row['pmf']) if row['pmf'] is not None else 0,
                    'audiences': {}
                }

                # Store partner settings
                if row['partner_id'] not in settings:
                    settings[row['partner_id']] = {
                        'currency': row['currency'],
                        'pmf':
                        float(row['pmf']) if row['pmf'] is not None else 0
                    }

            # If there's audience data, add it
            if row['audience_response_id']:
                audience_id = str(row['audience_id'])

                if audience_id not in responses[key]['audiences']:
                    responses[key]['audiences'][audience_id] = {
                        'timeline':
                        float(row['timeline_days'])
                        if row['timeline_days'] is not None else 0,
                        'comments':
                        row['comments'] or '',
                    }

                country = row['country']
                if country:
                    responses[key]['audiences'][audience_id][country] = {
                        'commitment':
                        float(row['commitment'])
                        if row['commitment'] is not None else 0,
                        'commitment_type':
                        row['commitment_type'] or 'fixed',
                        'is_best_efforts':
                        row['is_best_efforts'] or False,
                        'cpi':
                        float(row['cpi']) if row['cpi'] is not None else 0,
                        'n_delivered':
                        row['n_delivered'] or 0,
                        'quality_rejects':
                        row['quality_rejects'] or 0,
                        'final_loi':
                        float(row['final_loi'])
                        if row['final_loi'] is not None else None,
                        'final_ir':
                        float(row['final_ir'])
                        if row['final_ir'] is not None else None,
                        'final_timeline':
                        row['final_timeline'],
                        'final_cpi':
                        float(row['final_cpi'])
                        if row['final_cpi'] is not None else None,
                        'communication':
                        row['communication'],
                        'engagement':
                        row['engagement'],
                        'problem_solving':
                        row['problem_solving']
                    }

        return jsonify({'responses': responses, 'settings': settings})

    except Exception as e:
        print(f"Error getting bid: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
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

        cur.execute(
            """
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
        cur.execute(
            """
            UPDATE bids 
            SET status = 'closure'
            WHERE bid_number = %s
            RETURNING id, bid_number, status
        """, (bid_number, ))

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
        cur.execute(
            """
            SELECT DISTINCT p.id, p.partner_name
            FROM partners p
            JOIN partner_responses pr ON p.id = pr.partner_id
            WHERE pr.bid_id = %s
            ORDER BY p.partner_name
        """, (bid_id, ))
        partners = cur.fetchall()
        print(f"Found partners: {partners}")  # Debug log

        # Get LOI options
        cur.execute(
            """
            SELECT DISTINCT loi
            FROM partner_responses
            WHERE bid_id = %s
            ORDER BY loi
        """, (bid_id, ))
        loi_options = [{'loi': row['loi']} for row in cur.fetchall()]
        print(f"Found LOI options: {loi_options}")  # Debug log

        # Get audiences with their countries and responses
        cur.execute(
            """
            SELECT 
                bta.id,
                bta.audience_name,
                bta.ta_category,
                bta.broader_category,
                bta.mode,
                bta.ir,
                bta.is_best_efforts as audience_is_best_efforts,
                bac.country,
                bac.sample_size,
                bac.is_best_efforts as country_is_best_efforts,
                pr.partner_id,
                pr.loi,
                par.commitment,
                par.commitment_type,
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
        """, (bid_id, ))
        rows = cur.fetchall()
        print(f"Found {len(rows)} audience rows")  # Debug log

        # Structure audiences data
        audiences = []
        current_audience = None
        current_countries = []

        for row in rows:
            if not current_audience or current_audience['id'] != row['id']:
                if current_audience:
                    current_audience['countries'] = current_countries
                    audiences.append(current_audience)
                    current_countries = []

                current_audience = {
                    'id': row['id'],
                    'audience_name': row['audience_name'],
                    'ta_category': row['ta_category'],
                    'broader_category': row['broader_category'],
                    'mode': row['mode'],
                    'ir': row['ir'],
                    'is_best_efforts': row['audience_is_best_efforts'],
                    'countries': []
                }

            if row['country']:
                country_data = {
                    'country': row['country'],
                    'sample_size': row['sample_size'],
                    'is_best_efforts': row['country_is_best_efforts']
                }
                current_countries.append(country_data)

        if current_audience:
            current_audience['countries'] = current_countries
            audiences.append(current_audience)

        # Get responses separately
        responses = []
        for row in rows:
            if row['partner_id'] and row['loi']:
                responses.append({
                    'partner_id':
                    row['partner_id'],
                    'audience_id':
                    row['id'],
                    'country':
                    row['country'],
                    'loi':
                    row['loi'],
                    'commitment':
                    row['commitment'] or 0,
                    'commitment_type':
                    row['commitment_type']
                    if 'commitment_type' in row else 'fixed',
                    'cpi':
                    float(row['cpi']) if row['cpi'] is not None else 0,
                    'allocation':
                    row['allocation'] or 0
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
            cur.execute(
                """
                SELECT 
                    bta.id,
                    bta.audience_name,
                    bta.ta_category,
                    bac.country,
                    bac.sample_size as required,
                    bac.is_best_efforts as country_is_best_efforts,
                    pr.partner_id,
                    pr.loi,
                    par.commitment,
                    par.commitment_type,
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
            """, (bid_id, ))

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
                        'is_best_efforts': row['country_is_best_efforts'],
                        'partners': {}
                    }

                if row['partner_id'] and row['loi']:
                    partner_key = f"{row['partner_id']}-{row['loi']}"
                    audiences[audience_id]['countries'][country]['partners'][
                        partner_key] = {
                            'commitment': row['commitment'] or 0,
                            'is_best_efforts': row['country_is_best_efforts'],
                            'commitment_type': row['commitment_type']
                            or 'fixed',
                            'cpi':
                            float(row['cpi']) if row['cpi'] is not None else 0,
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
            cur.execute(
                """
                SELECT id FROM partner_responses 
                WHERE bid_id = %s AND partner_id = %s AND loi = %s
            """, (bid_id, data['partner_id'], data['loi']))

            response = cur.fetchone()
            if response:
                response_id = response[0]

                # Update allocation without updated_at
                cur.execute(
                    """
                    UPDATE partner_audience_responses 
                    SET allocation = %s
                    WHERE partner_response_id = %s 
                    AND audience_id = %s 
                    AND country = %s
                    RETURNING id
                """, (data['allocation'], response_id, data['audience_id'],
                      data['country']))

                updated_id = cur.fetchone()[0]
                conn.commit()
                return jsonify({
                    'id': updated_id,
                    'message': 'Allocation updated successfully'
                })
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

        # Modified query to correctly calculate total N-delivered
        cur.execute("""
            WITH metrics AS (
                SELECT 
                    pr.bid_id,
                    SUM(COALESCE(par.n_delivered, 0)) as total_delivered,
                    SUM(COALESCE(par.quality_rejects, 0)) as total_rejects,
                    AVG(COALESCE(par.final_loi, 0)) as avg_loi,
                    AVG(COALESCE(par.final_ir, 0)) as avg_ir
                FROM partner_responses pr
                JOIN partner_audience_responses par ON par.partner_response_id = pr.id
                WHERE par.allocation > 0
                GROUP BY pr.bid_id
            )
            SELECT DISTINCT ON (b.id)
                b.id,
                bpo.po_number,
                b.bid_number,
                b.study_name,
                c.client_name,
                COALESCE(m.total_delivered, 0) as total_delivered,
                COALESCE(m.total_rejects, 0) as quality_rejects,
                ROUND(COALESCE(m.avg_loi, 0)::numeric, 2) as avg_loi,
                ROUND(COALESCE(m.avg_ir, 0)::numeric, 2) as avg_ir,
                b.status
            FROM bids b
            LEFT JOIN bid_po_numbers bpo ON b.id = bpo.bid_id
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN metrics m ON b.id = m.bid_id
            WHERE b.status = 'closure'
            ORDER BY b.id, b.updated_at DESC
        """)

        bids = cur.fetchall()
        return jsonify(bids)

    except Exception as e:
        print(f"Error fetching closure bids: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/bids/closure/<int:bid_id>', methods=['GET'])
def get_closure_bid_details(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get unique partner-LOI combinations with their allocation status
        cur.execute(
            """
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
        """, (bid_id, ))

        partners_result = cur.fetchall()

        # Get audience details with metrics - Modified to handle new countries
        cur.execute(
            """
            WITH partner_metrics AS (
                SELECT 
                    par.audience_id,
                    par.country,
                    par.commitment as required,
                    par.commitment_type,
                    par.allocation,
                    COALESCE(par.n_delivered, 0) as n_delivered,  -- Set NULL to 0
                    par.final_loi,
                    par.final_ir,
                    par.final_timeline,
                    par.quality_rejects,
                    par.communication as communication,
                    par.engagement as engagement,
                    par.problem_solving as problem_solving,
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
                COALESCE(pm.commitment_type, 'fixed') as commitment_type,
                COALESCE(pm.allocation, 0) as allocation,
                COALESCE(pm.n_delivered, 0) as n_delivered,  -- Set NULL to 0
                pm.final_loi,
                pm.final_ir,
                pm.final_timeline,
                pm.quality_rejects,
                pm.communication,
                pm.engagement,
                pm.problem_solving,
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
        response_data = {'partners': {}, 'audiences': {}}

        # Process partners with allocation info
        for partner in partners_result:
            if partner['partner_name'] not in response_data['partners']:
                response_data['partners'][partner['partner_name']] = {
                    'id': partner['partner_id'],
                    'lois': [],
                    'has_allocation': {}
                }
            response_data['partners'][partner['partner_name']]['lois'].append(
                partner['loi'])
            response_data['partners'][partner['partner_name']][
                'has_allocation'][partner['loi']] = partner['has_allocation']

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
            if row['country'] not in response_data['audiences'][audience_id][
                    'countries']:
                response_data['audiences'][audience_id]['countries'][
                    row['country']] = {
                        'required':
                        'BE/Max' if row['commitment_type'] == 'be_max' else
                        row['required'],
                        'allocation':
                        row['allocation'],
                        'delivered':
                        0  # Set to 0 for new countries
                    }

            # Add metrics data only if we have partner info
            if row['partner_name'] and row['loi']:
                partner_key = f"{row['partner_name']}_{row['loi']}"
                if partner_key not in response_data['audiences'][audience_id][
                        'metrics']:
                    response_data['audiences'][audience_id]['metrics'][
                        partner_key] = {
                            'finalLOI': row['final_loi'],
                            'finalIR': row['final_ir'],
                            'finalTimeline': row['final_timeline'],
                            'qualityRejects': row['quality_rejects'],
                            'communication': row['communication'],
                            'engagement': row['engagement'],
                            'problemSolving': row['problem_solving'],
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

        print(f"Fetching data for bid {bid_id}, partner {partner}, LOI {loi}"
              )  # Debug log

        # Modified query to only get records where allocation > 0
        cur.execute(
            """
            WITH valid_responses AS (
                SELECT 
                    bta.id,
                    bta.audience_name as category,
                    bta.ta_category,
                    bta.broader_category,
                    bta.mode,
                    bta.ir,
                    par.country as country_name,
                    par.commitment as required,
                    par.commitment_type,
                    par.allocation,
                    par.n_delivered as delivered,
                    par.field_close_date,
                    pr.id as partner_response_id,
                    par.final_loi as "finalLOI",
                    par.final_ir as "finalIR",
                    par.final_timeline as "finalTimeline",
                    par.quality_rejects as "qualityRejects",
                    par.communication as "communication",
                    par.engagement as "engagement",
                    par.problem_solving as "problemSolving",
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
                    'id':
                    audience_id,
                    'category':
                    row['category'],
                    'ta_category':
                    row['ta_category'],
                    'broader_category':
                    row['broader_category'],
                    'mode':
                    row['mode'],
                    'ir':
                    row['ir'],
                    'field_close_date':
                    row['field_close_date'].isoformat()
                    if row['field_close_date'] else None,
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
                    'name':
                    row['country_name'],
                    'required':
                    'BE/Max'
                    if row['commitment_type'] == 'be_max' else row['required'],
                    'allocation':
                    row['allocation'],
                    'delivered':
                    row['delivered']
                })

        # Filter out audiences with no countries (all had allocation = 0)
        result = [
            audience for audience in audiences.values()
            if audience['countries']
        ]
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
        cur.execute(
            """
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
                if len(parts) >= 4 and parts[2] == partner and int(
                        parts[3]) == int(loi):
                    audience_id = parts[1]
                    metrics = value

                    # Convert empty strings to None for numeric fields
                    final_loi = int(metrics.get('finalLOI')) if metrics.get(
                        'finalLOI') not in ['', None] else None
                    final_ir = float(metrics.get('finalIR')) if metrics.get(
                        'finalIR') not in ['', None] else None
                    final_timeline = int(
                        metrics.get('finalTimeline')) if metrics.get(
                            'finalTimeline') not in ['', None] else None
                    quality_rejects = int(
                        metrics.get('qualityRejects')) if metrics.get(
                            'qualityRejects') not in ['', None] else None
                    communication = int(
                        metrics.get('communication')) if metrics.get(
                            'communication') not in ['', None] else None
                    engagement = int(metrics.get('engagement')) if metrics.get(
                        'engagement') not in ['', None] else None
                    problem_solving = int(
                        metrics.get('problemSolving')) if metrics.get(
                            'problemSolving') not in ['', None] else None

                    cur.execute(
                        """
                        UPDATE partner_audience_responses par
                        SET 
                            final_loi = %s,
                            final_ir = %s,
                            final_timeline = %s,
                            quality_rejects = %s,
                            communication = %s,
                            engagement = %s,
                            problem_solving = %s,
                            additional_feedback = %s
                        WHERE partner_response_id = %s 
                        AND audience_id = %s
                        AND allocation > 0
                    """, (final_loi, final_ir, final_timeline, quality_rejects,
                          communication, engagement, problem_solving,
                          metrics.get('additionalFeedback'),
                          partner_response_id, audience_id))
            else:
                # Handle delivered numbers for this partner/LOI
                audience_id, country = key.split('_')
                delivered = value.get('delivered')

                # Convert empty string to None for n_delivered
                n_delivered = int(delivered) if delivered not in ['', None
                                                                  ] else None

                cur.execute(
                    """
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


@app.route('/api/bids/<bid_id>/closure-data', methods=['GET'])
def get_closure_data(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get metrics data with LOI-specific information
        cur.execute(
            """
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
                    par.communication as communication,
                    par.engagement as engagement,
                    par.problem_solving as problem_solving,
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
        """, (bid_id, ))

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
                    'required':
                    row['required'],
                    'allocation':
                    row['allocation'],
                    'delivered':
                    row['n_delivered']
                    if row['n_delivered'] is not None else ''
                }

            # Add metrics data
            if partner_key not in closure_data[audience_key]['metrics']:
                closure_data[audience_key]['metrics'][partner_key] = {
                    'finalLOI': row['final_loi'],
                    'finalIR': row['final_ir'],
                    'finalTimeline': row['final_timeline'],
                    'qualityRejects': row['quality_rejects'],
                    'communication': row['communication'],
                    'engagement': row['engagement'],
                    'problemSolving': row['problem_solving'],
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
        cur.execute("SELECT id FROM bids WHERE bid_number = %s",
                    (str(bid_id), ))
        bid = cur.fetchone()
        if not bid:
            return jsonify({"error": f"Bid {bid_id} not found"}), 404
        actual_bid_id = bid[0]

        # Get PO number
        cur.execute(
            """
            SELECT po_number 
            FROM bid_po_numbers 
            WHERE bid_id = %s
        """, (actual_bid_id, ))
        po_result = cur.fetchone()
        po_number = po_result[0] if po_result else ''

        # Get saved invoice details for all partners and LOIs
        cur.execute(
            """
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
        """, (actual_bid_id, ))

        invoice_details_map = {}
        partner_invoice_fields = {}
        invoice_rows = cur.fetchall()
        for row in invoice_rows:
            partner_name = row[0]
            loi = row[1]
            key = f"{partner_name}_{loi}"
            invoice_date = row[2].strftime('%Y-%m-%d') if row[2] else ''
            invoice_sent = row[3].strftime('%Y-%m-%d') if row[3] else ''
            invoice_serial = row[4] or ''
            invoice_number = row[5] or ''
            invoice_amount = str(row[6]) if row[6] else '0.00'

            # Save the first non-empty invoice fields for this partner
            if partner_name not in partner_invoice_fields or (
                    not partner_invoice_fields[partner_name]['invoice_date']
                    and invoice_date):
                partner_invoice_fields[partner_name] = {
                    'invoice_date': invoice_date,
                    'invoice_sent': invoice_sent,
                    'invoice_serial': invoice_serial,
                    'invoice_number': invoice_number,
                    'invoice_amount': invoice_amount
                }

            invoice_details_map[key] = {
                'invoice_date': invoice_date,
                'invoice_sent': invoice_sent,
                'invoice_serial': invoice_serial,
                'invoice_number': invoice_number,
                'invoice_amount': invoice_amount
            }

        # Get deliverables data
        cur.execute(
            """
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
                COALESCE(par.initial_cost, (par.n_delivered * par.cpi)) as initial_cost,
                COALESCE(par.final_cost, (par.final_cpi * par.n_delivered)) as final_cost
            FROM partner_lois pl
            JOIN partner_audience_responses par ON par.partner_response_id = pl.response_id
            WHERE par.n_delivered > 0
            ORDER BY pl.partner_name, pl.loi, par.audience_id, par.country
        """, (actual_bid_id, ))

        results = cur.fetchall()
        if not results:
            return jsonify({"error":
                            "No partner data found for this bid"}), 404

        # Group deliverables by partner and LOI
        deliverables_by_partner = {}
        for row in results:
            partner_name = row[0]
            loi = row[1]
            key = f"{partner_name}_{loi}"

            if key not in deliverables_by_partner:
                deliverables_by_partner[key] = []

            deliverables_by_partner[key].append({
                "partner_name":
                partner_name,
                "loi":
                loi,
                "audience_id":
                row[7],
                "country":
                row[8],
                "allocation":
                row[9],
                "n_delivered":
                row[10] if row[10] is not None else 0,
                "initial_cpi":
                float(row[11]) if row[11] is not None else 0.0,
                "final_cpi":
                float(row[12]) if row[12] is not None else 0.0,
                "initial_cost":
                float(row[13]) if row[13] is not None else 0.0,
                "final_cost":
                float(row[14]) if row[14] is not None else 0.0,
                "savings":
                float(row[13] - row[14])
                if row[13] is not None and row[14] is not None else 0.0
            })

        # Build response, always use the partner's default invoice fields if this LOI's are empty
        response_data = {
            "po_number": po_number,
            "partner_data": {
                key: {
                    'invoice_date':
                    invoice_details_map[key]['invoice_date']
                    or partner_invoice_fields[partner_name]['invoice_date'],
                    'invoice_sent':
                    invoice_details_map[key]['invoice_sent']
                    or partner_invoice_fields[partner_name]['invoice_sent'],
                    'invoice_serial':
                    invoice_details_map[key]['invoice_serial']
                    or partner_invoice_fields[partner_name]['invoice_serial'],
                    'invoice_number':
                    invoice_details_map[key]['invoice_number']
                    or partner_invoice_fields[partner_name]['invoice_number'],
                    'invoice_amount':
                    invoice_details_map[key]['invoice_amount']
                    or partner_invoice_fields[partner_name]['invoice_amount'],
                    "deliverables":
                    deliverables
                }
                for key, deliverables in deliverables_by_partner.items()
                for partner_name in [key.split('_')[0]]
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


@app.route('/api/invoice/<int:bid_id>/<string:partner_name>/<int:loi>/details',
           methods=['GET'])
def get_invoice_details(bid_id, partner_name, loi):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT 
                par.audience_id,
                bta.ta_category,
                bta.broader_category,
                bta.mode,
                bta.ir,
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
            JOIN bid_target_audiences bta ON par.audience_id = bta.id
            LEFT JOIN bid_po_numbers bpn ON b.id = bpn.bid_id
            WHERE b.bid_number = %s::VARCHAR 
            AND p.partner_name = %s 
            AND pr.loi = %s
            AND par.n_delivered > 0
        """, (bid_id, partner_name, loi))

        deliverables = cur.fetchall()
        po_number = deliverables[0]['po_number'] if deliverables else None

        return jsonify({"deliverables": deliverables, "po_number": po_number})

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
        cur.execute("SELECT id FROM bids WHERE bid_number = %s",
                    (str(bid_number), ))
        bid_row = cur.fetchone()
        if not bid_row:
            raise Exception(f"Bid with number {bid_number} not found")

        bid_id = bid_row[0]
        print(f"Found bid_id {bid_id} for bid_number {bid_number}")

        # Update invoice details in partner_responses
        cur.execute(
            """
            UPDATE partner_responses pr
            SET 
                invoice_date = CASE 
                    WHEN %s IS NOT NULL AND %s != '' THEN %s::DATE 
                    ELSE invoice_date
                END,
                invoice_sent = CASE 
                    WHEN %s IS NOT NULL AND %s != '' THEN %s::DATE 
                    ELSE invoice_sent
                END,
                invoice_serial = CASE 
                    WHEN %s IS NOT NULL THEN %s 
                    ELSE invoice_serial
                END,
                invoice_number = CASE 
                    WHEN %s IS NOT NULL THEN %s 
                    ELSE invoice_number
                END,
                invoice_amount = CASE 
                    WHEN %s IS NOT NULL THEN %s::DECIMAL 
                    ELSE invoice_amount
                END,
                updated_at = CURRENT_TIMESTAMP
            FROM partners p
            WHERE pr.bid_id = %s
            AND p.partner_name = %s
            AND pr.partner_id = p.id
            AND pr.loi = %s
        """, (data['invoice_data'].get('invoice_date'),
              data['invoice_data'].get('invoice_date'),
              data['invoice_data'].get('invoice_date'),
              data['invoice_data'].get('invoice_sent'),
              data['invoice_data'].get('invoice_sent'),
              data['invoice_data'].get('invoice_sent'),
              data['invoice_data'].get('invoice_serial'),
              data['invoice_data'].get('invoice_serial'),
              data['invoice_data'].get('invoice_number'),
              data['invoice_data'].get('invoice_number'),
              data['invoice_data'].get('invoice_amount'),
              data['invoice_data'].get('invoice_amount'), bid_id,
              data['partner_name'], data['loi']))

        # Get partner_id from partner_name
        cur.execute(
            """
            SELECT id FROM partners WHERE partner_name = %s
        """, (data['partner_name'], ))

        partner_row = cur.fetchone()
        if not partner_row:
            raise Exception(f"Partner '{data['partner_name']}' not found")

        partner_id = partner_row[0]

        # Get partner_response_id
        cur.execute(
            """
            SELECT id FROM partner_responses 
            WHERE bid_id = %s AND partner_id = %s AND loi = %s
        """, (bid_id, partner_id, data['loi']))

        response_row = cur.fetchone()
        if not response_row:
            # If partner_response doesn't exist, create it
            print(
                f"Creating new partner_response for bid_id={bid_id}, partner_id={partner_id}, loi={data['loi']}"
            )
            cur.execute(
                """
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
            cur.execute(
                """
                SELECT id FROM partner_audience_responses
                WHERE partner_response_id = %s
                AND audience_id = %s
                AND country = %s
            """, (partner_response_id, deliverable['audience_id'],
                  deliverable['country']))

            par_row = cur.fetchone()

            if par_row:
                # Update existing record
                cur.execute(
                    """
                    UPDATE partner_audience_responses
                    SET 
                        final_cpi = %s,
                        final_cost = %s,
                        initial_cost = COALESCE(initial_cost, n_delivered * cpi),
                        savings = COALESCE(n_delivered * cpi, 0) - %s
                    WHERE id = %s
                """, (deliverable['final_cpi'], deliverable['final_cost'],
                      deliverable['final_cost'], par_row[0]))
            else:
                # Create a new record
                print(
                    f"Creating new partner_audience_response for response_id={partner_response_id}, audience_id={deliverable['audience_id']}, country={deliverable['country']}"
                )
                cur.execute(
                    """
                    INSERT INTO partner_audience_responses 
                    (bid_id, partner_response_id, audience_id, country, 
                     cpi, final_cpi, final_cost, n_delivered, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                    (
                        bid_id,
                        partner_response_id,
                        deliverable['audience_id'],
                        deliverable['country'],
                        0,  # Initial CPI
                        deliverable['final_cpi'],
                        deliverable['final_cost'],
                        deliverable['final_cost'] / deliverable['final_cpi']
                        if deliverable['final_cpi'] > 0 else 0))

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

        # Get all numeric bid numbers, convert to integers, and find the max
        cur.execute("""
            SELECT bid_number 
            FROM bids
            WHERE bid_number ~ '^[0-9]+$'
            ORDER BY CAST(bid_number AS INTEGER) DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        
        if result:
            current_max = int(result[0])
            print(f"Found current max bid number: {current_max}")
        else:
            # If no numeric bid numbers found, start from 33484
            current_max = 33484
            print("No numeric bid numbers found, starting from 33484")
        
        # The next bid number should always be current_max + 1
        next_bid_number = str(current_max + 1)
        print(f"Returning next bid number: {next_bid_number}")

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
        rejection_reason = data.get('rejection_reason')
        rejection_comments = data.get('rejection_comments')

        # Start transaction
        cur.execute("BEGIN")

        # Standardize status values
        status_mapping = {
            'infield': 'infield',
            'in_field': 'infield',
            'in-field': 'infield',
            'draft': 'draft',
            'completed': 'completed',
            'invoiced': 'invoiced',
            'rejected': 'rejected'
        }

        # Map the incoming status to standardized value
        standardized_status = status_mapping.get(status.lower(), status)

        # Update bid status and rejection fields if present
        if standardized_status == 'rejected':
            cur.execute(
                """
                UPDATE bids 
                SET status = %s,
                    rejection_reason = %s,
                    rejection_comments = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """, (standardized_status, rejection_reason,
                      rejection_comments, bid_id))
        else:
            cur.execute(
                """
                UPDATE bids 
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """, (standardized_status, bid_id))

        # Insert or update PO number in bid_po_numbers table
        if po_number:
            cur.execute(
                """
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
        cur.execute(
            """
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
        """, (bid_id, ))

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
        cur.execute(
            """
            SELECT 
                b.study_name,
                b.status,
                b.bid_number,
                bpn.po_number
            FROM bids b
            LEFT JOIN bid_po_numbers bpn ON b.id = bpn.bid_id
            WHERE b.id = %s
        """, (bid_id, ))
        bid_details = cur.fetchone()

        # Get audience data only for valid combinations
        if partners:  # Only get audience data if we have valid partners
            cur.execute(
                """
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
            if not current_audience or current_audience['id'] != row[
                    'audience_id']:
                current_audience = {
                    'id': row['audience_id'],
                    'name': row['audience_name'],
                    'ta_category': row['ta_category'],
                    'deliverables': []
                }
                audiences.append(current_audience)

            current_audience['deliverables'].append({
                'partner_id':
                row['partner_id'],
                'loi':
                row['loi'],
                'country':
                row['country'],
                'allocation':
                row['allocation'] or 0,
                'n_delivered':
                row['n_delivered'] or 0,
                'initial_cpi':
                float(row['initial_cpi']) if row['initial_cpi'] else 0,
                'final_cpi':
                float(row['final_cpi']) if row['final_cpi'] else 0,
                'initial_cost':
                float(row['initial_cost']) if row['initial_cost'] else 0,
                'final_cost':
                float(row['final_cost']) if row['final_cost'] else 0
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
            WHERE status = 'invoiced'
        """)
        avg_turnaround = cur.fetchone()['avg_time'] or 0

        # Get bids by status
        cur.execute("""
            SELECT status::text as status, COUNT(*) as count
            FROM bids
            GROUP BY status
        """)
        status_counts = cur.fetchall()

        # Get client-wise bid summary with corrected metrics
        cur.execute("""
            WITH client_metrics AS (
                SELECT 
                    c.client_name,
                    COUNT(b.id) as total_bids,
                    SUM(CASE WHEN b.status::text = 'infield' THEN 1 ELSE 0 END) as bids_in_field,
                    SUM(CASE WHEN b.status::text = 'closure' THEN 1 ELSE 0 END) as bid_closed,
                    SUM(CASE WHEN b.status::text = 'invoiced' THEN 1 ELSE 0 END) as bid_invoiced,
                    SUM(CASE WHEN b.status::text = 'rejected' THEN 1 ELSE 0 END) as bids_rejected,
                    COALESCE(SUM(CASE 
                        WHEN b.status IN ('closure', 'ready_for_invoice', 'invoiced') 
                        THEN COALESCE(
                            (SELECT SUM(par.n_delivered * COALESCE(par.final_cpi, par.cpi))
                             FROM partner_audience_responses par
                             JOIN partner_responses pr ON par.partner_response_id = pr.id
                             WHERE pr.bid_id = b.id), 
                            0)
                        ELSE 0 
                    END), 0) as total_amount
                FROM clients c
                LEFT JOIN bids b ON b.client = c.id
                GROUP BY c.client_name
            )
            SELECT 
                client_name,
                total_bids,
                bids_in_field,
                bid_closed,
                bid_invoiced,
                bids_rejected,
                ROUND(total_amount::numeric, 2) as total_amount,
                CASE 
                    WHEN total_bids = 0 THEN 0
                    ELSE ROUND(((bids_in_field + bid_closed + bid_invoiced)::float / total_bids * 100)::numeric, 2)
                END as conversion_rate
            FROM client_metrics
            ORDER BY total_bids DESC
        """)
        client_summary = cur.fetchall()

        # Status mapping
        status_mapping = {
            'draft': 'Draft',
            'infield': 'In Field',
            'in_field': 'In Field',
            'closure': 'Closure',
            'ready_for_invoice': 'Ready to Invoice',
            'invoiced': 'Completed',
            'rejected': 'Rejected'
        }

        bids_by_status = {
            "Draft": 0,
            "Partner Response": 0,
            "In Field": 0,
            "Closure": 0,
            "Ready to Invoice": 0,
            "Completed": 0,
            "Rejected": 0
        }

        for row in status_counts:
            status = row['status'].lower()
            count = row['count']
            mapped_status = status_mapping.get(status, status.capitalize())
            if mapped_status in bids_by_status:
                bids_by_status[mapped_status] += count

        # Create the dashboard data dictionary
        dashboard_data = {
            "total_bids":
            int(total_bids) if total_bids else 0,
            "active_bids":
            int(active_bids) if active_bids else 0,
            "total_savings":
            float(total_savings) if total_savings else 0.0,
            "avg_turnaround_time":
            round(float(avg_turnaround), 1) if avg_turnaround else 0.0,
            "bids_by_status":
            bids_by_status,
            "client_summary":
            client_summary if client_summary else []
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
                "Completed": 0,
                "Rejected": 0
            },
            "client_summary": []
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
            default_password = "admin"  # Set a default password
            hashed_password = generate_password_hash(default_password,
                                                     method='pbkdf2:sha256')

            cur.execute(
                """
                INSERT INTO users (email, name, password_hash, role, team, employee_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('admin@example.com', 'Admin User', hashed_password, 'admin',
                  'Operations', 'EMP001'))

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

        print(
            f"Updating closure data for bid {bid_id}, partner {data['partner']}, LOI {data['loi']}"
        )

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
            cur.execute(
                """
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
                    print(
                        f"Updating n_delivered for country {country}: {n_delivered}"
                    )

                    cur.execute(
                        """
                        UPDATE partner_audience_responses par
                        SET 
                            field_close_date = %s::date,
                            n_delivered = %s,
                            final_loi = %s,
                            final_ir = %s,
                            final_timeline = %s,
                            quality_rejects = %s,
                            communication = %s,
                            engagement = %s,
                            problem_solving = %s,
                            additional_feedback = %s
                        WHERE par.id = %s
                    """, (field_close_date, n_delivered,
                          metrics.get('finalLOI'), metrics.get('finalIR'),
                          metrics.get('finalTimeline'),
                          metrics.get('qualityRejects'),
                          metrics.get('communication'),
                          metrics.get('engagement'),
                          metrics.get('problemSolving'),
                          metrics.get('additionalFeedback'), record_id))
                    print(
                        f"Updated metrics and n_delivered for audience {audience['id']}, country {country}"
                    )
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
        cur.execute(
            """
            UPDATE bids 
            SET status = 'invoiced'
            WHERE id = %s
        """, (bid_id, ))

        conn.commit()
        return jsonify(
            {"message": "Bid status updated to invoiced successfully"})

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

        cur.execute(
            """
            SELECT id, bid_number, status
            FROM bids
            WHERE bid_number = %s
        """, (bid_number, ))

        bid = cur.fetchone()
        if bid:
            # Convert any Decimal values to float
            bid = {
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in bid.items()
            }

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
        cur.execute(
            """
            UPDATE bids 
            SET status = 'infield'
            WHERE bid_number = %s
            RETURNING id, bid_number, status
        """, (bid_number, ))

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

        cur.execute(
            """
            UPDATE users 
            SET email = %s,
                name = %s,
                employee_id = %s,
                role = %s,
                team = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (data['email'], data['name'], data['employee_id'], data['role'],
              data['team'], user_id))

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
            return jsonify({"message":
                            "Partner responses saved in session"}), 200

        bid_id = int(bid_id)
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        data = request.json
        partners = data.get('partners', [])
        lois = data.get('lois', [])

        # Start transaction
        cur.execute("BEGIN")

        # Get existing partner responses to preserve data
        cur.execute(
            """
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                pr.currency,
                pr.pmf,
                par.audience_id,
                par.country,
                par.commitment,
                par.commitment_type,
                par.cpi,
                par.timeline_days,
                par.comments
            FROM partner_responses pr
            LEFT JOIN partner_audience_responses par ON pr.id = par.partner_response_id
            WHERE pr.bid_id = %s
        """, (bid_id, ))

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
                cur.execute(
                    """
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
                        if (f"{partner}-{loi}" in key
                                and data.get('audience_id')
                                and data.get('country')):

                            cur.execute(
                                """
                                INSERT INTO partner_audience_responses 
                                (bid_id, partner_response_id, audience_id, country, 
                                 commitment, cpi, timeline_days, comments, initial_cost)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (bid_id, partner_response_id, audience_id, country) 
                                DO UPDATE SET 
                                    commitment = EXCLUDED.commitment,
                                    cpi = EXCLUDED.cpi,
                                    timeline_days = EXCLUDED.timeline_days,
                                    comments = EXCLUDED.comments,
                                    initial_cost = EXCLUDED.initial_cost
                            """,
                                (
                                    bid_id,
                                    partner_response_id,
                                    data['audience_id'],
                                    data['country'],
                                    data.get('commitment',
                                             0),  # Default to 0 if NULL
                                    data.get('cpi', 0),
                                    data.get('timeline_days', 0),
                                    data.get('comments', ''),
                                    data.get('initial_cost',
                                             0)  # Default to 0 if NULL
                                ))

        conn.commit()
        return jsonify({"message":
                        "Partner responses updated successfully"}), 200

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
        cur.execute(
            """
            SELECT partners, loi
            FROM bids
            WHERE id = %s
        """, (bid_id, ))

        bid_data = cur.fetchone()
        if not bid_data:
            return jsonify({"error": "Bid not found"}), 404

        # Get the full list of partners and LOIs from the bid
        partners = bid_data.get('partners', [])
        lois = bid_data.get('loi', [])

        return jsonify({"partners": partners, "lois": lois})

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
        cur.execute(
            """
            SELECT id 
            FROM bid_target_audiences 
            WHERE bid_id = %s 
            ORDER BY id
        """, (bid_id, ))

        audience_ids = [row['id'] for row in cur.fetchall()]

        # First get all partner responses (including those without audience responses)
        # This ensures we get PMF values for all partner-LOI combinations
        cur.execute(
            """
            SELECT 
                pr.id,
                pr.partner_id,
                pr.loi,
                pr.currency,
                pr.pmf,
                pr.status
            FROM partner_responses pr
            WHERE pr.bid_id = %s
        """, (bid_id, ))

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
        cur.execute(
            """
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
        """, (bid_id, ))

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
                    responses[key]['audiences'][audience_key][
                        row['country']] = {
                            'commitment': row['commitment'] or 0,
                            'cpi':
                            float(row['cpi']) if row['cpi'] is not None else 0
                        }

        return jsonify({'responses': responses, 'settings': settings})

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
        response.headers.add('Access-Control-Allow-Origin',
                             'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.status_code = 200
        return response

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # First, get the actual bid_id from the bid_number
        cur.execute("SELECT id FROM bids WHERE bid_number = %s",
                    (str(bid_id), ))
        bid_row = cur.fetchone()
        if not bid_row:
            raise Exception(f"Bid with number {bid_id} not found")

        actual_bid_id = bid_row[0]

        # Update bid status to 'invoiced'
        cur.execute(
            """
            UPDATE bids 
            SET status = 'invoiced',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (actual_bid_id, ))

        conn.commit()
        response = jsonify({"message": "Invoice submitted successfully"})
        response.headers.add('Access-Control-Allow-Origin',
                             'http://localhost:5173')
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

        # Update completed statuses to invoiced where appropriate
        cur.execute("""
            UPDATE bids 
            SET status = 'invoiced'
            WHERE status::text = 'completed'
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
    response.headers.add('Access-Control-Allow-Origin',
                         'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,POST,PUT,DELETE,OPTIONS')
    return response


@app.route('/api/bids/<bid_id>/partner-responses', methods=['PUT'])
def update_partner_responses(bid_id):
    try:
        data = request.json
        responses = data.get('responses', {})

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Process each partner response
        for key, response_data in responses.items():
            partner_id = response_data.get('partner_id')
            loi = response_data.get('loi')

            # Get or create partner_response record
            cur.execute(
                """
                SELECT id FROM partner_responses 
                WHERE bid_id = %s AND partner_id = %s AND loi = %s
            """, (bid_id, partner_id, loi))

            partner_response = cur.fetchone()
            if partner_response:
                partner_response_id = partner_response['id']
                # Update existing partner response with new PMF value
                cur.execute(
                    """
                    UPDATE partner_responses 
                    SET pmf = %s,
                        currency = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (response_data.get(
                        'pmf', 0), response_data.get(
                            'currency', 'USD'), partner_response_id))
            else:
                cur.execute(
                    """
                    INSERT INTO partner_responses 
                    (bid_id, partner_id, loi, status, currency, pmf)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (bid_id, partner_id, loi, 'draft',
                      response_data.get('currency',
                                        'USD'), response_data.get('pmf', 0)))
                partner_response_id = cur.fetchone()['id']

            # Process audience data
            audiences = response_data.get('audiences', {})
            for audience_key, audience_data in audiences.items():
                # Accept both numeric and 'audience-<id>' keys
                try:
                    if isinstance(audience_key,
                                  int) or (isinstance(audience_key, str)
                                           and audience_key.isdigit()):
                        audience_id = int(audience_key)
                    elif isinstance(
                            audience_key,
                            str) and audience_key.startswith('audience-'):
                        audience_id = int(audience_key.split('-')[1])
                    else:
                        print(f"Invalid audience key format: {audience_key}")
                        continue
                except (IndexError, ValueError):
                    print(f"Invalid audience key format: {audience_key}")
                    continue

                timeline = audience_data.get('timeline', 0)
                comments = audience_data.get('comments', '')

                # Process each country in the audience
                for country, country_data in audience_data.items():
                    if country in ('timeline', 'comments'):
                        continue

                    commitment = country_data.get('commitment', 0)
                    cpi = country_data.get('cpi', 0)
                    commitment_type = country_data.get('commitment_type',
                                                       'fixed')
                    is_best_efforts = commitment_type == 'be_max'

                    # Check if response already exists
                    cur.execute(
                        """
                        SELECT id FROM partner_audience_responses
                        WHERE partner_response_id = %s 
                        AND audience_id = %s 
                        AND country = %s
                    """, (partner_response_id, audience_id, country))

                    existing_response = cur.fetchone()

                    if existing_response:
                        # Update existing response
                        cur.execute(
                            """
                            UPDATE partner_audience_responses 
                            SET commitment = %s,
                                cpi = %s,
                                timeline_days = %s,
                                comments = %s,
                                commitment_type = %s,
                                is_best_efforts = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (commitment, cpi, timeline, comments,
                              commitment_type, is_best_efforts,
                              existing_response['id']))
                    else:
                        # Insert new response
                        cur.execute(
                            """
                            INSERT INTO partner_audience_responses 
                            (bid_id, partner_response_id, audience_id, country, 
                             commitment, cpi, timeline_days, comments, commitment_type, is_best_efforts, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (bid_id, partner_response_id, audience_id,
                              country, commitment, cpi, timeline, comments,
                              commitment_type, is_best_efforts))

        conn.commit()
        return jsonify({"message":
                        "Partner responses updated successfully"}), 200

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
        cur.execute(
            """
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
        """, (data.get('partner_name'), data.get('contact_person'),
              data.get('contact_email'), data.get('contact_phone'),
              data.get('website'), data.get('company_address'),
              data.get('specialized'), data.get('geographic_coverage'),
              partner_id))

        updated_partner = cur.fetchone()
        conn.commit()

        if not updated_partner:
            return jsonify(
                {"error": f"Partner with ID {partner_id} not found"}), 404

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
        cur.execute("SELECT id FROM partners WHERE id = %s", (partner_id, ))
        if not cur.fetchone():
            return jsonify(
                {"error": f"Partner with ID {partner_id} not found"}), 404

        # Delete the partner
        cur.execute("DELETE FROM partners WHERE id = %s", (partner_id, ))
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
        cur.execute(
            """
            UPDATE vendor_managers
            SET vm_id = %s,
                vm_name = %s,
                contact_person = %s,
                reporting_manager = %s,
                team = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at
        """, (data.get('vm_id'), data.get('vm_name'),
              data.get('contact_person'), data.get('reporting_manager'),
              data.get('team'), vm_id))

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
        cur.execute("SELECT id FROM vendor_managers WHERE id = %s", (vm_id, ))
        if not cur.fetchone():
            return jsonify({"error": f"VM with ID {vm_id} not found"}), 404

        # Delete the VM
        cur.execute("DELETE FROM vendor_managers WHERE id = %s", (vm_id, ))
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


@app.route('/api/sales/<int:sales_id>', methods=['PUT'])
def update_sales(sales_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        data = request.json
        print(f"Updating sales {sales_id} with data: {data}")

        # Update sales information
        cur.execute(
            """
            UPDATE sales
            SET sales_id = %s,
                sales_person = %s,
                contact_person = %s,
                reporting_manager = %s,
                region = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at
        """, (data.get('sales_id'), data.get('sales_person'),
              data.get('contact_person'), data.get('reporting_manager'),
              data.get('region'), sales_id))

        updated_sales = cur.fetchone()
        conn.commit()

        if not updated_sales:
            return jsonify({"error":
                            f"Sales with ID {sales_id} not found"}), 404

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
        cur.execute("SELECT id FROM sales WHERE id = %s", (sales_id, ))
        if not cur.fetchone():
            return jsonify({"error":
                            f"Sales with ID {sales_id} not found"}), 404

        # Delete the sales
        cur.execute("DELETE FROM sales WHERE id = %s", (sales_id, ))
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


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# Serve React App
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        print(f"Login attempt with email: {email}")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get user from database
            cur.execute(
                "SELECT id, email, name, role, password_hash FROM users WHERE email = %s",
                (email, ))
            user = cur.fetchone()

            if not user:
                print(f"User not found: {email}")
                return jsonify({'error': 'Invalid email or password'}), 401

            password_hash = user['password_hash']
            is_authenticated = check_password_hash(password_hash, password)

            if is_authenticated:
                # Get permissions for the user's role
                permissions = ROLES_AND_PERMISSIONS.get(user['role'], {})

                user_data = {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role'],
                    'permissions': permissions
                }
                print(f"Login successful for {email}")
                return jsonify({
                    'token': 'sample-jwt-token',
                    'user': user_data
                })

            print(f"Login failed for email: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401

        finally:
            cur.close()
            conn.close()

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500


def get_public_host_url():
    forwarded_host = request.headers.get('X-Forwarded-Host')
    if forwarded_host:
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        return f"{scheme}://{forwarded_host}/"
    # For Replit deployment
    return request.host_url.replace('http://', 'https://')


@app.route('/api/bids/<int:bid_id>/partners/<int:partner_id>/generate-link',
           methods=['POST'])
def generate_partner_link(bid_id, partner_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check if a valid link already exists
        cur.execute(
            """
            SELECT id, token, expires_at 
            FROM partner_links 
            WHERE bid_id = %s AND partner_id = %s AND expires_at > NOW()
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (bid_id, partner_id))
        existing_link = cur.fetchone()

        if existing_link:
            return jsonify({
                'link':
                f"{get_public_host_url()}partner-response/{existing_link['token']}",
                'expires_at':
                existing_link['expires_at'].isoformat()
            })

        # Generate new token and set expiry to 30 days
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)

        cur.execute(
            """
            INSERT INTO partner_links (bid_id, partner_id, token, expires_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, token, expires_at
        """, (bid_id, partner_id, token, expires_at))

        new_link = cur.fetchone()
        conn.commit()

        return jsonify({
            'link':
            f"{get_public_host_url()}partner-response/{new_link['token']}",
            'expires_at': new_link['expires_at'].isoformat()
        })
    except Exception as e:
        print(f"Error generating link: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/bids/<int:bid_id>/partners/<int:partner_id>/extend-link',
           methods=['POST'])
def extend_partner_link(bid_id, partner_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get the most recent link (even if expired)
        cur.execute(
            """
            SELECT id, token, expires_at 
            FROM partner_links 
            WHERE bid_id = %s AND partner_id = %s
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (bid_id, partner_id))
        existing_link = cur.fetchone()

        if not existing_link:
            return jsonify({"error": "No link found to extend"}), 404

        # Extend expiry by 30 days from now
        new_expires_at = datetime.now() + timedelta(days=30)

        cur.execute(
            """
            UPDATE partner_links 
            SET expires_at = %s 
            WHERE id = %s
            RETURNING id, token, expires_at
        """, (new_expires_at, existing_link['id']))

        updated_link = cur.fetchone()
        conn.commit()

        # Send email notification about extended link
        try:
            cur.execute(
                """
                SELECT p.email, p.partner_name, b.bid_number, b.study_name
                FROM partners p
                JOIN bids b ON b.id = %s
                WHERE p.id = %s
            """, (bid_id, partner_id))
            partner_info = cur.fetchone()

            if partner_info and partner_info['email']:
                send_link_extension_email(
                    partner_info['email'], partner_info['partner_name'],
                    partner_info['bid_number'], partner_info['study_name'],
                    f"{get_public_host_url()}partner-response/{updated_link['token']}",
                    updated_link['expires_at'])
        except Exception as email_error:
            print(f"Error sending extension email: {str(email_error)}")

        return jsonify({
            'link':
            f"{get_public_host_url()}partner-response/{updated_link['token']}",
            'expires_at': updated_link['expires_at'].isoformat()
        })
    except Exception as e:
        print(f"Error extending link: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


def send_link_extension_email(email, partner_name, bid_number, study_name,
                              link, expires_at):
    try:
        msg = Message('Your Partner Response Link Has Been Extended',
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[email])

        msg.body = f"""
        Dear {partner_name},

        Your access link for bid {bid_number} ({study_name}) has been extended.

        New Link: {link}
        New Expiry Date: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}

        You can use this link to view and edit your response.

        Best regards,
        Bid Management Team
        """

        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {str(e)}")


@app.route('/partner-response/<path:token>', methods=['GET'])
def partner_response_form(token):
    try:
        dist_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'dist'))
        if os.path.exists(os.path.join(dist_dir, token)):
            return send_from_directory(dist_dir, token)
        return send_from_directory(dist_dir, 'index.html')
    except Exception as e:
        print(f"Error serving partner response form: {str(e)}")
        return "Error loading page", 500


@app.route('/api/partner-link/<token>', methods=['GET'])
def get_partner_link_data(token):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT bid_id, partner_id, expires_at FROM partner_links WHERE token = %s
            """, (token, ))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Invalid or expired link."}), 404
        bid_id, partner_id, expires_at = row['bid_id'], row['partner_id'], row[
            'expires_at']
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return jsonify({"error": "This link has expired."}), 410

        # Fetch all the same data as PartnerResponse page, but for this partner and bid
        # Get bid details
        cur.execute(
            """
            SELECT * FROM bids WHERE id = %s
            """, (bid_id, ))
        bid_data = cur.fetchone()
        if not bid_data:
            return jsonify({"error": "Bid not found."}), 404

        # Get partner details
        cur.execute(
            """
            SELECT * FROM partners WHERE id = %s
            """, (partner_id, ))
        partner_data = cur.fetchone()
        if not partner_data:
            return jsonify({"error": "Partner not found."}), 404

        # Get LOIs for this partner in this bid
        cur.execute(
            """
            SELECT loi FROM partner_responses WHERE bid_id = %s AND partner_id = %s
            """, (bid_id, partner_id))
        lois = [row['loi'] for row in cur.fetchall()]

        # Get target audiences for this bid
        cur.execute(
            """
            SELECT * FROM bid_target_audiences WHERE bid_id = %s
            """, (bid_id, ))
        audiences = cur.fetchall()

        # Get country samples for each audience
        cur.execute(
            """
            SELECT * FROM bid_audience_countries WHERE bid_id = %s
            """, (bid_id, ))
        country_samples = cur.fetchall()

        # Get partner responses (all LOIs)
        cur.execute(
            """
            SELECT * FROM partner_responses WHERE bid_id = %s AND partner_id = %s
            """, (bid_id, partner_id))
        partner_responses = cur.fetchall()

        # Get partner audience responses (all LOIs)
        cur.execute(
            """
            SELECT * FROM partner_audience_responses WHERE bid_id = %s AND partner_response_id IN (
                SELECT id FROM partner_responses WHERE bid_id = %s AND partner_id = %s
            )
            """, (bid_id, bid_id, partner_id))
        partner_audience_responses = cur.fetchall()

        return jsonify({
            "bid": bid_data,
            "partner": partner_data,
            "lois": lois,
            "audiences": audiences,
            "country_samples": country_samples,
            "partner_responses": partner_responses,
            "partner_audience_responses": partner_audience_responses,
            "expires_at": expires_at.isoformat(),
        })
    except Exception as e:
        print(f"Error in get_partner_link_data: {str(e)}")
        return jsonify({"error": "An error occurred."}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/partner-link/<token>', methods=['POST'])
def submit_partner_link_response(token):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        print("Received data for partner link submission:", data)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Look up token
        cur.execute(
            """
            SELECT pl.bid_id, pl.partner_id, pl.expires_at 
            FROM partner_links pl
            WHERE pl.token = %s
            """, (token, ))

        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Invalid or expired link."}), 404

        bid_id = row['bid_id']
        partner_id = row['partner_id']
        expires_at = row['expires_at']

        # Validate expires_at timezone
        if expires_at.tzinfo is None:
            from datetime import timezone
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        from datetime import datetime, timezone
        if expires_at < datetime.now(timezone.utc):
            return jsonify({"error": "This link has expired."}), 403

        # Extract and validate required fields
        pmf = data.get('pmf')
        if pmf is None:
            return jsonify({"error": "PMF is required"}), 400

        currency = data.get('currency', 'USD')
        form_data = data.get('form')
        if not form_data:
            return jsonify({"error": "Form data is required"}), 400
        for loi, audiences in data.get('form', {}).items():
            # Upsert main partner_responses row for this LOI, now with pmf and currency
            cur.execute(
                """
                INSERT INTO partner_responses (bid_id, partner_id, loi, status, pmf, currency, updated_at)
                VALUES (%s, %s, %s, 'pending', %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (bid_id, partner_id, loi)
                DO UPDATE SET pmf = EXCLUDED.pmf, currency = EXCLUDED.currency, updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (bid_id, partner_id, loi, pmf, currency))
            result = cur.fetchone()
            if result is None:
                # Try to fetch the existing row
                cur.execute(
                    "SELECT id FROM partner_responses WHERE bid_id = %s AND partner_id = %s AND loi = %s",
                    (bid_id, partner_id, loi))
                result = cur.fetchone()
                if result is None:
                    print(
                        f"Failed to find or insert partner_responses for bid_id={bid_id}, partner_id={partner_id}, loi={loi}"
                    )
                    return jsonify(
                        {"error": "Failed to save partner response."}), 500
            # Get partner_response_id directly from the last query
            cur.execute(
                """
                SELECT pr.id FROM partner_responses pr
                WHERE pr.bid_id = %s AND pr.partner_id = %s AND pr.loi = %s
            """, (bid_id, partner_id, loi))
            result = cur.fetchone()

            if not result:
                raise Exception("Failed to get partner_response_id")

            partner_response_id = result['id']

            for audience_id, aud_data in audiences.items():
                timeline = aud_data.get('timeline')
                comments = aud_data.get('comments')
                for country, country_data in aud_data.get('countries',
                                                          {}).items():
                    commitment_type = country_data.get('commitment_type')
                    commitment = country_data.get('commitment')
                    cpi = country_data.get('cpi')
                    # Convert empty string to None for numeric fields
                    if commitment == '':
                        commitment = None
                    if cpi == '':
                        cpi = None
                    if timeline == '':
                        timeline = None
                    # Use INSERT ... ON CONFLICT DO UPDATE pattern with unique columns
                    cur.execute(
                        """
                        INSERT INTO partner_audience_responses 
                        (bid_id, partner_response_id, audience_id, country, 
                         commitment_type, commitment, cpi, timeline_days, comments, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (partner_response_id, audience_id, country) 
                        DO UPDATE SET 
                            commitment_type = EXCLUDED.commitment_type,
                            commitment = EXCLUDED.commitment,
                            cpi = EXCLUDED.cpi,
                            timeline_days = EXCLUDED.timeline_days,
                            comments = EXCLUDED.comments,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                        (bid_id, partner_response_id, audience_id, country,
                         commitment_type, commitment, cpi, timeline, comments))
        try:
            conn.commit()
            # Send admin notification email
            if ADMIN_NOTIFICATION_EMAIL:
                try:
                    msg = Message('Partner Response Updated',
                                  sender=app.config['MAIL_DEFAULT_SENDER'],
                                  recipients=[ADMIN_NOTIFICATION_EMAIL])
                    msg.body = f"""
                    Partner {partner_id} updated their response for Bid {bid_id}.
                    Link: {get_public_host_url()}partner-response/{token}
                    """
                    mail.send(msg)
                except Exception as e:
                    print(f"Error sending admin notification: {str(e)}")
            return jsonify({
                "success": True,
                "message": "Response saved successfully"
            })
        except Exception as commit_error:
            conn.rollback()
            print(f"Database commit error: {str(commit_error)}")
            return jsonify({"error":
                            "Database error while saving response"}), 500
    except Exception as e:
        print(f"Error in submit_partner_link_response: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            "error": "Failed to save partner response. Please try again.",
            "details": str(e)
        }), 500


@app.route('/api/bids/<int:bid_id>/partner-responses-summary', methods=['GET'])
def get_partner_responses_summary(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get bid info
        cur.execute("SELECT bid_number, study_name FROM bids WHERE id = %s",
                    (bid_id, ))
        bid = cur.fetchone()
        if not bid:
            cur.close()
            conn.close()
            return jsonify({"error": "Bid not found"}), 404

        # Get all LOIs for this bid
        cur.execute(
            "SELECT DISTINCT loi FROM partner_responses WHERE bid_id = %s ORDER BY loi",
            (bid_id, ))
        lois = [row['loi'] for row in cur.fetchall()]

        # Get all partners for this bid
        cur.execute(
            """
            SELECT DISTINCT p.id as partner_id, p.partner_name
            FROM partner_responses pr
            JOIN partners p ON pr.partner_id = p.id
            WHERE pr.bid_id = %s
        """, (bid_id, ))
        partners = cur.fetchall()

        # Get all audiences for this bid
        cur.execute(
            "SELECT id, audience_name FROM bid_target_audiences WHERE bid_id = %s",
            (bid_id, ))
        audiences = cur.fetchall()

        # Get all partner audience responses for this bid (with is_best_efforts and commitment_type)
        cur.execute(
            """
            SELECT pr.partner_id, pr.loi, par.audience_id, par.country, par.commitment, par.cpi, pr.status, pr.updated_at, par.is_best_efforts, par.commitment_type
            FROM partner_responses pr
            LEFT JOIN partner_audience_responses par ON pr.id = par.partner_response_id
            WHERE pr.bid_id = %s
        """, (bid_id, ))
        par_rows = cur.fetchall()

        # Organize responses by partner, loi, audience, country
        partner_loi_map = {}
        for row in par_rows:
            partner_id = row['partner_id']
            loi = row['loi']
            audience_id = row['audience_id']
            country = row['country']
            commitment = row['commitment']
            cpi = row['cpi']
            status = row['status']
            updated_at = row['updated_at']
            is_best_efforts = row['is_best_efforts']
            commitment_type = row['commitment_type']
            if partner_id is None or loi is None:
                continue
            partner_loi_map.setdefault(partner_id, {})
            partner_loi_map[partner_id].setdefault(
                loi, {
                    'status': status,
                    'updated_at': updated_at,
                    'audiences': {},
                    'be_max_count': 0,
                    'commitment_count': 0,
                    'total_count': 0,
                    'complete_count': 0
                })
            if audience_id is not None and country is not None:
                aud = partner_loi_map[partner_id][loi]['audiences'].setdefault(
                    audience_id, {'countries': []})
                # Use is_best_efforts and commitment_type from partner response
                c_type = 'be_max' if (commitment_type == 'be_max'
                                      or is_best_efforts) else 'commitment'
                # For BE/Max, count as complete if cpi is not None and cpi > 0 (ignore commitment)
                # For Commitment, count as complete if commitment > 0 AND cpi is not None and cpi > 0
                if c_type == 'be_max':
                    c_status = 'complete' if (cpi is not None
                                              and cpi > 0) else 'missing'
                else:
                    c_status = 'complete' if (commitment and commitment > 0
                                              and cpi is not None
                                              and cpi > 0) else 'missing'
                aud['countries'].append({
                    'name': country,
                    'status': c_status,
                    'type': c_type
                })
                partner_loi_map[partner_id][loi]['total_count'] += 1
                if c_type == 'be_max' and c_status == 'complete':
                    partner_loi_map[partner_id][loi]['be_max_count'] += 1
                if c_type == 'commitment' and c_status == 'complete':
                    partner_loi_map[partner_id][loi]['commitment_count'] += 1
                if c_status == 'complete':
                    partner_loi_map[partner_id][loi]['complete_count'] += 1

        # Build the final structure and compute status
        partner_objs = []
        summary_counts = {'complete': 0, 'partial': 0, 'not_started': 0}
        for partner in partners:
            partner_id = partner['partner_id']
            partner_name = partner['partner_name']
            lois_arr = []
            for loi in lois:
                loi_obj = {
                    'loi': loi,
                    'status': 'not started',
                    'updated_at': None,
                    'be_max_count': 0,
                    'commitment_count': 0,
                    'complete_count': 0,
                    'total_count': 0,
                    'audiences': []
                }
                if partner_id in partner_loi_map and loi in partner_loi_map[
                        partner_id]:
                    loi_data = partner_loi_map[partner_id][loi]
                    loi_obj['updated_at'] = loi_data['updated_at']
                    loi_obj['be_max_count'] = loi_data['be_max_count']
                    loi_obj['commitment_count'] = loi_data['commitment_count']
                    loi_obj['complete_count'] = loi_data['complete_count']
                    loi_obj['total_count'] = loi_data['total_count']
                    # Add audiences
                    for aud in audiences:
                        aud_id = aud['id']
                        aud_obj = {
                            'audience_name': aud['audience_name'],
                            'countries': []
                        }
                        if aud_id in loi_data['audiences']:
                            for cc in loi_data['audiences'][aud_id][
                                    'countries']:
                                aud_obj['countries'].append(cc)
                        loi_obj['audiences'].append(aud_obj)
                    # Compute status
                    if loi_obj['total_count'] > 0 and loi_obj[
                            'complete_count'] == loi_obj['total_count']:
                        loi_obj['status'] = 'complete'
                    elif loi_obj['complete_count'] > 0:
                        loi_obj['status'] = 'partial'
                    else:
                        loi_obj['status'] = 'not started'
                else:
                    # No data for this partner/loi, but still show audiences/countries
                    for aud in audiences:
                        aud_id = aud['id']
                        aud_obj = {
                            'audience_name': aud['audience_name'],
                            'countries': []
                        }
                        loi_obj['audiences'].append(aud_obj)
                lois_arr.append(loi_obj)
            # For summary: if any LOI is complete, count as complete; else if any partial, count as partial; else not started
            partner_statuses = [l['status'] for l in lois_arr]
            if 'complete' in partner_statuses:
                summary_counts['complete'] += 1
            elif 'partial' in partner_statuses:
                summary_counts['partial'] += 1
            else:
                summary_counts['not_started'] += 1
            partner_objs.append({
                'partner_id': partner_id,
                'partner_name': partner_name,
                'lois': lois_arr
            })

        cur.close()
        conn.close()
        return jsonify({
            'bid_number': bid['bid_number'],
            'study_name': bid['study_name'],
            'lois': lois,
            'partners': partner_objs,
            'summary_counts': summary_counts
        })
    except Exception as e:
        print(f"Error in get_partner_responses_summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/proposals', methods=['GET'])
def list_proposals():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            p.id as proposal_id,
            p.bid_id,
            b.bid_number,
            b.study_name,
            b.methodology,
            c.client_name,
            p.data->'data'->'summary'->>'totalCost' as total_cost,
            p.data->'data'->'summary'->>'totalRevenue' as total_revenue,
            p.data->'data'->'summary'->>'totalMargin' as total_margin,
            p.data->'data'->'summary'->>'effectiveMargin' as effective_margin,
            p.data->'data'->'summary'->>'avgCPI' as avg_cpi,
            p.created_at
        FROM proposals p
        JOIN bids b ON p.bid_id = b.id
        LEFT JOIN clients c ON b.client = c.id
        ORDER BY p.created_at DESC
    """)
    proposals = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(proposals)


@app.route('/api/proposals', methods=['POST'])
def create_proposal():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Insert new proposal
        cur.execute(
            """
            INSERT INTO proposals (bid_id, data)
            VALUES (%s, %s)
            RETURNING id
        """, (data['bid_id'], json.dumps(data)))

        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'id': new_id,
            'message': 'Proposal created successfully'
        }), 201

    except Exception as e:
        print(f"Error in create_proposal: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/proposals/<int:proposal_id>', methods=['PUT'])
def update_proposal(proposal_id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Update proposal with entire proposal data
        cur.execute(
            """
            UPDATE proposals 
            SET data = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, data
        """, (json.dumps({
                'bid_id': data.get('bid_id'),
                'data': data.get('data', {})
            }), proposal_id))

        updated = cur.fetchone()
        if not updated:
            return jsonify({"error": "Proposal not found"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'id': updated['id'],
            'data': updated['data'],
            'message': 'Proposal updated successfully'
        })

    except Exception as e:
        print(f"Error in update_proposal: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/proposals/<int:proposal_id>', methods=['GET'])
def get_proposal(proposal_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, bid_id, data FROM proposals WHERE id = %s',
                (proposal_id, ))
    proposal = cur.fetchone()
    cur.close()
    conn.close()
    if not proposal:
        return jsonify({'error': 'Proposal not found'}), 404
    return jsonify(proposal)


@app.route('/api/bids/<int:bid_id>/partners', methods=['GET'])
def get_bid_partners(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT DISTINCT p.id, p.partner_name
            FROM partners p
            JOIN partner_responses pr ON pr.partner_id = p.id
            WHERE pr.bid_id = %s
            ORDER BY p.partner_name
        """, (bid_id, ))
        partners = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(partners)
    except Exception as e:
        print(f"Error fetching partners for bid: {str(e)}")
        return jsonify([]), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return {'error': 'Not found'}, 404

    dist_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'dist'))

    try:
        # First try to serve the exact file if it exists
        if path and os.path.exists(os.path.join(dist_dir, path)):
            if path.endswith(('.js', '.css')):
                return send_from_directory(
                    dist_dir,
                    path,
                    mimetype='text/javascript'
                    if path.endswith('.js') else 'text/css')
            return send_from_directory(dist_dir, path)

        # If file not found, serve index.html for client-side routing
        if not os.path.exists(os.path.join(dist_dir, 'index.html')):
            print("Frontend not built. Building...")
            return "Frontend not built. Run 'npm run build' first.", 500

        return send_from_directory(dist_dir, 'index.html')
    except Exception as e:
        print(f"Error serving React app: {str(e)}")
        return "Internal server error", 500


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


# Move app.run to the end after all routes are defined
if __name__ == '__main__':
    try:
        print("Starting server on port 5000...")
        from waitress import serve
        serve(app,
              host='0.0.0.0',
              port=5000,
              threads=6,
              connection_limit=1000,
              cleanup_interval=8,
              channel_timeout=300,
              url_scheme='https')
    except Exception as e:
        print(f"Error starting server: {str(e)}")