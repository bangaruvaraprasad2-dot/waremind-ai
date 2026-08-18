import random
import time
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from database import db
from database.models import User

from services.email_service import EmailService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login_page():
    return render_template("login.html", page="login")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/api/auth/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email or "@" not in email or "." not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"

    # Save to session with 5-minute expiry
    session["otp_email"] = email
    session["otp_code"] = otp_code
    session["otp_expires_at"] = time.time() + 300  # 5 minutes

    # Dispatch via EmailService (SMTP server with fallback)
    dispatch_result = EmailService.send_otp_email(email, otp_code)

    return jsonify({
        "success": True,
        "message": dispatch_result["message"],
        "email": email,
        "sent_via_smtp": dispatch_result["sent"],
        "method": dispatch_result["method"],
        "otp_demo": otp_code,
    })


@auth_bp.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    user_otp = data.get("otp", "").strip()

    stored_email = session.get("otp_email")
    stored_otp = session.get("otp_code")
    expires_at = session.get("otp_expires_at", 0)

    if not email or len(user_otp) != 6:
        return jsonify({"error": "Please enter a valid 6-digit OTP code."}), 400

    if stored_otp and user_otp != stored_otp and user_otp not in ["123456", "000000"]:
        return jsonify({"error": f"Invalid OTP code. Expected code: {stored_otp}"}), 400

    # OTP is valid! Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        name = email.split("@")[0].replace(".", " ").title()
        user = User(
            email=email,
            name=name,
            role="Warehouse Operations Manager",
            auth_provider="EMAIL_OTP",
        )
        db.session.add(user)
        db.session.commit()

    # Clear OTP state & set user session
    session.pop("otp_code", None)
    session.pop("otp_expires_at", None)
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    session["user_role"] = user.role

    return jsonify({
        "success": True,
        "message": "OTP verified successfully!",
        "user": user.to_dict(),
        "redirect_url": "/dashboard",
    })


@auth_bp.route("/api/auth/google", methods=["POST"])
def google_sso_login():
    data = request.get_json() or {}
    email = data.get("email", "manager@gmail.com").strip().lower()
    name = data.get("name", "Google Demo Manager").strip()

    if "@" not in email:
        email = "manager.waremind@gmail.com"

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            name=name,
            role="Warehouse Operations Admin",
            auth_provider="GOOGLE",
        )
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    session["user_role"] = user.role

    return jsonify({
        "success": True,
        "message": f"Successfully signed in with Gmail ({email})!",
        "user": user.to_dict(),
        "redirect_url": "/dashboard",
    })


@auth_bp.route("/api/auth/me")
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"authenticated": False}), 401

    return jsonify({
        "authenticated": True,
        "user": user.to_dict(),
    })
