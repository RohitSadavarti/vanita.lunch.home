import os
import psycopg2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import json

app = Flask(__name__)
# Configure CORS - allow all origins for development, restrict in production
CORS(app, origins=['*'])  # Replace with your actual domain in production

# Remove admin functionality - no longer needed

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        sslmode='require'
    )
    return conn

# Route to serve the main page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get menu items
@app.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, item_name, description, CAST(price AS FLOAT) as price, category, veg_nonveg, meal_type, availability_time FROM menu_items ORDER BY category, item_name")
        menu_items = cur.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cur.description]
        
        # Convert to list of dictionaries
        menu_list = []
        if menu_items:
            for item in menu_items:
                item_dict = dict(zip(column_names, item))
                menu_list.append(item_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(menu_list)
    except Exception as e:
        print(f"Error in get_menu: {str(e)}")
        return jsonify({'error': 'Failed to load menu'}), 500

# API endpoint to place an order
@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        
        # Validate input data
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        cart_items = data.get('cart_items', [])
        payment_id = data.get('payment_id', '')
        
        if not name or not mobile or not address or not cart_items or not payment_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(mobile) != 10 or not mobile.isdigit():
            return jsonify({'error': 'Invalid mobile number'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Validate cart items against menu and calculate totals server-side
        validated_items = []
        subtotal = 0
        
        for cart_item in cart_items:
            item_id = cart_item.get('id')
            try:
                quantity = int(cart_item.get('quantity', 0))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity format'}), 400
            
            if not item_id or quantity <= 0:
                return jsonify({'error': 'Invalid item or quantity'}), 400
            
            # Fetch actual menu item from database
            cur.execute("SELECT id, item_name, price FROM menu_items WHERE id = %s", (item_id,))
            menu_item = cur.fetchone()
            
            if not menu_item:
                return jsonify({'error': f'Menu item with ID {item_id} not found'}), 400
            
            # Use server-side pricing
            actual_price = float(menu_item[2])
            item_total = actual_price * quantity
            subtotal += item_total
            
            validated_items.append({
                'id': menu_item[0],
                'name': menu_item[1],
                'price': actual_price,
                'quantity': quantity,
                'total': item_total
            })
        
        discount = 0  # No discount for now
        total_price = subtotal - discount
        
        # Insert single order record with validated items
        cur.execute("""
            INSERT INTO orders (customer_name, customer_mobile, items, subtotal, discount, total_price, status, payment_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            mobile,
            json.dumps(validated_items),
            subtotal,
            discount,
            total_price,
            'confirmed',
            payment_id,
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        print(f"Order placed successfully for {name} - {mobile}")
        return jsonify({'success': True, 'message': 'Order placed successfully'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in place_order: {str(e)}")
        return jsonify({'error': 'Failed to place order'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# API endpoint to get order status (for customer)
@app.route('/api/order-status/<order_id>', methods=['GET'])
def get_order_status(order_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, status, created_at, total_price FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        order_data = {
            'id': order[0],
            'status': order[1],
            'created_at': order[2].strftime('%Y-%m-%d %H:%M:%S'),
            'total_price': float(order[3])
        }
        
        return jsonify(order_data)
    except Exception as e:
        print(f"Error in get_order_status: {str(e)}")
        return jsonify({'error': 'Failed to get order status'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)