import os
import psycopg2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import json
import random # <--- Import the random module

app = Flask(__name__)
# Configure CORS - allow all origins for development, restrict in production
CORS(app, origins=['*'])  # Replace with your actual domain in production

# Remove admin functionality - no longer needed
otp_storage = {}

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
        # --- FIX: Added image_url to the SELECT statement ---
        cur.execute("SELECT id, item_name, description, CAST(price AS FLOAT) as price, category, veg_nonveg, meal_type, availability_time, image_url FROM menu_items ORDER BY category, item_name")
        menu_items = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        menu_list = [dict(zip(column_names, item)) for item in menu_items]
        cur.close()
        conn.close()
        return jsonify(menu_list)
    except Exception as e:
        print(f"Error in get_menu: {str(e)}")
        return jsonify({'error': 'Failed to load menu'}), 500
        
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    mobile = data.get('mobile')

    if not mobile or not (mobile.isdigit() and len(mobile) == 10):
        return jsonify({'success': False, 'error': 'Invalid mobile number.'}), 400

    otp = str(random.randint(100000, 999999))
    expiration_time = datetime.now() + timedelta(minutes=5) # OTP is valid for 5 minutes

    otp_storage[mobile] = {'otp': otp, 'expires_at': expiration_time}
    
    print(f"=====================================")
    print(f"OTP for {mobile} is: {otp}")
    print(f"=====================================")

    return jsonify({'success': True, 'message': 'OTP sent successfully.'})


# API endpoint to place an order
@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        cart_items = data.get('cart_items', [])
        otp_received = data.get('otp', '').strip()

        if not all([name, mobile, address, cart_items, otp_received]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if mobile not in otp_storage:
            return jsonify({'success': False, 'error': 'Please request an OTP first.'}), 400
        
        stored_otp_data = otp_storage[mobile]
        if datetime.now() > stored_otp_data['expires_at']:
            del otp_storage[mobile]
            return jsonify({'success': False, 'error': 'OTP has expired. Please request a new one.'}), 400
            
        if stored_otp_data['otp'] != otp_received:
            return jsonify({'success': False, 'error': 'Invalid OTP.'}), 400
        
        del otp_storage[mobile]

        conn = get_db_connection()
        cur = conn.cursor()
        
        validated_items = []
        subtotal = 0
        
        for cart_item in cart_items:
            item_id = cart_item.get('id')
            quantity = int(cart_item.get('quantity', 0))
            if not item_id or quantity <= 0:
                return jsonify({'error': 'Invalid item or quantity'}), 400
            
            cur.execute("SELECT id, item_name, price FROM menu_items WHERE id = %s", (item_id,))
            menu_item = cur.fetchone()
            if not menu_item:
                return jsonify({'error': f'Menu item with ID {item_id} not found'}), 400
            
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
        
        total_price = subtotal
        order_id = str(random.randint(10000000, 99999999))

        cur.execute("""
            INSERT INTO orders (order_id, customer_name, customer_mobile, items, subtotal, total_price, status, payment_method, created_at, updated_at, order_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id, name, mobile, json.dumps(validated_items), subtotal, total_price, 
            'confirmed', 'Cash', datetime.now(), datetime.now(), 'open'
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Order placed successfully! Your Order ID is: {order_id}'})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error in place_order: {str(e)}")
        return jsonify({'error': 'Failed to place order'}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

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
