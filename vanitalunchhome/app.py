import os
import psycopg2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import random

# --- Firebase Imports ---
import firebase_admin
from firebase_admin import credentials, messaging

# --- Securely Initialize Firebase Admin SDK from Environment Variable ---
try:
    # Render stores JSON environment variables as a string, so we need to parse it
    firebase_key_json = os.environ.get('FIREBASE_KEY')
    if firebase_key_json:
        firebase_credentials = json.loads(firebase_key_json)
        cred = credentials.Certificate(firebase_credentials)
        # Check if the app is already initialized to prevent errors
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    else:
        # If the key is not found, print a warning instead of crashing
        print("WARNING: FIREBASE_KEY environment variable not found. Firebase notifications will be disabled.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # Also print a warning here to prevent a crash
    print("WARNING: Firebase could not be initialized. Notifications will be disabled.")


app = Flask(__name__)
CORS(app, origins=['*'])

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/menu-items', methods=['GET'])
def get_menu():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
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

@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        
        # Log received data for debugging
        print("Received order data:", json.dumps(data, indent=2))
        
        # Get fields from request
        name = data.get('customer_name', '').strip()
        mobile = data.get('customer_mobile', '').strip()
        address = data.get('customer_address', '').strip()
        cart_items = data.get('items', [])
        
        # More detailed validation with specific error messages
        if not name:
            return jsonify({'success': False, 'error': 'Customer name is required'}), 400
        if not mobile:
            return jsonify({'success': False, 'error': 'Mobile number is required'}), 400
        if not address:
            return jsonify({'success': False, 'error': 'Address is required'}), 400
        if not cart_items or not isinstance(cart_items, list) or len(cart_items) == 0:
            return jsonify({'success': False, 'error': 'Cart is empty or invalid'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        validated_items = []
        subtotal = 0
        
        for cart_item in cart_items:
            item_id = cart_item.get('id')
            quantity = int(cart_item.get('quantity', 0))
            
            if not item_id:
                return jsonify({'error': 'Item ID is missing'}), 400
            if quantity <= 0:
                return jsonify({'error': f'Invalid quantity for item ID {item_id}'}), 400
            
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
            })
        
        total_price = subtotal
        order_id = str(random.randint(10000000, 99999999))

        # Insert order into database
        cur.execute("""
            INSERT INTO orders (order_id, customer_name, customer_mobile, items, subtotal, total_price, status, payment_method, created_at, updated_at, order_status, order_placed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            order_id, name, mobile, json.dumps(validated_items), subtotal, total_price, 
            'confirmed', 'Cash', datetime.now(), datetime.now(), 'open', 'customer'
        ))
        
        new_order_db_id = cur.fetchone()[0]
        conn.commit()

        # Send Firebase notification if initialized
        if firebase_admin._apps:
            try:
                message_data = {
                    'id': str(new_order_db_id),
                    'order_id': order_id,
                    'customer_name': name,
                    'customer_phone': mobile,
                    'total_price': str(total_price),
                    'items': json.dumps(validated_items),
                    'order_source': 'customer'
                }

                message = messaging.Message(
                    notification=messaging.Notification(
                        title='🔔 New Customer Order!',
                        body=f'Order #{order_id} from {name} for ₹{total_price:.2f}'
                    ),
                    data=message_data,
                    topic='new_orders'
                )
                response = messaging.send(message)
                print('Successfully sent notification:', response)
            except Exception as e:
                print(f"Error sending Firebase notification: {e}")

        return jsonify({
            'success': True, 
            'message': f'Order placed successfully! Your Order ID is: {order_id}',
            'order_id': order_id
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data'}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in place_order: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to place order: {str(e)}'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)


