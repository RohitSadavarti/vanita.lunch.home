import pytz
import os
import psycopg2
import bcrypt
import smtplib
import random
import json
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Firebase Imports ---
import firebase_admin
from firebase_admin import credentials, messaging

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
        print("WARNING: FIREBASE_KEY variable not found. Notifications disabled.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    print("WARNING: Firebase notifications disabled.")

app = Flask(__name__)
CORS(app, origins=['*'])

# --- Email Configuration (Get from Environment Variables) ---
SMTP_EMAIL = os.environ.get('MAIL_USERNAME')
SMTP_PASSWORD = os.environ.get('MAIL_PASSWORD')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Database Connection ---
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

# --- Helper: Send OTP Email ---
def send_otp_email(to_email, otp):
    # If credentials are missing, print to console (prevents 500 error)
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"DEBUG: Email credentials missing. OTP for {to_email} is {otp}")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Vanita Lunch Home - Verify Your Email"
        
        body = f"Your Verification OTP is: {otp}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# 1. REGISTER USER (NEW)
@app.route('/api/register', methods=['POST'])
def register_user():
    conn = None
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        mobile = data.get('mobile')
        email = data.get('email', '').strip().lower() # Normalize email
        password = data.get('password')
        address = data.get('address')
        lat = data.get('latitude')
        lng = data.get('longitude')

        # Hash Password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert User 
        # (Note: Requires 'vlh_user' table to verify email/otp columns exist)
        cur.execute("""
            INSERT INTO vlh_user 
            (full_name, mobile_number, email, password_hash, address_full, latitude, longitude, otp_code, otp_created_at, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), FALSE)
            RETURNING id
        """, (full_name, mobile, email, hashed_pw, address, lat, lng, otp))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Send OTP (Prints to console if email fails)
        print(f"DEBUG: OTP for {email} is ===> {otp} <===") 
        send_otp_email(email, otp)

        return jsonify({'success': True, 'message': 'User registered. Verify OTP.', 'userId': user_id})

    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': 'Mobile or Email already exists'}), 400
    except Exception as e:
        if conn: conn.rollback()
        print(f"Register Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

# 2. VERIFY OTP (NEW - Fixed "Invalid OTP" issue)
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    conn = None
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        otp_input = str(data.get('otp', '')).strip() # FORCE STRING & STRIP SPACES
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT otp_code FROM vlh_user WHERE email = %s", (email,))
        result = cur.fetchone()
        
        if result:
            db_otp = str(result[0]).strip() # FORCE STRING & STRIP DB VALUE
            
            print(f"DEBUG CHECK: Input '{otp_input}' vs DB '{db_otp}'") # Log for debugging
            
            if db_otp == otp_input:
                cur.execute("UPDATE vlh_user SET email_verified = TRUE, otp_code = NULL WHERE email = %s", (email,))
                conn.commit()
                return jsonify({'success': True, 'message': 'Email verified!'})
            else:
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
        else:
            return jsonify({'success': False, 'error': 'Email not found'}), 400
            
    except Exception as e:
        print(f"Verify Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

# 3. LOGIN USER (NEW)
@app.route('/api/login', methods=['POST'])
def login_user():
    conn = None
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
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
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({'success': False, 'error': 'Login error'}), 500
    finally:
        if conn: conn.close()

# 4. GET MENU (EXISTING)
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

# 5. PLACE ORDER (EXISTING - FULL CODE)
@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        
        # Log received data for debugging
        print("Received order data:", json.dumps(data, indent=2))
        
        # Get fields from request
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        cart_items = data.get('cart_items', [])
        
        # Validation
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
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        now_ist_str = now_ist.strftime('%Y-%m-%d %H:%M:%S.%f')

        # Insert order into database
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
