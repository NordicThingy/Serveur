import sqlite3

def create_table_if_not_exists():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL)''')  # Crée une table users si elle n'existe pas
    conn.commit()
    conn.close()

def list_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = c.fetchall()
    conn.close()

    return [user[0] for user in users]  # Extrait uniquement les noms d'utilisateur

# Créer la table si elle n'existe pas
create_table_if_not_exists()

# Afficher les utilisateurs existants
users = list_users()
if users:
    print("Utilisateurs enregistrés :")
    for user in users:
        print("-", user)
else:
    print("Aucun utilisateur trouvé.")
