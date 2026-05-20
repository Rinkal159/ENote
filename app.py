from flask import Flask, render_template, request, session, flash, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helpers import flash_and_redirect, get_email_password
from datetime import datetime
from password_validator import PasswordValidator
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


sql_url = os.getenv("SQL_URL")
db = SQL(sql_url)

schema = PasswordValidator()
schema.min(8)\
    .has().uppercase()\
    .has().lowercase()\
    .has().digits()\
    .has().no().spaces()

@app.route("/getlogin")
def getlogin():
    return render_template("login.html")

# Index page - login
@app.route("/")
def index():
    return render_template("index.html")

# Home
@app.route("/home")
def home():
    notes = db.execute("SELECT * FROM notes WHERE user_id = %s ORDER BY updated_at DESC", session.get("user_id"))
    return render_template("home.html", notes=notes)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        
        result = get_email_password()
        if result is None:
            return redirect("/login")
        
        email, password = result
        
        existed_user = db.execute("SELECT * FROM users WHERE email = %s", email)
        if len(existed_user) != 1 or not check_password_hash(existed_user[0]["password"], password):
            return flash_and_redirect("Invalid credentials", "danger", "/login")
        
        session["user_id"] = existed_user[0]["id"]
        
        return redirect("/home")
        
    return render_template("login.html")
        
# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
  
# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST": 
        result = get_email_password()
        if result is None:
            return redirect("/register")
        email, password = result
        
        username = request.form.get("username")
        if not username:
            return flash_and_redirect("Must provide Username", "danger", "/register")
        
        if len(username) < 4:
            return flash_and_redirect("Username must be longer than 4 characters.", "danger", "/register")
        
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return flash_and_redirect("Must provide Confirm Password", "danger", "/register")
        
        if not schema.validate(password):
            return flash_and_redirect("Password must have at least 8 characters, at least one uppercase letter and one lowercase letter, must contain at least one digit and it cannot contain spaces.", "danger", "/register")
        
        if password != confirmation:
            return flash_and_redirect("Password and Confirm Password do not match", "danger", "/register")
            
        
        hash_password = generate_password_hash(password)
        
        try:
            db.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", username, email, hash_password) 
        except Exception:
            flash("Please log in or try register with different email.", "danger")
            return redirect("/register")
            
            
        user = db.execute("SELECT * FROM users WHERE email = %s", email)
        session["user_id"] = user[0]["id"]

        return redirect("/home")
    
    return render_template("register.html")

# Create note
@app.route("/create")
def create():
    return render_template("create.html")

# Add note
@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    content = request.form.get("content")
    
    if not title:
        return flash_and_redirect("Must provide title", "danger", "/create")
    if not content:
        return flash_and_redirect("Must add some note", "danger", "/create")
    
    db.execute("INSERT INTO notes (user_id, title, content, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)", session.get("user_id"), title, content, datetime.now(), datetime.now())
    
    return redirect("/home")
      
# Show note
@app.route("/note/<int:id>")
def note(id):
    note = db.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", id, session.get("user_id"))
    return render_template("note.html", note=note)

# Update or delete
@app.route("/update", methods=["POST"])
def update():
    title = request.form.get("title")
    content = request.form.get("content")
    id = request.form.get("id")
    action = request.form.get("action")
    
    if action == "update":
        existed_note = db.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", id, session.get("user_id"))

        if title == existed_note[0]["title"] and content == existed_note[0]["content"]:
            return flash_and_redirect("Please make some changes to update a note", "danger", f"/note/{id}")

        db.execute("UPDATE notes SET title = %s, content = %s, updated_at = %s WHERE id = %s AND user_id = %s", title, content, datetime.now(), id, session.get("user_id"))
    else:
        db.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", id, session.get("user_id"))
    
    return redirect("/home")


if __name__ == "__main__":
    app.run(debug=True)