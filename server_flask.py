from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import serial
import requests
import sqlite3
import csv
import os
from threading import Thread
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change cette clé pour plus de sécurité

data_store = []
CSV_FILE = "data.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Récupère le dossier du script
CSV_FILE = os.path.join(BASE_DIR, "data.csv")  # Fichier CSV dans le même dossier que le script

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def init_pending_users_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pending_users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, 
                 firstname TEXT, lastname TEXT, birthdate TEXT, service TEXT)''')
    conn.commit()
    conn.close()

init_pending_users_db()

def add_user(username, password):
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def delete_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

init_db()

# Connexion au port série
def connect_to_serial():
    try:
        serial_port = "COM17"
        baud_rate = 115200
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        print(f"Connexion établie sur {serial_port}")
        return ser
    except serial.SerialException as e:
        print(f"Erreur de connexion au port série : {e}")
        return None

# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_password_hash = get_user(username)
        if user_password_hash and check_password_hash(user_password_hash, password):
            session['user'] = username
            return redirect(url_for('display_data'))
        else:
            return "Identifiants incorrects", 401
    
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Initialisation du fichier CSV avec en-tête si inexistant
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "data"])

# Fonction de nettoyage des données de plus de 7 jours
def clean_old_data():
    now = datetime.now()
    new_rows = []

    with open(CSV_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                row_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                if row_time >= now - timedelta(days=7):
                    new_rows.append(row)
            except ValueError:
                print(f"Erreur de format de date, ligne ignorée : {row}")

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(new_rows)

@app.before_request
def before_request():
    clean_old_data()

# Route pour recevoir et stocker les données
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    if 'data' in data:
        data_store.append(data['data'])
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['data']])
    return jsonify({"status": "success"})

# Route pour afficher la page avec les données
@app.route('/')
def display_data():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Route pour récupérer les données
@app.route('/get_data', methods=['GET'])
def get_data():
    if 'user' not in session:
        return jsonify({"error": "Non autorisé"}), 403
    return jsonify({"data": data_store})

# Route pour télécharger les données au format CSV
@app.route('/download')
def download():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    else:
        return "Le fichier CSV n'existe pas encore.", 404

# Lecture des données du port série et envoi au serveur
def read_serial_data():
    ser = connect_to_serial()
    if ser:
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                print(f"Donnée lue : {data}")
                if data:
                    try:
                        response = requests.post('http://127.0.0.1:5000/data', json={'data': data})
                        if response.status_code == 200:
                            print(f"Donnée envoyée avec succès : {data}")
                    except requests.exceptions.RequestException as e:
                        print(f"Erreur de connexion au serveur : {e}")

if __name__ == '__main__':
    serial_thread = Thread(target=read_serial_data)
    serial_thread.daemon = True
    serial_thread.start()
    app.run(host='127.0.0.1', port=5000, debug=True)
