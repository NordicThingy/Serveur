import serial  # Importation de la bibliothèque permettant de communiquer avec un port série
import time  # Importation de la bibliothèque pour gérer les délais d'attente
import requests  # Importation de la bibliothèque pour envoyer des requêtes HTTP au serveur

# Configuration du port série
COM_PORT = 'COM17'  # Définition du port série auquel l'appareil est connecté (à adapter si nécessaire)
BAUD_RATE = 115200  # Débit en bauds (bits par seconde), doit correspondre à la configuration de l'appareil (115200 pour les Nordic)

# URL du serveur auquel envoyer les données
SERVER_URL = 'http://127.0.0.1:5000/data'  # Adresse du serveur Flask qui va recevoir les données

# Fonction pour lire les données du port série
def read_from_port():
    try:
        # Ouverture du port série avec les paramètres spécifiés
        with serial.Serial(COM_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connexion établie sur {COM_PORT}")  # Confirmation que la connexion est réussie

            # Boucle infinie pour lire en continu les données du port série
            while True:
                data = ser.readline()  # Lecture d'une ligne complète de données depuis le port série

                if data:  # Vérifie si des données ont bien été reçues
                    try:
                        # Décodage des données en UTF-8 et suppression des espaces inutiles
                        decoded_data = data.decode('utf-8', errors='ignore').strip()

                        if decoded_data:  # Vérifie si la donnée décodée n'est pas vide
                            print(f"Donnée lue : {decoded_data}")  # Affiche la donnée reçue dans la console

                            # Envoi des données au serveur via une fonction défini ci-dessous
                            send_data_to_server(decoded_data)
                    
                    except UnicodeDecodeError as e:
                        # Capture et affiche une erreur si le décodage échoue
                        print(f"Erreur de décodage : {e}")

                time.sleep(0.2)  # Pause de 200ms avant la prochaine lecture pour éviter une surcharge (Dans le cas de l'utilisation du Thingy:91, vérifier aussi l'intervalle d'envoie depuis celui-ci)
                #Attention, l'envoie d'un paquet de données comprenant les 3 axes de l'espace prendra 3 fois le temps ci dessus
    except Exception as e:
        # Capture et affiche une erreur si la connexion au port série échoue
        print(f"Erreur de connexion au port série: {e}")

# Fonction pour envoyer les données au serveur via une requête HTTP POST
def send_data_to_server(data):
    try:
        # Envoi des données sous forme de JSON à l'URL spécifiée
        response = requests.post(SERVER_URL, json={'data': data})

        # Vérifie si la requête a été acceptée par le serveur
        if response.status_code == 200:
            print(f"Donnée envoyée avec succès : {data}")  # Affiche un message de confirmation
        else:
            print(f"Erreur lors de l'envoi des données au serveur : {response.status_code}")  # Affiche l'erreur HTTP reçue
    except Exception as e:
        # Capture et affiche une erreur si la connexion au serveur échoue
        print(f"Erreur de connexion au serveur: {e}")

# Lancement de la lecture du port série lorsque le script est exécuté directement
if __name__ == "__main__":
    read_from_port()  # Appelle la fonction pour commencer à lire les données du port série
