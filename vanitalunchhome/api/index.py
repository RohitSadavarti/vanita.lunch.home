from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app)

# --- Use Environment Variables for Database Configuration ---
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    """Create and return a database connection."""
    try:
        # This line with sslmode='require' is essential
        conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None
        
# --- API Routes ---
# These handle your application's data.

@app.route('/api/menu-items')
def get_menu_items():
    """Get all menu items, grouped by category."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, name, description, price, image_url, category FROM menu_items ORDER BY category, name')
        items = cursor.fetchall()
        
        categories = {}
        for item in items:
            category = item['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(dict(item))
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order by adding entries for each item."""
    data = request.get_json()
    
    if not all(key in data for key in ['customer_name', 'mobile_number', 'items']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        for item in data['items']:
            final_price = float(item['price']) * int(item['quantity'])
            
            cursor.execute('''
                INSERT INTO orders (customer_name, mobile_number, item, unit, final_price)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                data['customer_name'],
                data['mobile_number'],
                item['name'],
                item['quantity'],
                final_price
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully!'
        }), 201
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# --- Frontend Serving Route ---
# This single route serves your main webpage.
# It should be defined AFTER your API routes.

