from flask import Flask, request, jsonify, render_template
import random
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# -----------------------
# Temporary storages
# -----------------------
otp_storage = {}          # { email: otp }
pending_users = {}        # { email: { username, password } }

# -----------------------
# Gmail SMTP settings
# -----------------------
EMAIL_ADDRESS = "10c1amdasifahmed@gmail.com"
EMAIL_PASSWORD = "qjta cfve mecf ylot"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# -----------------------
# MongoDB setup
# -----------------------
MONGO_URI = "mongodb+srv://root_db_user:Qwer1234%40123@cluster0.4s40bte.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['musicdb']
users_collection = db['spotifytracks']

# -----------------------
# EMAIL FUNCTION
# -----------------------
def send_email(recipient, otp):
    msg = MIMEText(f"Your Dolsy Music OTP is: {otp}")
    msg['Subject'] = "Dolsy Music OTP Verification"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"OTP sent to {recipient}: {otp}")
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

# -----------------------
# ROUTES
# -----------------------
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register-page')
def register_page():
    return render_template('register.html')

@app.route('/forgotpassword')
def forgotpassword_page():
    return render_template('forgotpassword.html')

@app.route('/otp')
def otp_page():
    return render_template('otp.html')

@app.route('/resetpassword')
def resetpassword_page():
    return render_template('resetpassword.html')

# -----------------------
# API ROUTES
# -----------------------

# 1️⃣ Register temporarily and send OTP
@app.route('/register', methods=['POST'])
def register_temp():
    data = request.get_json()
    username = data.get('username').strip()
    email = data.get('email').strip()
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required.'})

    # Check uniqueness in DB
    if users_collection.find_one({'$or':[{'email': email}, {'username': username}]}):
        return jsonify({'success': False, 'message': 'Username or email already exists.'})

    # Store in pending_users
    pending_users[email] = {
        'username': username,
        'password': password
    }

    # Generate OTP and send
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp
    send_email(email, otp)

    return jsonify({'success': True, 'email': email})

# 2️⃣ Verify OTP and insert user
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')

    if email in otp_storage and otp_storage[email] == otp_input:
        user_data = pending_users.get(email)
        if user_data:
            hashed_password = generate_password_hash(user_data['password'])
            users_collection.insert_one({
                'username': user_data['username'],
                'email': email,
                'password': hashed_password,
                'verified': True
            })
            del otp_storage[email]
            del pending_users[email]
            # redirect flag
            return jsonify({'success': True, 'redirect': '/register-page?verified=true'})
    return jsonify({'success': False, 'message': 'Invalid OTP'})

# 3️⃣ Login
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username').strip()
    password = data.get('password').strip()

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'})
    if not user['verified']:
        return jsonify({'success': False, 'message': 'Please verify your email first.'})
    if check_password_hash(user['password'], password):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Incorrect password.'})

# 4️⃣ Send OTP for forgot password
@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email').strip()
    user = users_collection.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'Email not found.'})
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp
    send_email(email, otp)
    return jsonify({'success': True, 'email': email})

# 5️⃣ Reset password
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')

    if not email or not new_password:
        return jsonify({'success': False, 'message': 'Email and new password required.'})

    hashed_password = generate_password_hash(new_password)
    users_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
    return jsonify({'success': True})

# -----------------------
# RUN APP
# -----------------------
if __name__ == '__main__':
    app.run(debug=True)
