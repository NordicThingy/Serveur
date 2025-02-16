from server_flask import delete_user

username_to_delete = "tartiflette"
delete_user(username_to_delete)
print(f"Utilisateur '{username_to_delete}' supprimé !")
