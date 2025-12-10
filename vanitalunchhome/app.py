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

from twilio.rest import Client as TwilioClient

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

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio Sandbox default

SMS_API_KEY = os.environ.get('SMS_API_KEY')  # For future SMS implementation
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID')  # For future SMS implementation

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("Twilio client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Twilio client: {e}")
else:
    print("WARNING: Twilio credentials not found. WhatsApp OTP disabled.")

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

def send_otp_whatsapp(mobile_number, otp):
    """Send OTP via WhatsApp using Twilio API"""
    if not twilio_client:
        print(f"DEBUG: Twilio not configured. WhatsApp OTP to {mobile_number} not sent.")
        print(f"DEBUG: OTP for {mobile_number} is ===> {otp} <===")
        return False
        
    try:
        # Format the mobile number (ensure it has country code)
        formatted_number = mobile_number.strip()
        if not formatted_number.startswith('+'):
            if formatted_number.startswith('91'):
                formatted_number = '+' + formatted_number
            else:
                formatted_number = '+91' + formatted_number
        
        # Add whatsapp: prefix for Twilio
        whatsapp_to = f"whatsapp:{formatted_number}"
        
        message_body = f"🍽️ *Vanita Lunch Home*\n\nYour verification code is: *{otp}*\n\nThis code is valid for 10 minutes. Do not share it with anyone."
        
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=whatsapp_to
        )
        
        print(f"WhatsApp OTP sent successfully to {formatted_number}. SID: {message.sid}")
        return True
        
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
