from flask import Flask, request, redirect, url_for, render_template
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ----------------------- MongoDB Setup -----------------------
MONGO_URI = "mongodb+srv://root_db_user:Qwer1234%40123@cluster0.4s40bte.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['musicdb']
users_collection = db['users']

# ----------------------- Temporary Storages -----------------------
otp_storage = {}       # { email: otp }
pending_users = {}     # { email: { username, password } }

# ----------------------- Email Settings -----------------------
EMAIL_ADDRESS = "10c1amdasifahmed@gmail.com"
EMAIL_PASSWORD = "qjta cfve mecf ylot"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

# ----------------------- ROUTES -----------------------

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register-page')
def register_page():
    verified = request.args.get('verified', '')
    username = request.args.get('username', '')
    return render_template('register.html', verified=verified, created_username=username)

@app.route('/forgotpassword')
def forgotpassword_page():
    return render_template('forgotpassword.html')

@app.route('/otp')
def otp_page():
    email = request.args.get('email')
    source = request.args.get('source')
    return render_template('otp.html', email=email, source=source)

@app.route('/resetpassword')
def resetpassword_page():
    email = request.args.get('email')
    return render_template('resetpassword.html', email=email)

@app.route('/home')
def home_page():
    username = request.args.get('username', 'User')
    return render_template('home.html', username=username)

# ----------------------- API -----------------------

# Registration
@app.route('/register', methods=['POST'])
def register_temp():
    username = request.form.get('username').strip()
    email = request.form.get('email').strip()
    password = request.form.get('password')

    if not username or not email or not password:
        return "<script>alert('All fields are required'); window.history.back();</script>"

    if users_collection.find_one({'$or':[{'username': username}, {'email': email}]}):
        return "<script>alert('Username or email already exists'); window.history.back();</script>"

    pending_users[email] = {'username': username, 'password': password}

    otp = str(random.randint(100000,999999))
    otp_storage[email] = otp
    send_email(email, otp)

    return redirect(url_for('otp_page', email=email, source='register'))

# Verify OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp_input = request.form.get('otp')
    source = request.form.get('source')  # "register" or "forgot"

    if email in otp_storage and otp_storage[email] == otp_input:
        if source == "register":
            user_data = pending_users.get(email)
            if user_data:
                hashed_pass = generate_password_hash(user_data['password'])
                users_collection.insert_one({
                    'username': user_data['username'],
                    'email': email,
                    'password': hashed_pass,
                    'verified': True
                })
                del otp_storage[email]
                del pending_users[email]
                # redirect to register page with success animation
                return redirect(url_for('register_page', verified='true', username=user_data['username']))
        elif source == "forgot":
            del otp_storage[email]
            return redirect(url_for('resetpassword_page', email=email))
    return "<script>alert('Invalid OTP'); window.history.back();</script>"

# Login
@app.route('/login', methods=['POST'])
def login_user():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()

    user = users_collection.find_one({'username': username})
    if not user:
        return "<script>alert('User not found'); window.history.back();</script>"
    if not user.get('verified', False):
        return "<script>alert('Please verify your email first'); window.history.back();</script>"
    if check_password_hash(user['password'], password):
        return redirect(url_for('home_page', username=username))
    return "<script>alert('Incorrect password'); window.history.back();</script>"

# Forgot Password
@app.route('/send-otp', methods=['POST'])
def send_otp_forgot():
    email = request.form.get('email').strip()
    user = users_collection.find_one({'email': email})
    if not user:
        return "<script>alert('Email not found'); window.history.back();</script>"

    otp = str(random.randint(100000,999999))
    otp_storage[email] = otp
    send_email(email, otp)

    return redirect(url_for('otp_page', email=email, source='forgot'))

# Reset Password
@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    new_password = request.form.get('password')

    if not email or not new_password:
        return "<script>alert('Email and password required'); window.history.back();</script>"

    user = users_collection.find_one({'email': email})
    if user and check_password_hash(user['password'], new_password):
        return "<script>alert('Cannot use previous password'); window.history.back();</script>"

    hashed_password = generate_password_hash(new_password)
    users_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
    return redirect(url_for('login_page'))

# ----------------------- RUN -----------------------
if __name__ == '__main__':
    app.run(debug=True)
