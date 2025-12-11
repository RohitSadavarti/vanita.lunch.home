import pytz
import os
import psycopg2
import bcrypt
import smtplib
import random
import json
import requests  # Added for Green API HTTP requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading  # Added for background Firebase notifications

# --- Firebase Imports ---
import firebase_admin
from firebase_admin import credentials, messaging


def get_db_connection():
    """Create and return a database connection using DATABASE_URL environment variable"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    # Handle Render/Heroku postgres:// vs postgresql:// URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    conn = psycopg2.connect(database_url)
    return conn

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

GREEN_API_ID_INSTANCE = os.environ.get('GREEN_API_ID_INSTANCE', '7105417909')
GREEN_API_TOKEN = os.environ.get('GREEN_API_TOKEN', '5a524925ff024788818b04590bcfa39f5a1efa8e0e0b42c2b8')
GREEN_API_URL = os.environ.get('GREEN_API_URL', 'https://7105.api.greenapi.com')

SMS_API_KEY = os.environ.get('SMS_API_KEY')  # For future SMS implementation
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID')  # For future SMS implementation

# --- Helper: Send Email ---
def send_email(to_email, subject, body):
    """Send an email to the specified recipient with the given subject and body."""
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

def send_otp_whatsapp(mobile_number, otp):
    """Send OTP via WhatsApp using Green API"""
    if not GREEN_API_ID_INSTANCE or not GREEN_API_TOKEN:
        print(f"DEBUG: Green API not configured. WhatsApp OTP to {mobile_number} not sent.")
        print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
        return False
        
    try:
        # Format the mobile number
        clean_mobile = mobile_number.strip().replace("+", "").replace(" ", "").replace("-", "")
        
        # Add country code if not present (assuming India +91)
        if len(clean_mobile) == 10:
            clean_mobile = "91" + clean_mobile
        
        # Green API endpoint
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_ID_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        
        payload = {
            "chatId": f"{clean_mobile}@c.us",
            "message": f"Your Vanita Lunch Home verification code is: {otp}\n\nThis code is valid for 10 minutes. Do not share it with anyone."
        }
        
        headers = {'Content-Type': 'application/json'}
        
        print(f"DEBUG: Sending WhatsApp OTP via Green API to {clean_mobile}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Green-API Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print(f"WhatsApp OTP sent successfully to {clean_mobile}")
            return True
        else:
            print(f"Failed to send WhatsApp OTP: {response.text}")
            print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
            return False
        
    except Exception as e:
        print(f"Failed to send WhatsApp OTP: {e}")
        print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
        return False

def send_otp_sms(mobile_number, otp):
    """Send OTP via SMS - PLACEHOLDER FOR FUTURE IMPLEMENTATION"""
    if not SMS_API_KEY:
        print(f"DEBUG: SMS service not configured. SMS OTP to {mobile_number} not sent.")
        print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
        return False
    
    try:
        # TODO: Implement SMS sending when service is enabled
        # Example with a generic SMS API:
        # response = requests.post('https://sms-api.example.com/send', {
        #     'api_key': SMS_API_KEY,
        #     'sender': SMS_SENDER_ID,
        #     'to': mobile_number,
        #     'message': f'Vanita Lunch Home: Your OTP is {otp}. Valid for 10 minutes.'
        # })
        
        print(f"SMS OTP would be sent to {mobile_number} when service is enabled")
        print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
        return False  # Return False until SMS is implemented
        
    except Exception as e:
        print(f"Failed to send SMS OTP: {e}")
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
        otp_method = data.get('otp_method', 'whatsapp')  # Default to WhatsApp
        
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

        # 2. CHECK IF EMAIL EXISTS (only if email provided)
        if email:
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
        
        print(f"DEBUG: OTP for {mobile} is ===> {otp} <===")
        
        otp_sent = False
        if otp_method == 'whatsapp':
            otp_sent = send_otp_whatsapp(mobile, otp)
        elif otp_method == 'sms':
            otp_sent = send_otp_sms(mobile, otp)
        
        return jsonify({
            'success': True, 
            'message': 'User registered. Verify OTP sent to your WhatsApp.', 
            'userId': user_id, 
            'mobile': mobile,  # Return mobile instead of email for verification
            'otp_method': otp_method,
            'otp_sent': otp_sent
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"Register Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    conn = None
    try:
        data = request.get_json()
        mobile = data.get('mobile', '').strip()
        otp_method = data.get('otp_method', 'whatsapp')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Generate new OTP
        new_otp = str(random.randint(100000, 999999))
        
        # Update OTP in database
        cur.execute("""
            UPDATE vlh_user 
            SET otp_code = %s, otp_created_at = NOW() 
            WHERE mobile_number = %s AND email_verified = FALSE
            RETURNING id
        """, (new_otp, mobile))
        
        result = cur.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'User not found or already verified'}), 400
        
        conn.commit()
        
        # Send OTP
        print(f"DEBUG: New OTP for {mobile} is ===> {new_otp} <===")
        
        otp_sent = False
        if otp_method == 'whatsapp':
            otp_sent = send_otp_whatsapp(mobile, new_otp)
        elif otp_method == 'sms':
            otp_sent = send_otp_sms(mobile, new_otp)
        
        return jsonify({
            'success': True, 
            'message': f'OTP resent via {otp_method.upper()}',
            'otp_sent': otp_sent
        })
        
    except Exception as e:
        print(f"Resend OTP Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()
            
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    conn = None
    try:
        data = request.get_json()
        mobile = data.get('mobile', '').strip()
        otp_input = str(data.get('otp', '')).strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT otp_code, id, full_name, mobile_number, email, address_full, otp_created_at
            FROM vlh_user WHERE mobile_number = %s
        """, (mobile,))
        result = cur.fetchone()
        
        if result:
            db_otp = str(result[0]).strip()
            user_id = result[1]
            full_name = result[2]
            mobile_number = result[3]
            email = result[4]
            address = result[5]
            otp_created_at = result[6]
            
            # Check if OTP is expired (10 minutes)
            if otp_created_at:
                otp_age = datetime.now(otp_created_at.tzinfo) - otp_created_at if otp_created_at.tzinfo else datetime.now() - otp_created_at
                if otp_age.total_seconds() > 600:  # 10 minutes
                    return jsonify({'success': False, 'error': 'OTP expired. Please request a new one.'}), 400
            
            if db_otp == otp_input:
                cur.execute("UPDATE vlh_user SET email_verified = TRUE, otp_code = NULL WHERE mobile_number = %s", (mobile,))
                conn.commit()
                
                # Return user data on successful verification for auto-login
                user_data = {
                    'id': user_id,
                    'name': full_name,
                    'email': email,
                    'mobile': mobile_number,
                    'address': address
                }
                return jsonify({'success': True, 'message': 'Mobile verified successfully!', 'user': user_data})
            else:
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
        else:
            return jsonify({'success': False, 'error': 'Mobile number not found'}), 400
            
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
        email = data.get('email', '').strip()
        cart_items = data.get('cart_items', [])
        
        if not name:
            return jsonify({'success': False, 'error': 'Customer name is required'}), 400
        if not mobile:
            return jsonify({'success': False, 'error': 'Mobile number is required'}), 400
        if not address:
            return jsonify({'success': False, 'error': 'Address is required'}), 400
        if not cart_items or not isinstance(cart_items, list) or len(cart_items) == 0:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        validated_items = []
        subtotal = 0
        items_html_list = ""
        
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
            
            items_html_list += f"<li>{quantity} x {menu_item[1]} - ₹{item_total:.2f}</li>"
        
        total_price = subtotal
        order_id = str(random.randint(10000000, 99999999))
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        now_ist_str = now_ist.strftime('%Y-%m-%d %H:%M:%S.%f')

        cur.execute("""
            INSERT INTO orders (order_id, customer_name, customer_mobile, customer_address, items, subtotal, total_price, status, payment_method, created_at, updated_at, order_status, order_placed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            order_id, name, mobile, address, json.dumps(validated_items), subtotal, total_price, 
            'confirmed', 'Cash', now_ist_str, now_ist_str, 'open', 'customer'
        ))
        
        new_order_db_id = cur.fetchone()[0]
        conn.commit()

        def send_firebase_notification_async(order_db_id, order_id, name, mobile, total_price, validated_items):
            """Sends Firebase notification in a background thread to prevent blocking the UI."""
            if not firebase_admin._apps:
                return

            try:
                message_data = {
                    'id': str(order_db_id),
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
                print(f'✅ Successfully sent notification for order {order_id}:', response)
            except Exception as e:
                print(f"❌ Error sending Firebase notification for order {order_id}: {e}")

        if firebase_admin._apps:
            thread = threading.Thread(
                target=send_firebase_notification_async,
                args=(new_order_db_id, order_id, name, mobile, total_price, validated_items)
            )
            thread.daemon = True
            thread.start()

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
            'order_id': order_id,
            'total_price': total_price
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

@app.route('/api/customer-orders', methods=['GET'])
def get_customer_orders():
    conn = None
    try:
        mobile = request.args.get('mobile', '').strip()
        
        if not mobile:
            return jsonify({'success': False, 'error': 'Mobile number required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch all orders for the customer
        cur.execute("""
            SELECT id, order_id, customer_name, customer_mobile, items, subtotal, total_price, 
                   status, payment_method, created_at, order_status
            FROM orders 
            WHERE customer_mobile = %s 
            ORDER BY created_at DESC
            LIMIT 50
        """, (mobile,))
        
        orders = cur.fetchall()
        
        if not orders:
            return jsonify({'success': True, 'orders': []})
        
        orders_data = []
        for order in orders:
            try:
                items = json.loads(order[4]) if isinstance(order[4], str) else order[4]
                items_list = ', '.join([f"{item.get('quantity', 1)}x {item.get('name', 'Item')}" for item in items])
            except:
                items_list = 'Items'
            
            orders_data.append({
                'id': order[0],
                'order_id': order[1],
                'customer_name': order[2],
                'customer_mobile': order[3],
                'items_list': items_list,
                'subtotal': float(order[5]),
                'total_price': float(order[6]),
                'status': order[7],
                'payment_method': order[8],
                'created_at': order[9].isoformat() if order[9] else None,
                'order_status': order[10]
            })
        
        return jsonify({'success': True, 'orders': orders_data})
    
    except Exception as e:
        print(f"Error fetching customer orders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
