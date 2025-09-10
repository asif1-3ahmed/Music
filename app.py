from flask import Flask, request, jsonify, render_template
import random
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Store OTP temporarily
otp_storage = {}

# Gmail settings
EMAIL_ADDRESS = "10c1amdasifahmed@gmail.com"
EMAIL_PASSWORD = "qjta cfve mecf ylot"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# MongoDB setup
MONGO_URI = "mongodb+srv://root_db_user:Qwer1234%40123@cluster0.4s40bte.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['musicdb']
users_collection = db['spotifytracks']

# ====================
# EMAIL FUNCTION
# ====================
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

<<<<<<< HEAD
# ✅ New route for root URL
@app.route('/')
def home():
    return render_template('forgotpassword.html')

# Serve HTML pages
=======
# ====================
# ROUTES
# ====================

# Root route → login page
@app.route('/')
def home():
    return render_template('login.html')

# Registration page
@app.route('/register-page')
def register_page():
    return render_template('register.html')

# Forgot password page
>>>>>>> d79d539 (Add login, registration, OTP pages with MongoDB integration)
@app.route('/forgotpassword')
def forgotpassword_page():
    return render_template('forgotpassword.html')

# OTP page
@app.route('/otp')
def otp_page():
    return render_template('otp.html')

# ====================
# API ROUTES
# ====================

# Register user
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'})

    if users_collection.find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Email already registered'})

    hashed_password = generate_password_hash(password)

    users_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password
    })

    return jsonify({'success': True, 'message': 'User registered successfully!'})

# Login user
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'All fields are required'})

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    if check_password_hash(user['password'], password):
        return jsonify({'success': True, 'message': 'Login successful!'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect password'})

# Send OTP
@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email required.'})
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp
    if send_email(email, otp):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Failed to send OTP.'})

# Verify OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    if email in otp_storage and otp_storage[email] == otp_input:
        del otp_storage[email]
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid OTP'})

# ====================
# RUN APP
# ====================
if __name__ == '__main__':
    app.run(debug=True)
