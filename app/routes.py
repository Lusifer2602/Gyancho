from flask import render_template, url_for, flash, redirect, request, Blueprint
from app import db, photos, documents
from app.models import User, Upload, Friendship
from flask_login import login_user, login_required, logout_user, current_user
from app.forms import RegistrationForm, LoginForm
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)

# Registration Route
@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, 
                    password=form.password.data, interests=form.interests.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# Login Route
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('main.profile'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

# Profile Route
@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

# File Upload Route
@main.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(request.url)
    filename = secure_filename(file.filename)
    file.save(os.path.join('app/static/uploads', filename))
    new_upload = Upload(filename=filename, filetype=file.content_type, user_id=current_user.id)
    db.session.add(new_upload)
    db.session.commit()
    flash('File uploaded successfully!', 'success')
    return redirect(url_for('main.profile'))

# Friend Request Route
@main.route("/send_friend_request/<int:user_id>", methods=["POST"])
@login_required
def send_friend_request(user_id):
    receiver = User.query.get_or_404(user_id)
    if receiver == current_user:
        flash("You cannot send a friend request to yourself", "danger")
    else:
        friendship = Friendship(sender_id=current_user.id, receiver_id=user_id, status='Pending')
        db.session.add(friendship)
        db.session.commit()
        flash('Friend request sent!', 'success')
    return redirect(url_for('main.profile'))
