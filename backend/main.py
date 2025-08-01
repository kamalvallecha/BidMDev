import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from config import Config
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import json
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
from constants import ROLES_AND_PERMISSIONS
import uuid
import secrets
from flask_mail import Message, Mail
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from urllib.parse import urlsplit, urlunsplit


# --- Custom JSON Encoder must be defined before app = Flask(__name__) ---
class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'strftime'):  # Handle date objects
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)


# Define frontend URL as a constant
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3001')

# Initialize Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
CORS(app,
     resources={
         r"/api/*": {
             "origins": ["*"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": [
                 "Content-Type", "Authorization", "X-User-Id", "X-User-Team",
                 "X-User-Role", "X-User-Name"
             ],
             "supports_credentials":
             True,
             "expose_headers": ["Content-Type", "Authorization"]
         }
     })

# Configure Flask-Mail
# WARNING: Storing credentials directly in the code is a security risk.
# It is highly recommended to use environment variables for sensitive data.
#app.config['MAIL_SERVER'] = 'smtp.gmail.com'
#app.config['MAIL_PORT'] = 587
#app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USERNAME'] = 'kamalvallecha@gmail.com'
#app.config['MAIL_PASSWORD'] = 'slcwiktxtfgfcpkg'
#app.config['MAIL_DEFAULT_SENDER'] = 'kamal.vallecha@c5i.ai'

app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Microsoft 365 SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv(
    'MAIL_USERNAME')  # Your Microsoft 365 email
app.config['MAIL_PASSWORD'] = os.getenv(
    'MAIL_PASSWORD')  # Your Microsoft 365 password or app password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
app.config['FRONTEND_BASE_URL'] = os.getenv('FRONTEND_BASE_URL',
                                            'http://localhost:5173')

# Initialize Flask-Mail
mail = Mail(app)

# Initialize the scheduler
scheduler = BackgroundScheduler()

ADMIN_NOTIFICATION_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL')

print('MAIL_USERNAME:', os.getenv('MAIL_USERNAME'))
print('ADMIN_NOTIFICATION_EMAIL:', os.getenv('ADMIN_NOTIFICATION_EMAIL'))


def check_expiring_links():
    with app.app_context():
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
                    msg = Message(
                        'Your Partner Response Link is Expiring Soon',
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[link['contact_email']])

                    base_url = os.getenv('FRONTEND_BASE_URL',
                                         'http://localhost:3000')
                    # Note: request object not available in background scheduler context
                    # if 'replit.dev' in request.host or 'repl.co' in request.host:
                    #     base_url = f"https://{request.host.split(':')[0]}"
                    link_url = f"{base_url}/partner-response/{link['token']}"

                    msg.body = f"""
                    Dear {link['partner_name']},

                    Your access link for bid {link['bid_number']} ({link['study_name']}) will expire in 3 days.

                    Current Link: {link_url}
                    Expiry Date: {link['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}

                    Please complete your response before the link expires. If you need more time, please contact the bid manager.

                    Best regards,
                    Bid Management Team
                    """

                    #mail.send(msg)

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


def send_daily_access_request_digest():
    """Send daily digest of pending access requests to admins"""
    with app.app_context():
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get all pending access requests
            cur.execute("""
                SELECT 
                    bar.id,
                    bar.bid_id,
                    bar.user_id,
                    bar.team,
                    bar.requested_on,
                    b.bid_number,
                    b.study_name,
                    u.email as requester_email,
                    u.name as requester_name,
                    owner.email as owner_email,
                    owner.name as owner_name
                FROM bid_access_requests bar
                JOIN bids b ON bar.bid_id = b.id
                LEFT JOIN users u ON bar.user_id = u.id
                LEFT JOIN users owner ON b.created_by = owner.id
                WHERE bar.status = 'pending'
                ORDER BY bar.requested_on DESC
            """)

            pending_requests = cur.fetchall()

            if not pending_requests:
                print("No pending access requests found for daily digest")
                cur.close()
                conn.close()
                return

            # Get all admin users
            cur.execute("""
                SELECT email, name 
                FROM users 
                WHERE role IN ('admin', 'super_admin')
            """)
            admin_users = cur.fetchall()

            # Send only to designated admin notification email
            recipients = []
            if ADMIN_NOTIFICATION_EMAIL:
                recipients.append(ADMIN_NOTIFICATION_EMAIL)

            if not recipients:
                print("No admin recipients found for daily digest")
                cur.close()
                conn.close()
                return

            # Create HTML table for requests
            table_html = '''
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #1976d2; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Bid #</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Study Name</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Requester</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Team</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Requested On</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Bid Owner</th>
                </tr>
            '''
            
            for req in pending_requests:
                table_html += f'''
                <tr style="{'background-color: #f8f9fa;' if pending_requests.index(req) % 2 == 0 else ''}">
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['bid_number']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['study_name'][:50]}{'...' if len(req['study_name']) > 50 else ''}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['requester_name'] or 'Unknown'}<br><small>{req['requester_email'] or 'No email'}</small></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['team']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['requested_on'].strftime('%Y-%m-%d %H:%M')}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{req['owner_name'] or 'Unknown'}<br><small>{req['owner_email'] or 'No email'}</small></td>
                </tr>
                '''
            
            table_html += '</table>'

            # Send digest email
            base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
            
            msg = Message(
                f'📊 Daily Digest: {len(pending_requests)} Pending Bid Access Requests',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=recipients
            )

            msg.body = f"""
Daily Bid Access Request Digest

Total Pending Requests: {len(pending_requests)}

Please log into the bid management system to review and approve/deny these requests.

Access the system: {base_url}

This is an automated daily digest sent every morning at 9 AM.

Best regards,
Bid Management System
            """

            msg.html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #1976d2; margin-bottom: 20px;">📊 Daily Bid Access Request Digest</h2>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <strong>Summary:</strong> You have {len(pending_requests)} pending bid access requests that require your attention.
                </div>
                
                <h3 style="color: #333; margin-bottom: 15px;">Pending Requests:</h3>
                {table_html}
                
                <div style="background-color: #e3f2fd; border: 1px solid #90caf9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin-bottom: 10px;">Action Required:</h3>
                    <p style="margin: 0;">Please log into the bid management system to review and approve/deny these requests.</p>
                </div>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{base_url}" style="background-color: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Access Bid Management System
                    </a>
                </div>
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666; margin: 0;">
                    This is an automated daily digest sent every morning at 9 AM. Please do not reply to this email.
                </p>
            </div>
            """

            mail.send(msg)
            print(f"Daily digest sent to {len(recipients)} recipients for {len(pending_requests)} pending requests")

            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error sending daily digest: {str(e)}")
            import traceback
            print(f"Daily digest error traceback: {traceback.format_exc()}")
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

# Schedule daily digest at 9 AM
scheduler.add_job(send_daily_access_request_digest,
                  CronTrigger(hour=9, minute=0),
                  id='daily_access_request_digest',
                  replace_existing=True)

# Start the scheduler when the app starts
scheduler.start()


def get_db_connection():
    """Return PostgreSQL database connection"""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            raise Exception("DATABASE_URL environment variable not set")

        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        print(
            f"Available environment variables: DATABASE_URL={'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}"
        )
        print(f"PGHOST={os.getenv('PGHOST', 'NOT SET')}")
        print(f"PGDATABASE={os.getenv('PGDATABASE', 'NOT SET')}")
        print(f"PGUSER={os.getenv('PGUSER', 'NOT SET')}")
        print(f"PGPORT={os.getenv('PGPORT', 'NOT SET')}")
        raise e


def init_postgresql_db():
    """Initialize PostgreSQL database with default data"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if admin user exists, if not create one, or update existing one with correct hash
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'")
        if cur.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('admin',
                                                   method='pbkdf2:sha256')

            cur.execute(
                """
                INSERT INTO users (email, name, password_hash, role, team, employee_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, ('admin@example.com', 'Admin User', password_hash, 'admin',
                  'Operations', 'EMP001'))
            print("Default admin user created")
        else:
            # Update existing admin user with correct password hash
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('admin',
                                                   method='pbkdf2:sha256')
            cur.execute(
                """
                UPDATE users SET password_hash = %s WHERE email = 'admin@example.com'
            """, (password_hash, ))
            print("Admin user password hash updated")

        # Verify the admin user has the correct password hash format
        cur.execute(
            "SELECT password_hash FROM users WHERE email = 'admin@example.com'"
        )
        current_hash = cur.fetchone()
        if current_hash and not current_hash[0].startswith('pbkdf2:sha256'):
            print("Admin password hash needs updating to pbkdf2 format")
            new_hash = generate_password_hash('admin', method='pbkdf2:sha256')
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE email = 'admin@example.com'",
                (new_hash, ))
            print("Admin password hash updated to pbkdf2 format")

        # Check and create sample data if tables are empty
        cur.execute("SELECT COUNT(*) FROM clients")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO clients (client_id, client_name, contact_person, email, phone, country, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, ('CLIENT001', 'Sample Client Inc', 'John Doe',
                  'john@sampleclient.com', '+1-555-0123', 'USA'))
            print("Sample client data created")

        cur.execute("SELECT COUNT(*) FROM vendor_managers")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO vendor_managers (vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, ('VM001', 'Sample VM', 'Jane Smith', 'Bob Manager',
                  'Operations'))
            print("Sample VM data created")

        cur.execute("SELECT COUNT(*) FROM sales")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO sales (sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, ('SALES001', 'Mike Sales', 'Mike Contact', 'Sales Manager',
                  'north'))
            print("Sample sales data created")

        conn.commit()
        cur.close()
        conn.close()
        print("PostgreSQL database initialization completed")
    except Exception as e:
        print(f"Error initializing PostgreSQL database: {str(e)}")
        raise e


@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    try:
        if request.method == 'GET':
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT id, email, name, employee_id, role, team, created_at, updated_at
                FROM users ORDER BY id
            """)

            users = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify(users)

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

            conn = get_db_connection()
            cur = conn.cursor()

            # Check if email already exists
            cur.execute('SELECT id FROM users WHERE email = %s',
                        (data['email'], ))
            if cur.fetchone():
                return jsonify({"error": "Email already exists"}), 400

            # Create new user
            cur.execute(
                """
                INSERT INTO users (email, name, employee_id, password_hash, role, team, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """, (data['email'], data['name'], data.get('employee_id'),
                  password_hash, data['role'], data['team']))

            new_user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            return jsonify({
                'id': new_user_id,
                'message': 'User created successfully'
            }), 201

    except Exception as e:
        print(f"Error handling users: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vms', methods=['GET'])
def get_vms():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at
            FROM vendor_managers ORDER BY id
        """)

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
        print("Received VM data:", data)

        required_fields = [
            'vm_id', 'vm_name', 'contact_person', 'reporting_manager', 'team'
        ]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"error":
                                f"Field {field} cannot be empty"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if VM ID already exists
        cur.execute('SELECT id FROM vendor_managers WHERE vm_id = %s',
                    (data['vm_id'], ))
        if cur.fetchone():
            return jsonify({"error": "VM ID already exists"}), 400

        # Create new VM
        cur.execute(
            """
            INSERT INTO vendor_managers (vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """, (data['vm_id'], data['vm_name'], data['contact_person'],
              data['reporting_manager'], data['team']))

        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": new_id,
            "message": "VM created successfully"
        }), 201

    except Exception as e:
        print(f"Error creating VM: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/sales', methods=['GET'])
def get_sales():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at
            FROM sales ORDER BY id
        """)

        sales_list = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(sales_list)
    except Exception as e:
        print(f"Error in get_sales: {str(e)}")
        return jsonify({"error": str(e)}), 500


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

        cur.execute("""
            SELECT id, partner_id, partner_name, contact_person, contact_email, contact_phone, 
                   website, company_address, specialized, geographic_coverage, created_at, updated_at
            FROM partners ORDER BY id
        """)

        partners_list = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(partners_list)
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
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, client_id, client_name, contact_person, email, phone, country, created_at, updated_at
            FROM clients ORDER BY id
        """)

        clients_list = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(clients_list)
    except Exception as e:
        print(f"Error in get_clients: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        offset = (page - 1) * page_size
        search = request.args.get('search', '').strip().lower()

        # Get user info from headers
        user_id = request.headers.get('X-User-Id')
        user_team = request.headers.get('X-User-Team')
        user_role = (request.headers.get('X-User-Role') or '').lower()
        user_name = (request.headers.get('X-User-Name') or '').lower()

        # Debug: Print incoming user info
        print("/api/bids DEBUG: Incoming user info:")
        print(f"  user_id: {user_id}")
        print(f"  user_team: {user_team}")
        print(f"  user_role: {user_role}")
        print(f"  user_name: {user_name}")

        # Super Admin logic: role is super_admin or Kamal by name
        is_super_admin = user_role == 'super_admin' or 'kamal vallecha' in user_name
        is_admin = user_role == 'admin'

        # Get bids from PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Debug: Check what's actually in the bid_access table
        cur.execute("SELECT * FROM bid_access")
        all_bid_access = cur.fetchall()
        print(f"DEBUG: All bid_access records: {all_bid_access}")

        cur.execute("""
            SELECT b.id, b.bid_number, b.study_name, b.bid_date, b.status, b.methodology, 
                   b.project_requirement, b.client, b.vm_contact, b.sales_contact, b.created_by,
                   c.client_name, vm.vm_name, vm.team, s.sales_person
            FROM bids b
            LEFT JOIN clients c ON b.client = c.id
            LEFT JOIN vendor_managers vm ON b.vm_contact = vm.id
            LEFT JOIN sales s ON b.sales_contact = s.id
        """)

        bids_raw = cur.fetchall()

        # Convert to the expected format
        bids_data = {}
        for bid in bids_raw:
            bids_data[str(bid['id'])] = {
                'id': bid['id'],
                'bid_number': bid['bid_number'],
                'study_name': bid['study_name'],
                'bid_date': bid['bid_date'],
                'status': bid['status'],
                'methodology': bid['methodology'],
                'project_requirement': bid['project_requirement'],
                'client': bid['client'],
                'vm_contact': bid['vm_contact'],
                'sales_contact': bid['sales_contact'],
                'created_by': bid['created_by']
            }

        clients_data = {}
        vm_data = {}
        sales_data = {}

        # Get clients data
        cur.execute("SELECT id, client_name FROM clients")
        for client in cur.fetchall():
            clients_data[str(client['id'])] = {
                'client_name': client['client_name']
            }

        # Get VM data
        cur.execute("SELECT id, vm_name, team FROM vendor_managers")
        for vm in cur.fetchall():
            vm_data[str(vm['id'])] = {
                'vm_name': vm['vm_name'],
                'team': vm['team']
            }

        # Get sales data
        cur.execute("SELECT id, sales_person FROM sales")
        for sales in cur.fetchall():
            sales_data[str(sales['id'])] = {
                'sales_person': sales['sales_person']
            }

        print(f"DEBUG: Found {len(bids_data)} bids in database")
        print(f"DEBUG: Found {len(clients_data)} clients in database")
        print(f"DEBUG: Found {len(vm_data)} VMs in database")

        # Convert to list format
        all_bids = []
        for bid_id, bid in bids_data.items():
            # Get client name
            client_name = 'Unknown Client'
            if bid.get('client'):
                client_id = str(bid['client'])
                if client_id in clients_data:
                    client_name = clients_data[client_id].get(
                        'client_name', 'Unknown Client')

            # Get VM team and name
            vm_team = 'Unknown Team'
            vm_name = 'Unknown VM'
            if bid.get('vm_contact'):
                vm_id = str(bid['vm_contact'])
                if vm_id in vm_data:
                    vm_team = vm_data[vm_id].get('team', 'Unknown Team')
                    vm_name = vm_data[vm_id].get('vm_name', 'Unknown VM')

            # Get sales person
            sales_person = 'Unknown Sales'
            if bid.get('sales_contact'):
                sales_id = str(bid['sales_contact'])
                if sales_id in sales_data:
                    sales_person = sales_data[sales_id].get(
                        'sales_person', 'Unknown Sales')

            # Convert date to string if it exists
            bid_date = bid.get('bid_date')
            if bid_date and hasattr(bid_date, 'strftime'):
                bid_date = bid_date.strftime('%Y-%m-%d')
            elif bid_date and hasattr(bid_date, 'isoformat'):
                bid_date = bid_date.isoformat()

            bid_obj = {
                'id': bid.get('id'),
                'bid_number': bid.get('bid_number'),
                'study_name': bid.get('study_name'),
                'bid_date': bid_date,
                'status': bid.get('status', 'draft'),
                'client_name': client_name,
                'methodology': bid.get('methodology'),
                'project_requirement': bid.get('project_requirement'),
                'team': vm_team,
                'vm_name': vm_name,
                'sales_person': sales_person,
                'created_by': bid.get('created_by')
            }
            all_bids.append(bid_obj)

        # Get explicitly granted access for this user/team before closing connection
        # Check for both user-specific and team-specific grants
        cur.execute(
            """
            SELECT DISTINCT bid_id FROM bid_access 
            WHERE (user_id = %s) OR (team = %s)
            """, (user_id, user_team))
        granted_bid_ids = set(row['bid_id'] for row in cur.fetchall())
        print(
            f"DEBUG: Found explicitly granted access for bid IDs: {granted_bid_ids}"
        )

        # Debug: Show all access records for this user/team
        cur.execute(
            """
            SELECT bid_id, user_id, team FROM bid_access 
            WHERE (user_id = %s) OR (team = %s)
            """, (user_id, user_team))
        all_access_records = cur.fetchall()
        print(
            f"DEBUG: All access records for user {user_id}/{user_team}: {all_access_records}"
        )

        cur.close()
        conn.close()

        # Apply access control filters
        filtered_bids = []
        for bid in all_bids:
            # Check access
            has_access = False

            # Super admin and Kamal (by name) can see all bids
            if is_super_admin:
                has_access = True
                print(
                    f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} - Super admin access"
                )
            # Check for explicitly granted access in bid_access table (this should take precedence)
            elif bid.get('id') in granted_bid_ids:
                has_access = True
                print(
                    f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} has explicitly granted access"
                )
            # Bid creator can always see their own bids
            elif str(bid.get('created_by')) == str(user_id):
                has_access = True
                print(
                    f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} - Bid creator access"
                )
            # Team-based access: only if user's team matches bid's team
            elif user_team and bid.get('team'):
                # Normalize team names for comparison (remove spaces, convert to lowercase)
                user_team_norm = user_team.replace(' ', '').lower()
                bid_team_norm = bid['team'].replace(' ', '').lower()
                print(
                    f"DEBUG: Team access check - User team: '{user_team_norm}', Bid team: '{bid_team_norm}'"
                )
                if user_team_norm == bid_team_norm:
                    has_access = True
                    print(
                        f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} - Team access granted"
                    )

            if not has_access:
                print(
                    f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} - No access found. Bid ID: {bid.get('id')}, Granted IDs: {granted_bid_ids}"
                )

            print(
                f"DEBUG: Bid {bid.get('bid_number')} - User: {user_name} (Team: {user_team}) - Has access: {has_access}"
            )

            if has_access:
                # Apply search filter
                if search:
                    search_fields = [
                        str(bid.get('bid_number', '')).lower(),
                        str(bid.get('study_name', '')).lower(),
                        str(bid.get('client_name', '')).lower()
                    ]
                    if any(search in field for field in search_fields):
                        filtered_bids.append(bid)
                else:
                    filtered_bids.append(bid)

        # Sort by bid number (descending)
        filtered_bids.sort(key=lambda x: int(x.get('bid_number', 0) or 0),
                           reverse=True)

        # Apply pagination
        total = len(filtered_bids)
        paginated_bids = filtered_bids[offset:offset + page_size]

        print(f"/api/bids DEBUG: Number of bids found: {len(paginated_bids)}")
        print(f"/api/bids DEBUG: Total bids after filtering: {total}")

        return jsonify({
            'bids': paginated_bids,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        print(f"Error in get_bids: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bids', methods=['POST'])
def create_bid():
    try:
        data = request.json
        # Always enforce team and created_by from headers
        user_id = request.headers.get('X-User-Id')
        user_team = request.headers.get('X-User-Team')
        if not user_id or not user_team:
            return jsonify({'error':
                            'Missing user ID or team in headers'}), 400
        # Use only backend-determined values
        data['created_by'] = user_id
        data['team'] = user_team
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

        # Check if bid number already exists
        cur.execute('SELECT id FROM bids WHERE bid_number = %s',
                    (data['bid_number'], ))
        if cur.fetchone():
            return jsonify({
                "error":
                "Bid number already exists. Please choose a different number."
            }), 400

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
                created_by,
                team,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft', %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (data['bid_number'], data['bid_date'], data['study_name'],
              data['methodology'], data['sales_contact'], data['vm_contact'],
              data['client'], data['project_requirement'], data['created_by'],
              data['team']))

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


@app.route('/api/bids/pending-requests', methods=['GET'])
def get_pending_requests_batch():
    try:
        bid_ids_param = request.args.get('bid_ids', '')
        if not bid_ids_param:
            return jsonify({})
        bid_ids = [
            int(bid_id) for bid_id in bid_ids_param.split(',')
            if bid_id.isdigit()
        ]
        if not bid_ids:
            return jsonify({})
        conn = get_db_connection()
        cur = conn.cursor()
        # Query for all pending requests for these bids
        cur.execute(
            '''
            SELECT bid_id, COUNT(*) as pending_count
            FROM bid_access_requests
            WHERE bid_id = ANY(%s) AND status = 'pending'
            GROUP BY bid_id
        ''', (bid_ids, ))
        result = {str(row[0]): row[1] for row in cur.fetchall()}
        # Fill in 0 for bids with no pending requests
        for bid_id in bid_ids:
            if str(bid_id) not in result:
                result[str(bid_id)] = 0
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_pending_requests_batch: {str(e)}")
        return jsonify({})


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
                print(
                    f"Found audience ID {row['id']} with name '{row['name']}'")

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
                print(
                    f"Created audience object for ID {audience_id}: {row['name']}"
                )
            if row['country']:
                target_audiences[audience_id]['country_samples'][
                    row['country']] = {
                        'sample_size': row['sample_size'],
                        'is_best_efforts': row['country_is_best_efforts']
                    }
                print(
                    f"Added country sample: audience {audience_id}, country {row['country']}, size {row['sample_size']}"
                )

        # Sort audiences by ID to maintain consistent database order, then renumber sequentially
        sorted_audiences = sorted(target_audiences.values(),
                                  key=lambda x: x['id'])

        # Renumber audiences sequentially based on their sorted database ID order
        for index, audience in enumerate(sorted_audiences):
            audience['name'] = f"Audience - {index + 1}"
            audience['uniqueId'] = f"audience-{index}"

        print(
            f"Final sorted audience order after renumbering: {[f'ID:{a['id']}-{a['name']}' for a in sorted_audiences]}"
        )
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

        lois = list(set([r['loi']
                         for r in partner_lois])) if partner_lois else []

        response = {
            **bid, 'target_audiences': sorted_audiences,
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
        existing_audience_ids = [row[0] for row in cur.fetchall()]
        print("Existing audience IDs:", existing_audience_ids)

        # 3. Handle deleted audiences first
        deleted_audience_ids = data.get('deleted_audience_ids', [])
        if deleted_audience_ids:
            print(f"Deleting audiences with IDs: {deleted_audience_ids}")
            # Delete partner audience responses first (foreign key constraint)
            cur.execute("""
                DELETE FROM partner_audience_responses 
                WHERE audience_id = ANY(%s) AND bid_id = %s
            """, (deleted_audience_ids, bid_id))
            
            # Delete audience countries
            cur.execute("""
                DELETE FROM bid_audience_countries 
                WHERE audience_id = ANY(%s)
            """, (deleted_audience_ids,))
            
            # Delete the audiences themselves
            cur.execute("""
                DELETE FROM bid_target_audiences 
                WHERE id = ANY(%s) AND bid_id = %s
            """, (deleted_audience_ids, bid_id))

        # 4. Update or insert target audiences
        updated_audience_ids = set()  # Track which audience IDs have been updated
        for idx, audience in enumerate(data['target_audiences']):
            print(f"Processing audience {idx}: {audience}")
            if idx < len(existing_audience_ids):
                # Update existing audience
                audience_id = existing_audience_ids[idx]
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
                     audience.get(
                         'comments', ''), audience.get(
                             'is_best_efforts', False), audience_id, bid_id))
                print(f"Updated audience ID: {audience_id}")
                updated_audience_ids.add(audience_id)
            else:
                # Insert new audience (either no ID, doesn't exist, or is a duplicate)
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
                     audience.get('comments',
                                  ''), audience.get('is_best_efforts', False)))
                audience_id = cur.fetchone()[0]
                existing_audience_ids.append(audience_id)
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
                    f"Deleted old country samples for audience ID: {audience_id}"
                )

                # Then insert new country samples
                for country, sample_data in audience['country_samples'].items(
                ):
                    try:
                        print(
                            f"Inserting country {country} with sample data {sample_data}"
                        )
                        # Handle both dictionary and direct integer values
                        if isinstance(sample_data, dict):
                            sample_size = sample_data.get('sample_size', 0)
                            is_best_efforts = sample_data.get(
                                'is_best_efforts', False)
                        else:
                            # For backward compatibility
                            sample_size = sample_data
                            is_best_efforts = sample_size == 0 and audience.get(
                                'is_best_efforts', False)

                        # Check if record already exists (despite the DELETE)
                        cur.execute(
                            """
                            SELECT 1 FROM bid_audience_countries 
                            WHERE bid_id = %s AND audience_id = %s AND country = %s
                        """, (bid_id, audience_id, country))

                        exists = cur.fetchone()
                        if exists:
                            # Update existing record
                            print(
                                f"Country record exists, updating: {country}")
                            cur.execute(
                                """
                                UPDATE bid_audience_countries
                                SET sample_size = %s,
                                    is_best_efforts = %s
                                WHERE bid_id = %s AND audience_id = %s AND country = %s
                            """, (int(sample_size), is_best_efforts, bid_id,
                                  audience_id, country))
                        else:
                            # Insert new record
                            print(
                                f"Country record does not exist, inserting: {country}"
                            )
                            cur.execute(
                                """
                                INSERT INTO bid_audience_countries (
                                    bid_id, audience_id, country, sample_size, is_best_efforts
                                ) VALUES (%s, %s, %s, %s, %s)
                            """, (bid_id, audience_id, country,
                                  int(sample_size), is_best_efforts))
                        print(f"Successfully processed country {country}")
                    except Exception as country_error:
                        print(
                            f"Error processing country {country}: {str(country_error)}"
                        )
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
        print(f"Error getting partner responses: {str(e)}")
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

        # Modified query to correctly calculate total N-delivered and quality rejects
        cur.execute("""
            WITH metrics AS (
                SELECT 
                    pr.bid_id,
                    SUM(COALESCE(par.n_delivered, 0)) as total_delivered,
                    SUM(COALESCE(par.quality_rejects, 0)) as total_rejects,
                    CASE 
                        WHEN COUNT(par.final_loi) > 0 THEN AVG(par.final_loi)
                        ELSE AVG(COALESCE(par.final_loi, 0))
                    END as avg_loi,
                    CASE 
                        WHEN COUNT(par.final_ir) > 0 THEN AVG(par.final_ir)
                        ELSE AVG(COALESCE(par.final_ir, 0))
                    END as avg_ir
                FROM partner_responses pr
                JOIN partner_audience_responses par ON par.partner_response_id = pr.id
                WHERE par.allocation > 0 AND par.n_delivered > 0
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
        # Return empty string to indicate manual entry is required
        return jsonify({"next_bid_number": ""})
    except Exception as e:
        print(f"Error getting next bid number: {str(e)}")
        return jsonify({"error": str(e)}), 500


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

        # Get bids data from PostgreSQL with user team information
        cur.execute("""
            SELECT b.id, b.status, b.client, b.created_by, u.team 
            FROM bids b
            LEFT JOIN users u ON b.created_by = u.id
        """)
        bids_data = cur.fetchall()

        # Get clients data from PostgreSQL
        cur.execute("SELECT id, client_name FROM clients")
        clients_data = {str(client['id']): client for client in cur.fetchall()}

        # Calculate dashboard metrics
        total_bids = len(bids_data)

        # Count by status
        status_counts = {
            "Draft": 0,
            "Partner Response": 0,
            "In Field": 0,
            "Closure": 0,
            "Ready to Invoice": 0,
            "Completed": 0,
            "Rejected": 0
        }

        active_statuses = ['draft', 'partner_response', 'infield', 'closure']
        active_bids = 0

        for bid in bids_data:
            status = bid.get('status', 'draft').lower()

            # Map status to display names
            if status == 'draft':
                status_counts["Draft"] += 1
            elif status in ['partner_response', 'pending']:
                status_counts["Partner Response"] += 1
            elif status == 'infield':
                status_counts["In Field"] += 1
            elif status == 'closure':
                status_counts["Closure"] += 1
            elif status in ['ready_for_invoice', 'invoiced']:
                status_counts["Ready to Invoice"] += 1
            elif status == 'completed':
                status_counts["Completed"] += 1
            elif status == 'rejected':
                status_counts["Rejected"] += 1

            if status in active_statuses:
                active_bids += 1

        # Create detailed client summary with status breakdown
        client_summary = []
        client_metrics = {}

        # Process each bid to calculate client metrics
        for bid in bids_data:
            client_id = str(bid.get('client', '')) if bid.get('client') else 'unknown'
            status = bid.get('status', 'draft').lower()
            
            if client_id not in client_metrics:
                client_metrics[client_id] = {
                    'total_bids': 0,
                    'bids_in_field': 0,
                    'bid_closed': 0,
                    'bid_invoiced': 0,
                    'bids_rejected': 0,
                    'total_amount': 0,
                    'closed_bids': 0  # For conversion rate calculation
                }
            
            client_metrics[client_id]['total_bids'] += 1
            
            # Count by status
            if status == 'infield':
                client_metrics[client_id]['bids_in_field'] += 1
            elif status in ['closure', 'completed']:
                client_metrics[client_id]['bid_closed'] += 1
                client_metrics[client_id]['closed_bids'] += 1
            elif status in ['ready_for_invoice', 'invoiced']:
                client_metrics[client_id]['bid_invoiced'] += 1
                client_metrics[client_id]['closed_bids'] += 1
            elif status == 'rejected':
                client_metrics[client_id]['bids_rejected'] += 1

        # Get invoice amounts for clients (simplified - you may need to adjust based on your invoice structure)
        cur.execute("""
            SELECT 
                b.client,
                SUM(COALESCE(pr.invoice_amount, 0)) as total_amount
            FROM bids b
            LEFT JOIN partner_responses pr ON b.id = pr.bid_id
            WHERE pr.invoice_amount IS NOT NULL AND pr.invoice_amount > 0
            GROUP BY b.client
        """)
        
        invoice_amounts = {}
        for row in cur.fetchall():
            if row['client']:
                invoice_amounts[str(row['client'])] = float(row['total_amount'] or 0)

        # Build final client summary
        for client_id, metrics in client_metrics.items():
            client_name = 'Unknown Client'
            if client_id in clients_data:
                client_name = clients_data[client_id].get('client_name', 'Unknown Client')
            
            # Calculate conversion rate
            conversion_rate = 0
            if metrics['total_bids'] > 0:
                conversion_rate = round((metrics['closed_bids'] / metrics['total_bids']) * 100, 2)
            
            client_summary.append({
                'client_name': client_name,
                'total_bids': metrics['total_bids'],
                'bids_in_field': metrics['bids_in_field'],
                'bid_closed': metrics['bid_closed'],
                'bid_invoiced': metrics['bid_invoiced'],
                'bids_rejected': metrics['bids_rejected'],
                'total_amount': invoice_amounts.get(client_id, 0),
                'conversion_rate': conversion_rate
            })

        # Sort by total_bids descending
        client_summary.sort(key=lambda x: x['total_bids'], reverse=True)

        # Calculate team statistics
        team_summary = []
        team_metrics = {}

        # Process each bid to calculate team metrics
        for bid in bids_data:
            team = bid.get('team', 'Unknown Team') if bid.get('team') else 'Unknown Team'
            status = bid.get('status', 'draft').lower()
            
            if team not in team_metrics:
                team_metrics[team] = {
                    'total_bids': 0,
                    'bids_in_field': 0,
                    'bids_closed': 0,
                    'bids_invoiced': 0
                }
            
            team_metrics[team]['total_bids'] += 1
            
            # Count by status
            if status == 'infield':
                team_metrics[team]['bids_in_field'] += 1
            elif status in ['closure', 'completed']:
                team_metrics[team]['bids_closed'] += 1
            elif status in ['ready_for_invoice', 'invoiced']:
                team_metrics[team]['bids_invoiced'] += 1

        # Build final team summary
        for team, metrics in team_metrics.items():
            team_summary.append({
                'team': team,
                'total_bids': metrics['total_bids'],
                'bids_in_field': metrics['bids_in_field'],
                'bids_closed': metrics['bids_closed'],
                'bids_invoiced': metrics['bids_invoiced']
            })

        # Sort by total_bids descending
        team_summary.sort(key=lambda x: x['total_bids'], reverse=True)

        dashboard_data = {
            "total_bids": total_bids,
            "active_bids": active_bids,
            "total_savings": 0,  # TODO: Calculate from partner responses
            "avg_turnaround_time": 0,  # TODO: Calculate from bid dates
            "bids_by_status": status_counts,
            "client_summary": client_summary,
            "team_summary": team_summary
        }

        cur.close()
        conn.close()
        print(f"Sending dashboard data: {dashboard_data}")  # Debug log
        return jsonify(dashboard_data)

    except Exception as e:
        print(f"Error in dashboard endpoint: {str(e)}")  # Debug log
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
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
        print("Starting PostgreSQL database initialization...")

        # Initialize PostgreSQL database
        init_postgresql_db()

        print("PostgreSQL database initialization completed successfully")

    except Exception as e:
        print(f"Error initializing PostgreSQL database: {str(e)}")
        raise e


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


# These functions are not needed for Replit DB (key-value store)
def add_field_close_date_column():
    print("Skipping field_close_date column addition - using Replit DB")


def standardize_invoice_status():
    print("Skipping invoice status standardization - using Replit DB")


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

        # Start transaction
        cur.execute("BEGIN")

        print(f"Processing {len(responses)} partner responses for bid {bid_id}")

        # Batch process partner responses
        partner_response_ids = {}
        
        # First pass: Create or update all partner_responses
        for key, response_data in responses.items():
            partner_id = response_data.get('partner_id')
            loi = response_data.get('loi')

            if not partner_id or not loi:
                continue

            # Use ON CONFLICT to handle updates more efficiently
            cur.execute(
                """
                INSERT INTO partner_responses 
                (bid_id, partner_id, loi, status, currency, pmf, created_at, updated_at)
                VALUES (%s, %s, %s, 'draft', %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (bid_id, partner_id, loi) 
                DO UPDATE SET 
                    pmf = EXCLUDED.pmf,
                    currency = EXCLUDED.currency,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (bid_id, partner_id, loi,
                  response_data.get('currency', 'USD'), 
                  response_data.get('pmf', 0)))
            
            partner_response_id = cur.fetchone()['id']
            partner_response_ids[key] = partner_response_id

        # Second pass: Process audience responses in batches
        audience_updates = []
        audience_inserts = []

        for key, response_data in responses.items():
            partner_response_id = partner_response_ids.get(key)
            if not partner_response_id:
                continue

            audiences = response_data.get('audiences', {})
            for audience_key, audience_data in audiences.items():
                # Parse audience ID
                try:
                    if isinstance(audience_key, int) or (isinstance(audience_key, str) and audience_key.isdigit()):
                        audience_id = int(audience_key)
                    elif isinstance(audience_key, str) and audience_key.startswith('audience-'):
                        audience_id = int(audience_key.split('-')[1])
                    else:
                        continue
                except (IndexError, ValueError):
                    continue

                timeline = audience_data.get('timeline', 0)
                comments = audience_data.get('comments', '')

                # Process countries
                for country, country_data in audience_data.items():
                    if country in ('timeline', 'comments'):
                        continue

                    commitment = country_data.get('commitment', 0)
                    cpi = country_data.get('cpi', 0)
                    commitment_type = country_data.get('commitment_type', 'fixed')
                    is_best_efforts = commitment_type == 'be_max'

                    # Prepare data for batch processing
                    audience_data_tuple = (
                        bid_id, partner_response_id, audience_id, country,
                        commitment, cpi, timeline, comments, 
                        commitment_type, is_best_efforts
                    )
                    
                    # Check if exists first
                    cur.execute(
                        """
                        SELECT id FROM partner_audience_responses
                        WHERE partner_response_id = %s AND audience_id = %s AND country = %s
                    """, (partner_response_id, audience_id, country))
                    
                    if cur.fetchone():
                        audience_updates.append(audience_data_tuple)
                    else:
                        audience_inserts.append(audience_data_tuple)

        # Batch update existing audience responses
        if audience_updates:
            for update_data in audience_updates:
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
                    WHERE bid_id = %s AND partner_response_id = %s 
                    AND audience_id = %s AND country = %s
                """, (update_data[4], update_data[5], update_data[6], 
                      update_data[7], update_data[8], update_data[9],
                      update_data[0], update_data[1], update_data[2], update_data[3]))

        # Batch insert new audience responses
        if audience_inserts:
            cur.executemany(
                """
                INSERT INTO partner_audience_responses 
                (bid_id, partner_response_id, audience_id, country, 
                 commitment, cpi, timeline_days, comments, commitment_type, is_best_efforts, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, audience_inserts)

        conn.commit()
        print(f"Successfully updated {len(responses)} partner responses, {len(audience_updates)} audience updates, {len(audience_inserts)} audience inserts")
        return jsonify({"message": "Partner responses updated successfully"}), 200

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Error updating partner responses: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
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
        data = request.json
        print(f"Updating VM {vm_id} with data: {data}")

        # Get VMs from Replit DB
        vms = db.get('vendor_managers', {})

        # Find the VM to update
        vm_key = str(vm_id)
        if vm_key not in vms:
            return jsonify({"error": f"VM with ID {vm_id} not found"}), 404

        # Check if new vm_id already exists (if it's being changed)
        if data.get('vm_id') and data.get('vm_id') != vms[vm_key].get('vm_id'):
            for existing_vm in vms.values():
                if existing_vm.get('vm_id') == data.get('vm_id'):
                    return jsonify({"error": "VM ID already exists"}), 400

        # Update VM data
        vms[vm_key].update({
            'vm_id': data.get('vm_id'),
            'vm_name': data.get('vm_name'),
            'contact_person': data.get('contact_person'),
            'reporting_manager': data.get('reporting_manager'),
            'team': data.get('team'),
            'updated_at': datetime.now().isoformat()
        })

        # Save back to Replit DB
        db['vendor_managers'] = vms

        return jsonify(vms[vm_key])

    except Exception as e:
        print(f"Error updating VM: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/vms/<int:vm_id>', methods=['DELETE'])
def delete_vm(vm_id):
    try:
        # Get VMs from Replit DB
        vms = db.get('vendor_managers', {})

        # Check if VM exists
        vm_key = str(vm_id)
        if vm_key not in vms:
            return jsonify({"error": f"VM with ID {vm_id} not found"}), 404

        # Delete the VM
        del vms[vm_key]
        db['vendor_managers'] = vms

        return jsonify({"message": "VM deleted successfully"})

    except Exception as e:
        print(f"Error deleting VM: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
        email = data.get('email')
        password = data.get('password')

        print(f"Login attempt with email: {email}")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Find user by email
        cur.execute('SELECT * FROM users WHERE email = %s', (email, ))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            print(f"User not found: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401

        password_hash = user['password_hash']
        print(f"Input password: {password}")

        is_authenticated = False

        try:
            # Try Werkzeug's check_password_hash first
            is_authenticated = check_password_hash(password_hash, password)
            print(f"Password verification result: {is_authenticated}")
        except Exception as e:
            print(f"Password verification error: {str(e)}")
            # Fallback: try direct password comparison for admin or regenerate hash
            is_authenticated = False

            # For admin user with default password, update hash and authenticate
            if email == 'admin@example.com' and password == 'admin':
                try:
                    new_password_hash = generate_password_hash(
                        password, method='pbkdf2:sha256')
                    conn_update = get_db_connection()
                    cur_update = conn_update.cursor()
                    cur_update.execute(
                        "UPDATE users SET password_hash = %s WHERE email = %s",
                        (new_password_hash, email))
                    conn_update.commit()
                    cur_update.close()
                    conn_update.close()
                    is_authenticated = True
                    print(
                        "Updated admin password hash and authenticated successfully"
                    )
                except Exception as fallback_error:
                    print(
                        f"Fallback authentication failed: {str(fallback_error)}"
                    )
                    # Last resort: check if password matches plain text (for migration)
                    if password_hash == password:
                        new_password_hash = generate_password_hash(
                            password, method='pbkdf2:sha256')
                        try:
                            conn_update = get_db_connection()
                            cur_update = conn_update.cursor()
                            cur_update.execute(
                                "UPDATE users SET password_hash = %s WHERE email = %s",
                                (new_password_hash, email))
                            conn_update.commit()
                            cur_update.close()
                            conn_update.close()
                            is_authenticated = True
                            print(
                                "Migrated plain text password to hash and authenticated"
                            )
                        except Exception as migration_error:
                            print(f"Migration failed: {str(migration_error)}")
                            is_authenticated = False

        if is_authenticated:
            # Get permissions for the user's role
            permissions = ROLES_AND_PERMISSIONS.get(user['role'], {})

            user_data = {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'team': user['team'],
                'permissions': permissions
            }
            print(f"Login successful for {email}")
            return jsonify({'token': 'sample-jwt-token', 'user': user_data})

        print(
            f"Login failed for email: {email} - password verification failed")
        return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500


def get_public_host_url():
    # In a development environment, the frontend runs on a separate server.
    # We detect this by checking if the request host is a local address.
    host = request.host.split(':')[0]

    # Check if we're in Replit environment
    if 'replit.dev' in request.host or 'repl.co' in request.host:
        # Use the current request host but ensure it's https
        return f"https://{request.host.split(':')[0]}"

    if host in ('localhost', '127.0.0.1', '0.0.0.0'):
        # Always use http://localhost:3000 for local development links.
        return 'http://localhost:3000'

    # For production, use the forwarded host if behind a proxy.
    forwarded_host = request.headers.get('X-Forwarded-Host')
    if forwarded_host:
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        return f"{scheme}://{forwarded_host}"

    # Otherwise, return the default request host URL.
    return request.host_url.rstrip('/')


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
            base_url = get_public_host_url().replace('5000',
                                                     '3000').rstrip('/')
            return jsonify({
                'link':
                f"{base_url}/partner-response/{existing_link['token']}",
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

        base_url = get_public_host_url().replace('5000', '3000').rstrip('/')
        return jsonify({
            'link': f"{base_url}/partner-response/{new_link['token']}",
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
        # try:
        #     cur.execute("""
        #         SELECT p.contact_email, p.partner_name, b.bid_number, b.study_name
        #         FROM partners p
        #         JOIN bids b ON b.id = %s
        #         WHERE p.id = %s
        #     """, (bid_id, partner_id))
        #     partner_info = cur.fetchone()

        #     if partner_info and partner_info['contact_email']:
        #         send_link_extension_email(
        #             partner_info['contact_email'],
        #             partner_info['partner_name'],
        #             partner_info['bid_number'],
        #             partner_info['study_name'],
        #             f"http://localhost:3001/partner-response/{updated_link['token']}",
        #             updated_link['expires_at']
        #         )
        # except Exception as email_error:
        #     print(f"Error sending extension email: {str(email_error)}")

        base_url = get_public_host_url().replace('5000', '3000').rstrip('/')
        return jsonify({
            'link': f"{base_url}/partner-response/{updated_link['token']}",
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

        #mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {str(e)}")


@app.route('/partner-response/<token>', methods=['GET'])
def partner_response_form(token):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bid_id, partner_id, expires_at FROM partner_links WHERE token = %s
            """, (token, ))
        row = cur.fetchone()
        if not row:
            return "Invalid or expired link.", 404
        bid_id, partner_id, expires_at = row
        # Make expires_at timezone-aware if it's naive
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return "This link has expired.", 410
        return f"Valid link! Bid ID: {bid_id}, Partner ID: {partner_id}"
    except Exception as e:
        print(f"Error in partner_response_form: {str(e)}")
        return "An error occurred.", 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


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
        conn = get_db_connection()
        cur = conn.cursor()
        # Look up token
        cur.execute(
            "SELECT bid_id, partner_id, expires_at FROM partner_links WHERE token = %s",
            (token, ))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Invalid or expired link."}), 404
        bid_id, partner_id, expires_at = row
        if expires_at.tzinfo is None:
            from datetime import timezone
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        from datetime import datetime, timezone
        if expires_at < datetime.now(timezone.utc):
            return jsonify({"error": "This link has expired."}), 403
        data = request.get_json()
        pmf = data.get('pmf')
        currency = data.get('currency')
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
            partner_response_id = cur.fetchone()[0]
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
                    # Upsert into partner_audience_responses
                    cur.execute(
                        """
                        INSERT INTO partner_audience_responses (bid_id, partner_response_id, audience_id, country, commitment_type, commitment, cpi, timeline_days, comments, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (bid_id, partner_response_id, audience_id, country)
                        DO UPDATE SET commitment_type = EXCLUDED.commitment_type, commitment = EXCLUDED.commitment, cpi = EXCLUDED.cpi, timeline_days = EXCLUDED.timeline_days, comments = EXCLUDED.comments, updated_at = CURRENT_TIMESTAMP
                    """,
                        (bid_id, partner_response_id, audience_id, country,
                         commitment_type, commitment, cpi, timeline, comments))
        conn.commit()

        # Send admin notification email
        if ADMIN_NOTIFICATION_EMAIL:
            try:
                # Fetch additional details for the email
                cur.execute("SELECT partner_name FROM partners WHERE id = %s",
                            (partner_id, ))
                partner_name = cur.fetchone()[0]

                cur.execute(
                    "SELECT bid_number, study_name FROM bids WHERE id = %s",
                    (bid_id, ))
                bid_info = cur.fetchone()
                bid_number = bid_info[0]
                study_name = bid_info[1]

                # Map audience IDs to full details
                cur.execute(
                    "SELECT id, audience_name, ta_category, broader_category, mode, ir FROM bid_target_audiences WHERE bid_id = %s",
                    (bid_id, ))
                aud_map = {}
                for row in cur.fetchall():
                    aud_map[str(row[0])] = {
                        'audience_name': row[1],
                        'ta_category': row[2],
                        'broader_category': row[3],
                        'mode': row[4],
                        'ir': row[5]
                    }

                # Build HTML table
                table_html = '''<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;">
<tr><th>LOI</th><th>Audience</th><th>Country</th><th>Commitment Type</th><th>Commitment</th><th>CPI</th><th>Timeline</th><th>Comments</th><th>Updated On</th></tr>
'''
                for loi, audiences in data.get('form', {}).items():
                    # Fetch updated_at for this LOI
                    cur.execute(
                        "SELECT updated_at FROM partner_responses WHERE bid_id = %s AND partner_id = %s AND loi = %s",
                        (bid_id, partner_id, loi))
                    updated_at_result = cur.fetchone()
                    updated_at_str = updated_at_result[0].strftime(
                        '%Y-%m-%d %H:%M:%S') if updated_at_result else 'N/A'

                    for aud_id, aud_data in audiences.items():
                        aud_info = aud_map.get(str(aud_id), {})
                        aud_label = f"{aud_info.get('audience_name', f'Audience {aud_id}')}: {aud_info.get('ta_category','')} - {aud_info.get('broader_category','')} - {aud_info.get('mode','')} - IR {aud_info.get('ir','')}%"
                        timeline = aud_data.get('timeline', '')
                        comments = aud_data.get('comments', '')
                        for country, cdata in aud_data.get('countries',
                                                           {}).items():
                            table_html += f"<tr>"
                            table_html += f"<td>{loi}</td>"
                            table_html += f"<td>{aud_label}</td>"
                            table_html += f"<td>{country}</td>"
                            table_html += f"<td>{cdata.get('commitment_type','')}</td>"
                            table_html += f"<td>{cdata.get('commitment','')}</td>"
                            table_html += f"<td>{cdata.get('cpi','')}</td>"
                            table_html += f"<td>{timeline}</td>"
                            table_html += f"<td>{comments.replace('<','&lt;').replace('>','&gt;').replace('\n',' ')}</td>"
                            table_html += f"<td>{updated_at_str}</td>"
                            table_html += f"</tr>"
                table_html += "</table>"
                if table_html.count('<tr>') == 1:
                    table_html = "No audience/country data submitted."

                msg = Message(
                    f'Response Submitted: {partner_name} for Bid {bid_number}',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[ADMIN_NOTIFICATION_EMAIL])
                msg.body = f"""
A partner has submitted or updated their response.

Partner Name: {partner_name}
Bid Number: {bid_number}
Study Name: {study_name}

See the HTML version of this email for a detailed table.

You can view the full response by clicking the link below:
Link: {base_url}/partner-response/{token}
"""
                base_url = os.getenv('FRONTEND_BASE_URL',
                                     'http://localhost:3000')
                if hasattr(request, 'host') and ('replit.dev' in request.host
                                                 or 'repl.co' in request.host):
                    base_url = f"https://{request.host.split(':')[0]}"

                msg.html = f"""
<p>A partner has submitted or updated their response.</p>
<p><b>Partner Name:</b> {partner_name}<br>
<b>Bid Number:</b> {bid_number}<br>
<b>Study Name:</b> {study_name}</p>
<p><b>Submitted Details:</b><br>{table_html}</p>
<p>You can view the full response by clicking the link below:<br>
<a href='{base_url}/partner-response/{token}'>Link: {base_url}/partner-response/{token}</a></p>
                """
                #mail.send(msg)
            except Exception as e:
                print(f"Error sending admin notification: {str(e)}")
        return jsonify({"success": True})
    except Exception as e:
        print("Error in submit_partner_link_response:", e)
        return jsonify({"error": str(e)}), 500


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

        # Update proposal
        cur.execute(
            """
            UPDATE proposals 
            SET data = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (json.dumps(data), proposal_id))

        updated = cur.fetchone()
        if not updated:
            return jsonify({"error": "Proposal not found"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'id': updated['id'],
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


@app.route('/api/bids/find-similar', methods=['POST'])
def find_similar_bids():
    try:
        data = request.json
        ta_category = data.get('taCategory')
        broader_category = data.get('broaderCategory')
        mode = data.get('mode')

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            '''
            WITH base AS (
                SELECT
                    b.id as bid_id,
                    b.bid_number,
                    c.client_name,
                    p.partner_name,
                    bta.exact_ta_definition,
                    bta.ir,
                    bta.sample_required,
                    bta.is_best_efforts,
                    bac.country,
                    bta.id as audience_id,
                    par.commitment,
                    par.n_delivered,
                    par.cpi
                FROM bids b
                JOIN clients c ON b.client = c.id
                JOIN bid_target_audiences bta ON b.id = bta.bid_id
                JOIN bid_audience_countries bac ON bta.id = bac.audience_id AND bac.country IS NOT NULL
                JOIN partner_responses pr ON pr.bid_id = b.id
                JOIN partners p ON pr.partner_id = p.id
                JOIN partner_audience_responses par ON pr.id = par.partner_response_id AND par.audience_id = bta.id
                WHERE bta.ta_category = %s
                  AND bta.broader_category = %s
                  AND bta.mode = %s
                  AND bac.country = par.country
            )
            , country_agg AS (
                SELECT
                    bid_id,
                    bid_number,
                    client_name,
                    partner_name,
                    exact_ta_definition,
                    ir,
                    sample_required,
                    is_best_efforts,
                    country,
                    SUM(commitment) as committed,
                    SUM(n_delivered) as n_delivered,
                    MAX(cpi) as cpi
                FROM base
                GROUP BY bid_id, bid_number, client_name, partner_name, exact_ta_definition, ir, sample_required, is_best_efforts, country
            )
            SELECT
                bid_id,
                bid_number,
                client_name,
                partner_name,
                exact_ta_definition,
                ir,
                sample_required,
                is_best_efforts,
                STRING_AGG(country, ', ') as countries,
                SUM(committed) as committed,
                SUM(n_delivered) as n_delivered,
                MAX(cpi) as cpi,
                jsonb_object_agg(
                    country,
                    jsonb_build_object(
                        'committed', committed,
                        'delivered', n_delivered,
                        'cpi', cpi
                    )
                ) as country_data
            FROM country_agg
            GROUP BY bid_id, bid_number, client_name, partner_name, exact_ta_definition, ir, sample_required, is_best_efforts
            ORDER BY bid_number DESC;
        ''', (ta_category, broader_category, mode))

        results = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        print(f"Error in find_similar_bids: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/bids/request-access', methods=['POST'])
def request_access():
    conn = None
    cur = None
    conn_email = None
    cur_email = None

    try:
        data = request.json
        bid_id = data.get('bidId')
        bid_number = data.get('bidNumber')
        study_name = data.get('studyName')
        user_email = data.get('userEmail')
        user_name = data.get('userName')
        user_team = data.get('userTeam')

        print(
            f"Request access called with: bid_id={bid_id}, bid_number={bid_number}, user_email={user_email}"
        )

        conn = get_db_connection()
        cur = conn.cursor()

        # Look up user_id by email
        user_id = None
        if user_email:
            cur.execute('SELECT id FROM users WHERE email = %s', (user_email,))
            user_row = cur.fetchone()
            if user_row:
                user_id = user_row[0]

        # Check if there's already a request for this bid/user/team combination
        cur.execute(
            '''
            SELECT status FROM bid_access_requests 
            WHERE bid_id = %s AND user_id = %s AND team = %s
        ''', (bid_id, user_id, user_team))

        existing_request = cur.fetchone()
        request_created_or_updated = False

        if existing_request:
            if existing_request[0] == 'pending':
                print(f"Access request already pending for bid {bid_id}, user {user_id}, team {user_team}")
                # Request already exists and is pending, no action needed
                request_created_or_updated = False
            elif existing_request[0] == 'denied':
                # Update the denied request to pending (allow re-request)
                print(f"Updating denied request to pending for bid {bid_id}, user {user_id}, team {user_team}")
                cur.execute(
                    '''
                    UPDATE bid_access_requests 
                    SET status = 'pending', requested_on = CURRENT_TIMESTAMP
                    WHERE bid_id = %s AND user_id = %s AND team = %s
                ''', (bid_id, user_id, user_team))
                request_created_or_updated = True
            elif existing_request[0] == 'granted':
                print(f"Access already granted for bid {bid_id}, user {user_id}, team {user_team}")
                # Request already granted, no action needed
                request_created_or_updated = False
        else:
            # Insert new access request
            print(f"Creating new access request for bid {bid_id}, user {user_id}, team {user_team}")
            cur.execute(
                '''
                INSERT INTO bid_access_requests (bid_id, user_id, team, status)
                VALUES (%s, %s, %s, 'pending')
            ''', (bid_id, user_id, user_team))
            request_created_or_updated = True

        conn.commit()

        # Only send email notifications if a request was actually created or updated
        if request_created_or_updated:
            # Send email notifications to multiple recipients
            try:
                conn_email = get_db_connection()
                cur_email = conn_email.cursor(cursor_factory=RealDictCursor)

                # Get bid owner email
                cur_email.execute(
                    '''
                    SELECT u.email, u.name 
                    FROM bids b 
                    JOIN users u ON b.created_by = u.id 
                    WHERE b.id = %s
                ''', (bid_id,))
                bid_owner = cur_email.fetchone()

                # Send notification only to bid creator
                if bid_owner and bid_owner['email']:
                    base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
                    if hasattr(request, 'host') and ('replit.dev' in request.host or 'repl.co' in request.host):
                        base_url = f"https://{request.host.split(':')[0]}"

                    msg = Message('🔔 Bid Access Request - Action Required',
                                  sender=app.config['MAIL_DEFAULT_SENDER'],
                                  recipients=[bid_owner['email']])

                    msg.body = f"""URGENT: New Bid Access Request

A user has requested access to a bid and requires your approval.

📋 REQUEST DETAILS:
• Bid Number: {bid_number}
• Study Name: {study_name}
• Requester: {user_name} ({user_email})
• Team: {user_team}
• Request Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 ACTION REQUIRED:
Please log into the bid management system to review and approve/deny this request.

Access the system: {base_url}

⚠️ Note: This request is pending your approval. The user cannot access the bid until you grant permission.

Best regards,
Bid Management System
---
This is an automated notification. Please do not reply to this email."""

                    msg.html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                        <h2 style="color: #d32f2f; margin-bottom: 20px;">🔔 Bid Access Request - Action Required</h2>

                        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <strong>URGENT:</strong> A user has requested access to a bid and requires your approval.
                        </div>

                        <h3 style="color: #333; margin-bottom: 15px;">📋 Request Details:</h3>
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <tr style="background-color: #f8f9fa;">
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Bid Number:</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{bid_number}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Study Name:</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{study_name}</td>
                            </tr>
                            <tr style="background-color: #f8f9fa;">
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Requester:</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{user_name} ({user_email})</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Team:</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{user_team}</td>
                            </tr>
                            <tr style="background-color: #f8f9fa;">
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Request Time:</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                        </table>

                        <div style="background-color: #e3f2fd; border: 1px solid #90caf9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <h3 style="color: #1976d2; margin-bottom: 10px;">🎯 Action Required:</h3>
                            <p style="margin: 0;">Please log into the bid management system to review and approve/deny this request.</p>
                        </div>

                        <div style="text-align: center; margin: 20px 0;">
                            <a href="{base_url}" style="background-color: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Access Bid Management System
                            </a>
                        </div>

                        <div style="background-color: #ffebee; border: 1px solid #ffcdd2; padding: 10px; border-radius: 5px; margin-top: 20px;">
                            <small style="color: #d32f2f;">
                                ⚠️ <strong>Note:</strong> This request is pending your approval. The user cannot access the bid until you grant permission.
                            </small>
                        </div>

                        <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #666; margin: 0;">
                            This is an automated notification from the Bid Management System. Please do not reply to this email.
                        </p>
                    </div>
                    """

                    mail.send(msg)
                    print(f"Access request email sent to bid creator: {bid_owner['email']}")

            except Exception as email_error:
                print(f"Error sending access request email: {str(email_error)}")
                import traceback
                print(f"Email error traceback: {traceback.format_exc()}")
            finally:
                if cur_email:
                    cur_email.close()
                if conn_email:
                    conn_email.close()

        return jsonify({'message': 'Access request submitted successfully'}), 200

    except Exception as e:
        print(f"Error in request_access: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/notifications/count', methods=['GET'])
def get_notification_count():
    """Get notification count for current user"""
    try:
        user_id = request.headers.get('X-User-Id')
        user_role = (request.headers.get('X-User-Role') or '').lower()
        user_name = (request.headers.get('X-User-Name') or '').lower()
        
        if not user_id:
            return jsonify({'count': 0}), 200
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        notification_count = 0
        
        # Count pending requests only for bids they created
        cur.execute('''
            SELECT COUNT(*)
            FROM bid_access_requests bar
            JOIN bids b ON bar.bid_id = b.id
            WHERE bar.status = 'pending'
            AND b.created_by = %s
        ''', (user_id,))
        result = cur.fetchone()
        notification_count = result[0] if result else 0
        
        cur.close()
        conn.close()
        
        return jsonify({'count': notification_count}), 200
        
    except Exception as e:
        print(f"Error getting notification count: {str(e)}")
        return jsonify({'count': 0}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get detailed notifications for current user"""
    try:
        user_id = request.headers.get('X-User-Id')
        user_role = (request.headers.get('X-User-Role') or '').lower()
        user_name = (request.headers.get('X-User-Name') or '').lower()
        
        if not user_id:
            return jsonify({'notifications': []}), 200
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get pending requests only for bids they created
        cur.execute('''
            SELECT 
                bar.id,
                bar.bid_id,
                bar.user_id,
                bar.team,
                bar.requested_on,
                b.bid_number,
                b.study_name,
                u.email,
                u.name as requester_name
            FROM bid_access_requests bar
            JOIN bids b ON bar.bid_id = b.id
            LEFT JOIN users u ON bar.user_id = u.id
            WHERE bar.status = 'pending'
            AND b.created_by = %s
            ORDER BY bar.requested_on DESC
        ''', (user_id,))
        
        notifications = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({'notifications': notifications}), 200
        
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify({'notifications': []}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bids/<int:bid_id>/copy', methods=['POST'])
def copy_bid(bid_id):
    try:
        data = request.json or {}
        new_creator_id = data.get('created_by')
        new_team = data.get('team')
        if not new_creator_id or not new_team:
            return jsonify({'error': 'created_by and team are required'}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Get the original bid
        cur.execute('SELECT * FROM bids WHERE id = %s', (bid_id, ))
        orig_bid = cur.fetchone()
        if not orig_bid:
            return jsonify({'error': 'Original bid not found'}), 404

        # 2. Get the next bid number
        cur.execute('SELECT MAX(CAST(bid_number AS INTEGER)) FROM bids')
        max_bid_number = cur.fetchone()['max']
        new_bid_number = str(int(max_bid_number) +
                             1) if max_bid_number else '10001'

        # 3. Insert the new bid
        cur.execute(
            '''
            INSERT INTO bids (
                bid_number, bid_date, study_name, methodology, status, client, sales_contact, vm_contact, project_requirement, created_by, team, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (new_bid_number, orig_bid['bid_date'], orig_bid['study_name'],
              orig_bid['methodology'], orig_bid['client'],
              orig_bid['sales_contact'], orig_bid['vm_contact'],
              orig_bid['project_requirement'], new_creator_id, new_team))
        new_bid_id = cur.fetchone()['id']

        # 4. Copy target audiences
        cur.execute('SELECT * FROM bid_target_audiences WHERE bid_id = %s',
                    (bid_id, ))
        orig_audiences = cur.fetchall()
        old_to_new_audience = {}
        for aud in orig_audiences:
            cur.execute(
                '''
                INSERT INTO bid_target_audiences (
                    bid_id, audience_name, ta_category, broader_category, exact_ta_definition, mode, sample_required, is_best_efforts, ir, comments, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (new_bid_id, aud['audience_name'], aud['ta_category'],
                  aud['broader_category'], aud['exact_ta_definition'],
                  aud['mode'], aud['sample_required'], aud['is_best_efforts'],
                  aud['ir'], aud['comments']))
            new_aud_id = cur.fetchone()['id']
            old_to_new_audience[aud['id']] = new_aud_id

        # 5. Copy audience countries
        cur.execute('SELECT * FROM bid_audience_countries WHERE bid_id = %s',
                    (bid_id, ))
        for row in cur.fetchall():
            cur.execute(
                '''
                INSERT INTO bid_audience_countries (
                    bid_id, audience_id, country, sample_size, is_best_efforts, created_at
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (new_bid_id, old_to_new_audience.get(row['audience_id']),
                  row['country'], row['sample_size'], row['is_best_efforts']))

        # 6. Copy bid partners
        cur.execute('SELECT * FROM bid_partners WHERE bid_id = %s', (bid_id, ))
        for row in cur.fetchall():
            cur.execute(
                '''
                INSERT INTO bid_partners (
                    bid_id, partner_id, created_at, updated_at
                ) VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (new_bid_id, row['partner_id']))

        # 7. Copy partner_responses and partner_audience_responses
        # Map old partner_response_id to new
        cur.execute('SELECT * FROM partner_responses WHERE bid_id = %s',
                    (bid_id, ))
        orig_partner_responses = cur.fetchall()
        old_to_new_partner_response = {}
        for pr in orig_partner_responses:
            cur.execute(
                '''
                INSERT INTO partner_responses (
                    bid_id, partner_id, loi, status, currency, pmf, timeline, invoice_date, invoice_sent, invoice_serial, invoice_number, invoice_amount, response_date, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (new_bid_id, pr['partner_id'], pr['loi'], pr['status'],
                  pr['currency'], pr['pmf'], pr['timeline'],
                  pr['invoice_date'], pr['invoice_sent'], pr['invoice_serial'],
                  pr['invoice_number'], pr['invoice_amount'],
                  pr['response_date']))
            new_pr_id = cur.fetchone()['id']
            old_to_new_partner_response[pr['id']] = new_pr_id

        # 8. Copy partner_audience_responses
        cur.execute(
            'SELECT * FROM partner_audience_responses WHERE bid_id = %s',
            (bid_id, ))
        for row in cur.fetchall():
            cur.execute(
                '''
                INSERT INTO partner_audience_responses (
                    bid_id, partner_response_id, audience_id, country, allocation, commitment, is_best_efforts, commitment_type, cpi, timeline_days, comments, n_delivered, quality_rejects, final_loi, final_ir, final_timeline, final_cpi, field_close_date, initial_cost, final_cost, savings, communication, engagement, problem_solving, additional_feedback, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (new_bid_id,
                  old_to_new_partner_response.get(row['partner_response_id']),
                  old_to_new_audience.get(row['audience_id']), row['country'],
                  row['allocation'], row['commitment'], row['is_best_efforts'],
                  row['commitment_type'], row['cpi'], row['timeline_days'],
                  row['comments'], row['n_delivered'], row['quality_rejects'],
                  row['final_loi'], row['final_ir'], row['final_timeline'],
                  row['final_cpi'], row['field_close_date'],
                  row['initial_cost'], row['final_cost'], row['savings'],
                  row['communication'], row['engagement'],
                  row['problem_solving'], row['additional_feedback']))

        conn.commit()
        return jsonify({
            'new_bid_id': new_bid_id,
            'new_bid_number': new_bid_number
        }), 201
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f'Error copying bid: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@app.route('/api/bids/<int:bid_id>/grant-access', methods=['POST'])
def grant_bid_access(bid_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        team = data.get('team')
        granted_by = data.get(
            'granted_by')  # In real use, get from session/auth
        if not (user_id or team):
            return jsonify({'error': 'user_id or team is required'}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        # Insert access record
        cur.execute(
            '''
            INSERT INTO bid_access (bid_id, user_id, team, granted_by)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (bid_id, user_id, team) DO NOTHING
        ''', (bid_id, user_id, team, granted_by))
        conn.commit()
        # Fetch bid info for email
        cur.execute('SELECT bid_number, study_name FROM bids WHERE id = %s',
                    (bid_id, ))
        bid_info = cur.fetchone()
        bid_number = bid_info[0] if bid_info else bid_id
        study_name = bid_info[1] if bid_info else ''
        # Prepare recipients
        recipients = []
        if user_id:
            cur.execute('SELECT email, name FROM users WHERE id = %s',
                        (user_id, ))
            user = cur.fetchone()
            if user:
                recipients.append({'email': user[0], 'name': user[1]})
        if team:
            cur.execute('SELECT email, name FROM users WHERE team = %s',
                        (team, ))
            team_users = cur.fetchall()
            for u in team_users:
                recipients.append({'email': u[0], 'name': u[1]})
        # Remove duplicates
        seen = set()
        unique_recipients = []
        for r in recipients:
            if r['email'] not in seen:
                unique_recipients.append(r)
                seen.add(r['email'])
        # Send email
        for r in unique_recipients:
            try:
                msg = Message(subject=f"Bid Access Granted: {bid_number}",
                              sender=app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[r['email']])
                msg.body = f"""Hi {r['name']},

You have been granted access to the following bid:

Bid Number: {bid_number}
Study Name: {study_name}

You can now view and copy this bid in the system.

Best regards,
Bid Management Team"""

                mail.send(msg)
                print(f"Access granted email sent to {r['email']}")
            except Exception as email_error:
                print(
                    f"Error sending access granted email to {r['email']}: {str(email_error)}"
                )
                import traceback
                print(f"Email error traceback: {traceback.format_exc()}")
        cur.close()
        conn.close()
        return jsonify({'message': 'Access granted successfully.'}), 200
    except Exception as e:
        print(f"Error in grant_bid_access: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/access', methods=['GET'])
def check_bid_access(bid_id):
    try:
        user_id = request.args.get('user_id')
        team = request.args.get('team')
        if not (user_id or team):
            return jsonify({'error': 'user_id or team is required'}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT 1 FROM bid_access
            WHERE bid_id = %s AND (user_id = %s OR team = %s)
            LIMIT 1
        ''', (bid_id, user_id, team))
        has_access = cur.fetchone() is not None
        cur.close()
        conn.close()
        return jsonify({'has_access': has_access}), 200
    except Exception as e:
        print(f"Error in check_bid_access: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/access-requests', methods=['GET'])
def get_access_requests(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT r.id, r.user_id, r.team, r.requested_on, r.status, u.email, u.name
            FROM bid_access_requests r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.bid_id = %s AND r.status = 'pending'
            ORDER BY r.requested_on
        ''', (bid_id, ))
        requests = [{
            'id': row[0],
            'user_id': row[1],
            'team': row[2],
            'requested_on': row[3],
            'status': row[4],
            'email': row[5],
            'name': row[6],
        } for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'requests': requests}), 200
    except Exception as e:
        print(f"Error in get_access_requests: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/access-requests/<int:request_id>/grant',
           methods=['POST'])
def grant_access_request(bid_id, request_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Get the request info
        cur.execute(
            '''
            SELECT bar.user_id, bar.team, u.email, u.name, b.bid_number, b.study_name
            FROM bid_access_requests bar
            LEFT JOIN users u ON bar.user_id = u.id
            JOIN bids b ON bar.bid_id = b.id
            WHERE bar.id = %s AND bar.bid_id = %s
            ''', (request_id, bid_id))
        req = cur.fetchone()
        if not req:
            cur.close()
            conn.close()
            return jsonify({'error': 'Request not found'}), 404
        
        user_id, team, user_email, user_name, bid_number, study_name = req['user_id'], req['team'], req['email'], req['name'], req['bid_number'], req['study_name']

        print(
            f"DEBUG: Granting access for bid_id={bid_id}, user_id={user_id}, team={team}"
        )

        # Grant access (insert into bid_access)
        # Insert access record without conflict resolution for now
        cur.execute(
            '''
            INSERT INTO bid_access (bid_id, user_id, team, granted_by)
            VALUES (%s, %s, %s, %s)
        ''', (bid_id, user_id, team, None))

        # Mark request as granted
        cur.execute('UPDATE bid_access_requests SET status = %s WHERE id = %s',
                    ('granted', request_id))
        conn.commit()

        # Verify the access was inserted
        cur.execute(
            'SELECT * FROM bid_access WHERE bid_id = %s AND (user_id = %s OR team = %s)',
            (bid_id, user_id, team))
        access_record = cur.fetchone()
        print(f"DEBUG: Access record after grant: {access_record}")

        # Send email notification to the user who requested access
        try:
            if user_email:
                base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
                if hasattr(request, 'host') and ('replit.dev' in request.host or 'repl.co' in request.host):
                    base_url = f"https://{request.host.split(':')[0]}"

                msg = Message('✅ Bid Access Granted - You Can Now Access the Bid',
                              sender=app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[user_email])

                msg.body = f"""Good news! Your bid access request has been approved.

📋 ACCESS GRANTED FOR:
• Bid Number: {bid_number}
• Study Name: {study_name}
• Granted Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 NEXT STEPS:
You can now access this bid in the system. You have full viewing and copying permissions for this bid.

Access the system: {base_url}

Thank you for using the Bid Management System!

Best regards,
Bid Management Team
---
This is an automated notification. Please do not reply to this email."""

                msg.html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #4caf50; margin-bottom: 20px;">✅ Bid Access Granted</h2>
                    
                    <div style="background-color: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <strong>Good news!</strong> Your bid access request has been approved.
                    </div>
                    
                    <h3 style="color: #333; margin-bottom: 15px;">📋 Access Granted For:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Bid Number:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{bid_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Study Name:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{study_name}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Granted Time:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                    </table>
                    
                    <div style="background-color: #e3f2fd; border: 1px solid #90caf9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="color: #1976d2; margin-bottom: 10px;">🎯 Next Steps:</h3>
                        <p style="margin: 0;">You can now access this bid in the system. You have full viewing and copying permissions for this bid.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{base_url}" style="background-color: #4caf50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Access Bid Management System
                        </a>
                    </div>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666; margin: 0;">
                        This is an automated notification from the Bid Management System. Please do not reply to this email.
                    </p>
                </div>
                """

                mail.send(msg)
                print(f"Access granted email sent to {user_email}")
        except Exception as email_error:
            print(f"Error sending access granted email: {str(email_error)}")

        cur.close()
        conn.close()
        return jsonify({'message': 'Access granted and request updated.'}), 200
    except Exception as e:
        print(f"Error in grant_access_request: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/access-requests/<int:request_id>/deny',
           methods=['POST'])
def deny_access_request(bid_id, request_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'UPDATE bid_access_requests SET status = %s WHERE id = %s AND bid_id = %s',
            ('denied', request_id, bid_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Request denied.'}), 200
    except Exception as e:
        print(f"Error in deny_access_request: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/debug-access-requests', methods=['GET'])
def debug_access_requests(bid_id):
    """
    Debug endpoint: List all access requests for a bid, including status, user, and team.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT r.id, r.user_id, u.email, u.name, r.team, r.requested_on, r.status
            FROM bid_access_requests r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.bid_id = %s
            ORDER BY r.requested_on
        ''', (bid_id, ))
        requests = [{
            'id':
            row[0],
            'user_id':
            row[1],
            'email':
            row[2],
            'name':
            row[3],
            'team':
            row[4],
            'requested_on':
            row[5].strftime('%Y-%m-%d %H:%M:%S') if row[5] else None,
            'status':
            row[6]
        } for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'requests': requests}), 200
    except Exception as e:
        print(f"Error in debug_access_requests: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/revoke-access', methods=['POST'])
def revoke_bid_access(bid_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        team = data.get('team')
        if not (user_id or team):
            return jsonify({'error': 'user_id or team is required'}), 400
        conn = get_db_connection()
        cur = conn.cursor()

        # Remove access record
        cur.execute(
            '''
            DELETE FROM bid_access
            WHERE bid_id = %s AND (user_id = %s OR team = %s)
        ''', (bid_id, user_id, team))

        # Also remove any existing access request records for this user/team
        cur.execute(
            '''
            DELETE FROM bid_access_requests
            WHERE bid_id = %s AND (user_id = %s OR team = %s)
        ''', (bid_id, user_id, team))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Access revoked successfully.'}), 200
    except Exception as e:
        print(f"Error in revoke_bid_access: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/<int:bid_id>/granted-access', methods=['GET'])
def get_granted_access(bid_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT ba.user_id, u.email, u.name, ba.team
            FROM bid_access ba
            LEFT JOIN users u ON ba.user_id = u.id
            WHERE ba.bid_id = %s
        ''', (bid_id, ))
        granted = [{
            'user_id': row[0],
            'email': row[1],
            'name': row[2],
            'team': row[3]
        } for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'granted': granted}), 200
    except Exception as e:
        print(f"Error in get_granted_access: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bids/granted-counts', methods=['GET'])
def get_granted_counts_batch():
    try:
        bid_ids_param = request.args.get('bid_ids', '')
        if not bid_ids_param:
            return jsonify({})
        bid_ids = [
            int(bid_id) for bid_id in bid_ids_param.split(',')
            if bid_id.isdigit()
        ]
        if not bid_ids:
            return jsonify({})
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT bid_id, COUNT(*) as granted_count
            FROM bid_access
            WHERE bid_id = ANY(%s)
            GROUP BY bid_id
        ''', (bid_ids, ))
        rows = cur.fetchall()
        result = {row[0]: row[1] for row in rows}
        cur.close()
        conn.close()
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_granted_counts_batch: {e}")
        return jsonify({}), 500


def create_tables():
    """Create additional tables if they don't exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create partner_links table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partner_links (
            id SERIAL PRIMARY KEY,
            bid_id INTEGER REFERENCES bids(id),
            partner_id INTEGER REFERENCES partners(id),
            token TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notification_sent BOOLEAN DEFAULT FALSE,
            UNIQUE(bid_id, partner_id)
        )
    """)

    # Create proposals table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id SERIAL PRIMARY KEY,
            bid_id INTEGER REFERENCES bids(id),
            data JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    try:
        # Skip API routes first
        if path.startswith('api/'):
            return "API route not found", 404

        # Look for dist directory in the project root
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        dist_dir = os.path.join(project_root, 'dist')

        print(f"Serving path: {path}")
        print(f"Dist dir: {dist_dir}")
        print(f"Dist exists: {os.path.exists(dist_dir)}")

        if not os.path.exists(dist_dir):
            return "React app not built. The 'dist' directory doesn't exist.", 404

        # For specific files (like CSS, JS, images), try to serve them directly
        if path and '.' in path:
            file_path = os.path.join(dist_dir, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_from_directory(dist_dir, path)

        # For all other routes (including root), serve index.html for React Router
        index_path = os.path.join(dist_dir, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(dist_dir, 'index.html')

        return "React app index.html not found.", 404

    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return f"Error serving file: {str(e)}", 500


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


@app.route('/api/admin/reset-password', methods=['POST'])
def reset_admin_password():
    """
    Temporarily endpoint to reset the admin password.
    This should be removed in a production environment.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Set a new password for the admin user
        new_password = 'admin'
        password_hash = generate_password_hash(new_password,
                                               method='pbkdf2:sha256')

        # Update the password for 'admin@example.com'
        cur.execute(
            """
            UPDATE users
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = 'admin@example.com'
            RETURNING id
            """, (password_hash, ))

        updated_user = cur.fetchone()
        conn.commit()

        if updated_user:
            return jsonify({
                'message':
                f"Password for 'admin@example.com' has been reset to '{new_password}'."
            }), 200
        else:
            return jsonify(
                {'error': "Admin user 'admin@example.com' not found."}), 404

    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


# Move app.run to the end after all routes are defined
if __name__ == '__main__':
    try:
        print("Initializing application...")
        # Initialize database when app starts
        init_db()
        create_tables()
        add_field_close_date_column()
        standardize_invoice_status()
        print("Database initialization completed")

        port = int(os.environ.get('PORT', 5000))
        print(f"Starting server on port {port}...")

        # Use Flask in production mode
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

    except Exception as e:
        print(f"Error starting server: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

        # Try alternative port if 5000 is busy
        try:
            alt_port = 5001
            print(f"Trying alternative port {alt_port}...")
            app.run(host='0.0.0.0',
                    port=alt_port,
                    debug=False,
                    use_reloader=False)
        except Exception as fallback_error:
            print(f"Fallback server also failed: {str(fallback_error)}")
            raise