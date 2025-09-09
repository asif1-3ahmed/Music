from flask import Flask, request, jsonify, render_template
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Store OTP temporarily
otp_storage = {}

# Gmail settings
EMAIL_ADDRESS = "10c1amdasifahmed@gmail.com"      # Replace with your Gmail
EMAIL_PASSWORD = "qjta cfve mecf ylot"        # Use Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Send email function
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

# Serve HTML pages
@app.route('/forgotpassword')
def forgotpassword_page():
    return render_template('forgotpassword.html')

@app.route('/otp')
def otp_page():
    return render_template('otp.html')

# API: send OTP
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

# API: verify OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    if email in otp_storage and otp_storage[email] == otp_input:
        del otp_storage[email]
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid OTP'})

if __name__ == '__main__':
    app.run(debug=True)
