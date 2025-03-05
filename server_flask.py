from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import serial  # Bibliothèque pour la communication série
import requests  # Pour envoyer des requêtes HTTP
import sqlite3  # Base de données SQLite pour la gestion des utilisateurs
import csv  # Pour enregistrer les données dans un fichier CSV
import os  # Pour manipuler les fichiers et chemins
from threading import Thread  # Permet d'exécuter la lecture série en parallèle du serveur Flask
from werkzeug.security import generate_password_hash, check_password_hash  # Sécurisation des mots de passe
from datetime import datetime, timedelta  # Gestion des dates et suppression des anciennes données

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clé secrète pour sécuriser les sessions (doit être changée pour la production)

data_store = []  # Stockage temporaire des données reçues
CSV_FILE = "donnees.csv"  # Nom du fichier CSV utilisé pour enregistrer les données

# Définition du chemin du fichier CSV dans le même dossier que le script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "data.csv")

# Initialisation de la base de données SQLite pour les utilisateurs
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Création de la table des utilisateurs si elle n'existe pas
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

# Initialisation de la base de données pour les utilisateurs en attente de validation
def init_pending_users_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Création d'une table pour stocker les demandes d'inscription
    c.execute('''CREATE TABLE IF NOT EXISTS pending_users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, 
                 firstname TEXT, lastname TEXT, birthdate TEXT, service TEXT)''')
    conn.commit()
    conn.close()

# Exécute l'initialisation de la base de données des utilisateurs en attente
init_pending_users_db()

# Fonction pour ajouter un utilisateur avec mot de passe haché
def add_user(username, password):
    hashed_password = generate_password_hash(password)  # Hachage du mot de passe
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

# Fonction pour récupérer le mot de passe haché d'un utilisateur
def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None  # Retourne le mot de passe haché ou None si l'utilisateur n'existe pas

# Fonction pour supprimer un utilisateur
def delete_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

# Exécute l'initialisation de la base de données des utilisateurs
init_db()

# Connexion au port série
def connect_to_serial():
    try:
        serial_port = "COM17"  # Port série utilisé (adapter selon le système)
        baud_rate = 115200  # Vitesse de communication en bauds
        ser = serial.Serial(serial_port, baud_rate, timeout=1)  # Connexion au port série
        print(f"Connexion établie sur {serial_port}")
        return ser
    except serial.SerialException as e:
        print(f"Erreur de connexion au port série : {e}")
        return None

# Route de connexion des utilisateurs
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_password_hash = get_user(username)
        if user_password_hash and check_password_hash(user_password_hash, password):
            session['user'] = username  # Stocke l'utilisateur en session
            return redirect(url_for('display_data'))
        else:
            return "Identifiants incorrects", 401  # Retourne une erreur si les identifiants sont faux
    
    return render_template('login.html')  # Affiche la page de connexion

# Route pour déconnecter un utilisateur
@app.route('/logout')
def logout():
    session.pop('user', None)  # Supprime l'utilisateur de la session
    return redirect(url_for('login'))

# Initialisation du fichier CSV avec un en-tête s'il n'existe pas
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "data"])  # Ajoute les en-têtes au fichier CSV

# Fonction pour nettoyer les données de plus de 7 jours
def clean_old_data():
    now = datetime.now()
    new_rows = []

    with open(CSV_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # Récupère l'en-tête
        for row in reader:
            if len(row) < 2:
                continue
            try:
                row_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                if row_time >= now - timedelta(days=7):  # Garde uniquement les données des 7 derniers jours
                    new_rows.append(row)
            except ValueError:
                print(f"Erreur de format de date, ligne ignorée : {row}")

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(new_rows)

# Nettoyage automatique avant chaque requête
@app.before_request
def before_request():
    clean_old_data()

# Route pour recevoir et stocker les données
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    if 'data' in data:
        data_store.append(data['data'])  # Stockage en mémoire
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['data']])
    return jsonify({"status": "success"})

# Route pour afficher la page des données
@app.route('/')
def display_data():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Route pour récupérer les données stockées
@app.route('/get_data', methods=['GET'])
def get_data():
    if 'user' not in session:
        return jsonify({"error": "Non autorisé"}), 403
    return jsonify({"data": data_store})

# Route pour télécharger le fichier CSV
@app.route('/download')
def download():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    else:
        return "Le fichier CSV n'existe pas encore.", 404

# Fonction pour lire les données du port série et les envoyer au serveur
def read_serial_data():
    ser = connect_to_serial()
    if ser:
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()  # Lecture et décodage des données
                print(f"Donnée lue : {data}")
                if data:
                    try:
                        response = requests.post('http://127.0.0.1:5000/data', json={'data': data})
                        if response.status_code == 200:
                            print(f"Donnée envoyée avec succès : {data}")
                    except requests.exceptions.RequestException as e:
                        print(f"Erreur de connexion au serveur : {e}")

# Exécution du serveur Flask et du thread de lecture série
if __name__ == '__main__':
    serial_thread = Thread(target=read_serial_data)  # Lancement de la lecture série en arrière-plan
    serial_thread.daemon = True  # Arrêt automatique du thread à la fermeture du programme
    serial_thread.start()

    app.run(host='127.0.0.1', port=5000, debug=True)  # Lancement du serveur Flask
