from flask import Flask, render_template, request, redirect, url_for, session
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import csv

import secrets
secret_key = secrets.token_hex(24)  # Generates a 48-character hex string
print(secret_key)
app = Flask(__name__)

# Dummy admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Load known faces
known_face_encodings = []
known_face_names = []

photos_dir ="students"
for filename in os.listdir(photos_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        path = os.path.join(photos_dir, filename)
        image = face_recognition.load_image_file(path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_face_encodings.append(encoding[0])
            name = os.path.splitext(filename)[0].capitalize()
            known_face_names.append(name)
def load_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir('photos'):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join('photos', filename)
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                known_face_encodings.append(encoding[0])
                name = os.path.splitext(filename)[0].capitalize()
                known_face_names.append(name)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    if not session.get('admin'):
        return redirect(url_for('login'))

    uploaded_image = face_recognition.load_image_file('static/uploaded.jpg')
    face_locations = face_recognition.face_locations(uploaded_image)
    face_encodings = face_recognition.face_encodings(uploaded_image, face_locations)

    names_found = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            names_found.append(name)
            log_attendance(name)

    message = f"Recognized: {', '.join(names_found)}" if names_found else "No known faces found."
    return render_template('dashboard.html', message=message)

@app.route('/attendance_records')
def attendance_records():
    if not session.get('admin'):
        return redirect(url_for('login'))

    attendance_folder = 'attendance'
    records = []
    if os.path.exists(attendance_folder):
        for filename in sorted(os.listdir(attendance_folder)):
            path = os.path.join(attendance_folder, filename)
            with open(path, 'r') as f:
                reader = csv.reader(f)
                data = list(reader)
                records.append({'date': filename.replace('.csv', ''), 'data': data})
    return render_template('attendance.html', records=records)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

def log_attendance(name):
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")
    filename = os.path.join('attendance', f'{current_date}.csv')
    os.makedirs('attendance', exist_ok=True)

    with open(filename, 'a+', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, time_now])

if __name__ == '__main__':
    app.run(debug=True)
