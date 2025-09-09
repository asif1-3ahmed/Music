import smtplib
from email.mime.text import MIMEText
import random

# Gmail configuration
EMAIL_ADDRESS = "10c1amdasifahmed@gmail.com"       # Replace with your Gmail
EMAIL_PASSWORD = "qwer1234@123"         # Replace with Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Recipient email (the one you want to send OTP to)
recipient_email = input("Enter recipient email: ")

# Generate a 6-digit OTP
otp = str(random.randint(100000, 999999))

# Create the email message
msg = MIMEText(f"Your Dolsy Music OTP is: {otp}")
msg['Subject'] = "Dolsy Music OTP Verification"
msg['From'] = EMAIL_ADDRESS
msg['To'] = recipient_email

try:
    # Connect to Gmail SMTP server
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()  # Enable security
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Login with Gmail
    server.send_message(msg)  # Send email
    server.quit()
    print(f"OTP sent successfully to {recipient_email}: {otp}")
except Exception as e:
    print("Failed to send OTP. Error:", e)
