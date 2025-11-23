import os
import json
import random
import datetime
import smtplib
import bcrypt  # Added for password hashing
import pytz
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta

# --- Firebase Imports ---
import firebase_admin
from firebase_admin import credentials, messaging

# --- Email Configuration (Add these to your environment variables) ---
# If you don't have these set yet, the code will default to None and email sending will fail safely.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ.get('rohit.o.cs23073@gmail.com') 
SMTP_PASSWORD = os.environ.get('Clashe@7494')

# --- Securely Initialize Firebase Admin SDK ---
try:
    firebase_key_json = os.environ.get('FIREBASE_KEY')
    if firebase_key_json:
        firebase_credentials = json.loads(firebase_key_json)
        cred = credentials.Certificate(firebase_credentials)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    else:
        print("WARNING: FIREBASE_KEY not found. Notifications disabled.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    print("WARNING: Firebase could not be initialized.")


app = Flask(__name__)
CORS(app, origins=['*'])

# --- Helper Functions ---

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

def send_otp_email(to_email, otp):
    try:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("Email credentials missing in environment variables.")
            return False

        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Vanita Lunch Home - Verify your Email"
        
        body = f"Your Verification OTP is: {otp}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# --- Routes ---

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

@app.route('/api/register', methods=['POST'])
def register_user():
    conn = None
    try:
        data = request.get_json()
        
        # Extract data
        full_name = data.get('full_name')
        mobile = data.get('mobile')
        email = data.get('email')
        password = data.get('password')
        address = data.get('address')
        lat = data.get('latitude')
        lng = data.get('longitude')

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert User with OTP
        # Ensure your table 'vlh_user' exists with these columns
        cur.execute("""
            INSERT INTO vlh_user 
            (full_name, mobile_number, email, password_hash, address_full, latitude, longitude, otp_code, otp_created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (full_name, mobile, email, hashed_pw, address, lat, lng, otp))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Send Email
        # Uncomment the line below when you have set MAIL_USERNAME and MAIL_PASSWORD in Render env vars
        # send_otp_email(email, otp) 
        
        # For testing, we verify immediately or print OTP to console
        print(f"DEBUG: OTP for {email} is {otp}")

        return jsonify({'success': True, 'message': 'User registered. Please verify OTP.', 'userId': user_id})

    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'Mobile or Email already exists'}), 400
    except Exception as e:
        if conn: conn.rollback()
        print(f"Register Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        data = request.get_json()
        email = data.get('email')
        otp_input = data.get('otp')
        
        cur.execute("SELECT otp_code FROM vlh_user WHERE email = %s", (email,))
        result = cur.fetchone()
        
        if result and result[0] == otp_input:
            cur.execute("UPDATE vlh_user SET email_verified = TRUE, otp_code = NULL WHERE email = %s", (email,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Email verified successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
            
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login_user():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        data = request.get_json()
        username = data.get('username') # Mobile or Email
        password = data.get('password')
        
        # Check against mobile or email
        cur.execute("""
            SELECT id, full_name, mobile_number, email, password_hash, address_full, latitude, longitude 
            FROM vlh_user 
            WHERE mobile_number = %s OR email = %s
        """, (username, username))
        
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            return jsonify({
                'success': True,
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'mobile': user[2],
                    'email': user[3],
                    'address': user[5],
                    'lat': user[6],
                    'lng': user[7]
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        print("Received order data:", json.dumps(data, indent=2))
        
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        cart_items = data.get('cart_items', [])
        
        if not name or not mobile or not address:
            return jsonify({'success': False, 'error': 'Name, Mobile, and Address are required'}), 400
        if not cart_items or len(cart_items) == 0:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        validated_items = []
        subtotal = 0
        
        for cart_item in cart_items:
            item_id = cart_item.get('id')
            quantity = int(cart_item.get('quantity', 0))
            
            if not item_id or quantity <= 0:
                continue

            cur.execute("SELECT id, item_name, price FROM menu_items WHERE id = %s", (item_id,))
            menu_item = cur.fetchone()
            
            if menu_item:
                actual_price = float(menu_item[2])
                item_total = actual_price * quantity
                subtotal += item_total
                
                validated_items.append({
                    'id': menu_item[0],
                    'name': menu_item[1],
                    'price': actual_price,
                    'quantity': quantity,
                })
        
        if not validated_items:
             return jsonify({'error': 'No valid items in cart'}), 400

        total_price = subtotal
        order_id = str(random.randint(10000000, 99999999))
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        now_ist_str = now_ist.strftime('%Y-%m-%d %H:%M:%S.%f')

        cur.execute("""
            INSERT INTO orders (order_id, customer_name, customer_mobile, items, subtotal, total_price, status, payment_method, created_at, updated_at, order_status, order_placed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            order_id, name, mobile, json.dumps(validated_items), subtotal, total_price, 
            'confirmed', 'Cash', now_ist_str, now_ist_str, 'open', 'customer'
        ))
        
        new_order_db_id = cur.fetchone()[0]
        conn.commit()

        # Send Firebase notification
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
                messaging.send(message)
                print('Successfully sent notification.')
            except Exception as e:
                print(f"Error sending Firebase notification: {e}")

        return jsonify({
            'success': True, 
            'message': f'Order placed successfully! Your Order ID is: {order_id}',
            'order_id': order_id
        })
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error in place_order: {str(e)}")
        return jsonify({'error': f'Failed to place order: {str(e)}'}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
