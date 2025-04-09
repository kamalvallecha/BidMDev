from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        dbname="BidM",
        user="your_username",
        password="your_password",
        host="localhost"
    )

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users ORDER BY id')
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO users (employee_id, username, email, password, team, role, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        data['employee_id'],
        data['username'],
        data['email'],
        data['password'],  # Note: In production, hash the password
        data['team'],
        data['role'],
        'Active',
        datetime.now(),
        datetime.now()
    ))
    
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': new_id, 'message': 'User created successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000) 