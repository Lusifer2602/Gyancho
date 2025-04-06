import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'xlsx', 'docx', 'pptx', 'mp4', 'mp3', 'jpg', 'png', 'avi', 'mov', 'wmv'}
app.secret_key = 'supersecretkey'

# Simple in-memory user database
users_db = {
    "Admin": {"password": "password", "role": "admin"},
    "Student1": {"password": "studentpass", "role": "student"},
    "Teacher": {"password": "teacherpass", "role": "teacher"},
}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

5# Helper function to get all lectures
def get_lectures():
    lectures = []
    if os.path.exists('lectures.txt'):
        with open('lectures.txt', 'r') as f:
            for line in f:
                title, professor, filename = line.strip().split(',')
                lectures.append({'title': title, 'professor': professor, 'filename': filename})
    return lectures

# Helper function to get all announcements
def get_announcements():
    announcements = []
    if os.path.exists('announcements.txt'):
        with open('announcements.txt', 'r') as f:
            for line in f:
                author, content = line.strip().split('|')
                announcements.append({'author': author, 'content': content})
    return announcements

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# New route to upload notes
@app.route('/notes/upload', methods=['GET', 'POST'])
def upload_notes():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect(url_for('view_notes'))

    return render_template('upload_notes.html')

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# New route to view uploaded notes
@app.route('/notes', methods=['GET'])
def view_notes():
    # List all files in the upload folder
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files = [f for f in files if allowed_file(f)]
    return render_template('notes.html', files=files)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_db.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# Admin Dashboard (restricted to admin)
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    return render_template('admin_dashboard.html', users=users_db, lectures=get_lectures())

# Add User (admin only)
@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if username and password and role in ['student', 'teacher']:
            if username not in users_db:
                users_db[username] = {"password": password, "role": role}
                flash(f'User {username} added successfully!', 'success')
            else:
                flash('Username already exists!', 'danger')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid input!', 'danger')
    return render_template('add_user.html')

# Delete User (admin only)
@app.route('/admin/delete_user/<username>')
def delete_user(username):
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if username in users_db and username != 'admin':
        del users_db[username]
        flash(f'User {username} deleted successfully!', 'success')
    else:
        flash('Cannot delete this user!', 'danger')

    return redirect(url_for('admin_dashboard'))

# Delete Lecture (admin only)
@app.route('/admin/delete_lecture/<filename>')
def delete_lecture(filename):
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Remove the lecture from the text file
        with open('lectures.txt', 'r') as f:
            lectures = f.readlines()

        with open('lectures.txt', 'w') as f:
            for lecture in lectures:
                if filename not in lecture:
                    f.write(lecture)

        flash(f'Lecture {filename} deleted successfully!', 'success')
    else:
        flash('Lecture not found!', 'danger')

    return redirect(url_for('admin_dashboard'))

# Publish a lecture (restricted to teachers)
@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if 'role' not in session or session['role'] != 'teacher':
        flash('Access denied! Teachers only.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        professor = request.form['professor']
        file = request.files['video']

        if title and professor and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save the lecture details
            with open('lectures.txt', 'a') as f:
                f.write(f'{title},{professor},{filename}\n')

            flash('Lecture published successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid input or file type!', 'danger')

    return render_template('publish.html')

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'role' not in session or session['role'] != 'teacher':
        flash('Access denied! Teachers only.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        professor = request.form['professor']
        file = request.files['document']

        if title and professor and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save the lecture details
            with open('notes.txt', 'a') as f:
                f.write(f'{title},{professor},{filename}\n')

            flash('Lecture published successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid input or file type!', 'danger')

    return render_template('notes.html')


# Stream a live lecture (restricted to teachers)
@app.route('/stream')
def stream():
    if 'role' not in session or session['role'] != 'teacher':
        flash('Access denied! Teachers only.', 'danger')
        return redirect(url_for('home'))
    return render_template('stream.html')

# View all lectures (accessible to all)
@app.route('/view')
def view_lectures():
    return render_template('view.html', lectures=get_lectures())

# Announcements page (accessible to all)
@app.route('/announcements')
def announcements():
    return render_template('announcements.html', announcements=get_announcements())

# Add Announcement (restricted to teachers and admins)
@app.route('/add_announcement', methods=['GET', 'POST'])
def add_announcement():
    if 'role' not in session or session['role']:
        flash('Access denied! Teachers and Admins only.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        content = request.form['content']

        if content:
            with open('announcements.txt', 'a') as f:
                f.write(f'{session["username"]}|{content}\n')
            flash('Announcement added successfully!', 'success')
            return redirect(url_for('announcements'))
        else:
            flash('Announcement content cannot be empty!', 'danger')

    return render_template('add_announcement.html')

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists('le   tures.txt'):
        open('lectures.txt', 'w').close()
    if not os.path.exists('announcements.txt'):
        open('announcements.txt', 'w').close()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
