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

# --- Email Configuration ---
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

# --- Helper: Send Email ---
def send_email(to_email, subject, body):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"DEBUG: Email credentials missing. Email to {to_email} not sent.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html')) # Use HTML for better formatting
        
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

@app.route('/api/register', methods=['POST'])
def register_user():
    conn = None
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        mobile = data.get('mobile')
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        
        # Optional fields
        address = data.get('address', '')
        lat = data.get('latitude', None)
        lng = data.get('longitude', None)

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. CHECK IF MOBILE EXISTS
        cur.execute("SELECT id FROM vlh_user WHERE mobile_number = %s", (mobile,))
        if cur.fetchone():
            return jsonify({'success': False, 'error': 'Mobile number already registered'}), 400

        # 2. CHECK IF EMAIL EXISTS
        cur.execute("SELECT id FROM vlh_user WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'success': False, 'error': 'Email address already registered'}), 400

        # 3. IF CLEAR, PROCEED TO INSERT
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        otp = str(random.randint(100000, 999999))
        
        cur.execute("""
            INSERT INTO vlh_user 
            (full_name, mobile_number, email, password_hash, address_full, latitude, longitude, otp_code, otp_created_at, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), FALSE)
            RETURNING id
        """, (full_name, mobile, email, hashed_pw, address, lat, lng, otp))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Send OTP
        print(f"DEBUG: OTP for {email} is ===> {otp} <===") 
        email_body = f"""
        <h2>Welcome to Vanita Lunch Home!</h2>
        <p>Thank you for registering. Please use the OTP below to verify your email address:</p>
        <h1 style="color: #ff8100;">{otp}</h1>
        <p>This OTP is valid for 10 minutes.</p>
        """
        send_email(email, "Verify Your Email - Vanita Lunch Home", email_body)

        return jsonify({'success': True, 'message': 'User registered. Verify OTP.', 'userId': user_id, 'email': email})

    except Exception as e:
        if conn: conn.rollback()
        print(f"Register Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()
            
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    conn = None
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        otp_input = str(data.get('otp', '')).strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch user details along with OTP verification
        cur.execute("""
            SELECT otp_code, id, full_name, mobile_number, address_full 
            FROM vlh_user WHERE email = %s
        """, (email,))
        result = cur.fetchone()
        
        if result:
            db_otp = str(result[0]).strip()
            user_id = result[1]
            full_name = result[2]
            mobile = result[3]
            address = result[4]
            
            if db_otp == otp_input:
                cur.execute("UPDATE vlh_user SET email_verified = TRUE, otp_code = NULL WHERE email = %s", (email,))
                conn.commit()
                
                # Return user data on successful verification for auto-login
                user_data = {
                    'id': user_id,
                    'name': full_name,
                    'email': email,
                    'mobile': mobile,
                    'address': address
                }
                return jsonify({'success': True, 'message': 'Email verified!', 'user': user_data})
            else:
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
        else:
            return jsonify({'success': False, 'error': 'Email not found'}), 400
            
    except Exception as e:
        print(f"Verify Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/login', methods=['POST'])
def login_user():
    conn = None
    try:
        data = request.get_json()
        username = data.get('username') # Can be email or mobile
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
        return jsonify({'menu_items': menu_list}) # Consistent with other endpoints
    except Exception as e:
        print(f"Error in get_menu: {str(e)}")
        return jsonify({'error': 'Failed to load menu'}), 500

@app.route('/api/order', methods=['POST'])
def place_order():
    conn = None
    cur = None
    try:
        data = request.get_json()
        
        # Get fields from request
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        email = data.get('email', '').strip() # New field for email notification
        cart_items = data.get('cart_items', [])
        
        # Validation
        if not name or not mobile:
            return jsonify({'success': False, 'error': 'Name and Mobile are required'}), 400
        if not cart_items or not isinstance(cart_items, list) or len(cart_items) == 0:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        validated_items = []
        subtotal = 0
        items_html_list = "" # For email
        
        for cart_item in cart_items:
            item_id = cart_item.get('id')
            quantity = int(cart_item.get('quantity', 0))
            
            if quantity <= 0: continue
            
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
                
                items_html_list += f"<li>{quantity} x {menu_item[1]} - ₹{item_total:.2f}</li>"
        
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

        # 1. Send Firebase Notification to Admin
        if firebase_admin._apps:
            try:
                message_data = {
                    'id': str(new_order_db_id),
                    'order_id': order_id,
                    'customer_name': name,
                    'total_price': str(total_price),
                    'items': json.dumps(validated_items),
                    'order_source': 'customer',
                    'status': 'pending'
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
            except Exception as e:
                print(f"Error sending Firebase notification: {e}")

        # 2. Send Email Notification to Customer
        if email:
            email_subject = f"Order Confirmation - #{order_id}"
            email_body = f"""
            <html>
            <body>
                <h2 style="color: #ff8100;">Order Placed Successfully!</h2>
                <p>Hi {name},</p>
                <p>Thank you for ordering from Vanita Lunch Home. We have received your order.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Order Summary (#{order_id})</h3>
                    <ul>
                        {items_html_list}
                    </ul>
                    <hr>
                    <h3>Total: ₹{total_price:.2f}</h3>
                </div>
                
                <p><strong>Delivery Address:</strong><br>{address}</p>
                <p>We will contact you on <strong>{mobile}</strong> if required.</p>
                <br>
                <p>Best regards,<br>Vanita Lunch Home Team</p>
            </body>
            </html>
            """
            send_email(email, email_subject, email_body)

        return jsonify({
            'success': True, 
            'message': f'Order placed successfully! Order ID: {order_id}',
            'order_id': order_id
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data'}), 400
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
