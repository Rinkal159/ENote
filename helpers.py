from flask import flash, redirect, request

def flash_and_redirect(message, type, route):
    flash(message, type)
    return redirect(route)

def get_email_password():
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email:
        flash("Must provide Email", "danger")
        return None
    if not password:
        flash("Must provide Password", "danger")
        return None
    else:
        return email, password