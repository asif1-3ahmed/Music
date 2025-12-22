from flask import Flask, request, redirect, url_for, render_template, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os
import requests

# -------------------- APP --------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

# -------------------- DATABASE --------------------
MONGO_URI = "mongodb+srv://root_db_user:MdbSecurity%40secure%40123%4012@cluster0.4s40bte.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["musicdb"]
users = db["users"]

# -------------------- TEMP STORAGE --------------------
otp_storage = {}        # { email: otp }
pending_users = {}      # { email: { username, password } }

# -------------------- RESEND --------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

FROM_EMAIL = "Dolsy Music <onboarding@resend.dev>"

def send_email(recipient, otp):
    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY not set")
        return False

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Dolsy Music <onboarding@resend.dev>",
                "to": recipient,
                "subject": "Dolsy Music OTP",
                "html": f"<h1>Your OTP is {otp}</h1>"
            },
            timeout=10
        )

        print("📨 Resend status:", r.status_code)
        print("📨 Resend response:", r.text)

        return r.status_code == 200

    except Exception as e:
        print("❌ Resend exception:", e)
        return False

# -------------------- PAGES --------------------
@app.route("/")
def first_page():
    return render_template("firstpage.html")

@app.route("/animation")
def animation_page():
    return render_template("html.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template(
        "register.html",
        verified=request.args.get("verified", ""),
        created_username=request.args.get("username", "")
    )

@app.route("/otp")
def otp_page():
    return render_template(
        "otp.html",
        email=request.args.get("email"),
        source=request.args.get("source")
    )

@app.route("/forgotpassword")
def forgotpassword_page():
    return render_template("forgotpassword.html")

@app.route("/resetpassword")
def resetpassword_page():
    return render_template(
        "resetpassword.html",
        email=request.args.get("email")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# -------------------- REGISTER --------------------
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not username or not email or not password:
        return "<script>alert('All fields required');history.back();</script>"

    if users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return "<script>alert('User already exists');history.back();</script>"

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp
    pending_users[email] = {"username": username, "password": password}

    if not send_email(email, otp):
        return "<script>alert('OTP sending failed');history.back();</script>"

    return redirect(url_for("otp_page", email=email, source="register"))

# -------------------- VERIFY OTP --------------------
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email")
    otp = request.form.get("otp")
    source = request.form.get("source")

    if email in otp_storage and otp_storage[email] == otp:

        if source == "register":
            user = pending_users[email]
            users.insert_one({
                "username": user["username"],
                "email": email,
                "password": generate_password_hash(user["password"]),
                "verified": True
            })
            otp_storage.pop(email)
            pending_users.pop(email)
            return redirect(url_for("register_page", verified="true", username=user["username"]))

        if source == "forgot":
            otp_storage.pop(email)
            return redirect(url_for("resetpassword_page", email=email))

    return "<script>alert('Invalid OTP');history.back();</script>"

# -------------------- LOGIN --------------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = users.find_one({"username": username})
    if not user:
        return "<script>alert('User not found');history.back();</script>"

    if not user.get("verified"):
        return "<script>alert('Email not verified');history.back();</script>"

    if check_password_hash(user["password"], password):
        session["username"] = username
        return redirect("/main")

    return "<script>alert('Wrong password');history.back();</script>"

# -------------------- MAIN --------------------
@app.route("/main")
def main_page():
    if "username" not in session:
        return redirect(url_for("login_page"))
    return render_template("main.html", username=session["username"])

# -------------------- FORGOT PASSWORD --------------------
@app.route("/send-otp", methods=["POST"])
def send_otp_forgot():
    email = request.form.get("email", "").strip()

    if not users.find_one({"email": email}):
        return "<script>alert('Email not found');history.back();</script>"

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    if not send_email(email, otp):
        return "<script>alert('OTP sending failed');history.back();</script>"

    return redirect(url_for("otp_page", email=email, source="forgot"))

@app.route("/reset-password", methods=["POST"])
def reset_password():
    email = request.form.get("email")
    new_password = request.form.get("password")

    users.update_one(
        {"email": email},
        {"$set": {"password": generate_password_hash(new_password)}}
    )
    return redirect(url_for("login_page"))

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
