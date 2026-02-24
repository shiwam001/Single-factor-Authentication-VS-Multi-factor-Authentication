from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText

# --------------------
# Flask Setup
# --------------------
app = Flask(__name__)
app.secret_key = "secret123"

# --------------------
# Database Setup
# --------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --------------------
# EMAIL CONFIG (PUT YOUR REAL DETAILS)
# --------------------
EMAIL_ADDRESS = "shiwamsrivastava0105@gmail.com"
EMAIL_PASSWORD = "wzqqziuwubysloys"

# --------------------
# User Model
# --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    last_login = db.Column(db.DateTime)

with app.app_context():
    db.create_all()

# --------------------
# Send OTP Email
# --------------------
def send_otp(email, otp):
    msg = MIMEText(f"Your OTP is {otp}\nValid for 2 minutes.")
    msg["Subject"] = "Login OTP Verification"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

# --------------------
# Routes
# --------------------
@app.route("/")
def home():
    return render_template("login.html")

# -------- Register --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(email=email).first():
            return "Email already registered"

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect("/")

    return render_template("register.html")

# -------- Login (Step 1) --------
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        otp = random.randint(100000, 999999)

        session["otp"] = otp
        session["otp_expiry"] = (datetime.now() + timedelta(minutes=2)).isoformat()
        session["temp_user"] = user.id

        send_otp(user.email, otp)
        return redirect("/otp")

    return "Invalid Email or Password"

# -------- OTP (Step 2) --------
@app.route("/otp", methods=["GET", "POST"])
def otp():
    if request.method == "POST":
        if datetime.now() > datetime.fromisoformat(session["otp_expiry"]):
            return "OTP Expired"

        if str(session["otp"]) == request.form["otp"]:
            user = User.query.get(session["temp_user"])
            user.last_login = datetime.now()
            db.session.commit()

            session.clear()
            session["user"] = user.username
            return redirect("/dashboard")

        return "Invalid OTP"

    return render_template("otp.html")

# -------- Dashboard --------
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        user = User.query.filter_by(username=session["user"]).first()
        return render_template("dashboard.html", user=user)
    return redirect("/")

# -------- Logout --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --------------------
# Run App
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
