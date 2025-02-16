import serial
import time
import requests

# Configuration du port série
COM_PORT = 'COM17'
BAUD_RATE = 115200  # Assurez-vous que la vitesse du baud rate correspond à celle de votre périphérique

# URL du serveur auquel envoyer les données
SERVER_URL = 'http://127.0.0.1:5000/data'  # Modifiez l'URL si le serveur est sur une autre machine

# Fonction pour lire les données du port série
def read_from_port():
    try:
        with serial.Serial(COM_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connexion établie sur {COM_PORT}")
            while True:
                data = ser.readline()
                if data:
                    try:
                        decoded_data = data.decode('utf-8', errors='ignore').strip()
                        if decoded_data:
                            print(f"Donnée lue : {decoded_data}")
                            send_data_to_server(decoded_data)
                    except UnicodeDecodeError as e:
                        print(f"Erreur de décodage : {e}")
                time.sleep(1)
    except Exception as e:
        print(f"Erreur de connexion au port série: {e}")

# Fonction pour envoyer les données au serveur via une requête HTTP
def send_data_to_server(data):
    try:
        response = requests.post(SERVER_URL, json={'data': data})
        if response.status_code == 200:
            print(f"Donnée envoyée avec succès : {data}")
        else:
            print(f"Erreur lors de l'envoi des données au serveur : {response.status_code}")
    except Exception as e:
        print(f"Erreur de connexion au serveur: {e}")

# Lancer la fonction de lecture du port
if __name__ == "__main__":
    read_from_port()
