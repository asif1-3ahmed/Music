from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import random, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "supersecret"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["dolsy_music"]
users = db["users"]

# Store OTPs temporarily
otp_storage = {}

# Gmail SMTP
EMAIL_ADDRESS = "yourmail@gmail.com"      # replace
EMAIL_PASSWORD = "your-app-password"      # replace

def send_otp(email, otp):
    msg = MIMEText(f"Your OTP for Dolsy Music is: {otp}")
    msg["Subject"] = "Dolsy Music - OTP Verification"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())

@app.route("/")
def index():
    return redirect(url_for("register"))

# ---------------- Register ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # check if email exists
        if users.find_one({"email": email}):
            return "❌ Email already registered!"

        otp = str(random.randint(100000, 999999))
        otp_storage[email] = {"otp": otp, "username": username, "password": password}
        send_otp(email, otp)
        session["pending_email"] = email
        return redirect(url_for("otp"))
    return render_template("register.html")

# ---------------- OTP ----------------
@app.route("/otp", methods=["GET", "POST"])
def otp():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("register"))

    if request.method == "POST":
        entered_otp = request.form["otp"]
        if otp_storage.get(email) and otp_storage[email]["otp"] == entered_otp:
            data = otp_storage[email]
            users.insert_one({
                "username": data["username"],
                "email": email,
                "password": data["password"]
            })
            del otp_storage[email]
            session.pop("pending_email", None)
            return redirect(url_for("account_created"))
        else:
            return "❌ Invalid OTP!"
    return render_template("otp.html")

# ---------------- Account Created ----------------
@app.route("/account_created")
def account_created():
    return render_template("account_created.html")

# ---------------- Home ----------------
@app.route("/home")
def home():
    return render_template("home.html", username="Hello")

# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({"email": email, "password": password})
        if user:
            return redirect(url_for("home"))
        return "❌ Invalid credentials!"
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
