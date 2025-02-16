# Configuration du serveur Flask pour afficher les données sur une interface et sauvegarder les données en CSV

**Configuration nécessaire:**
Avoir effectué le paramétrage disponible sur le Github nRF5340DK

**Configuration et démarrage du serveur**
- Télécharger le dossier sur votre ordinateur
- Copier le chemin d'accès du fichier nommé server et tapez ensuite la commande dans powershell : python "Chemin d'accès sans les guillemets"
- Copier ensuite le chemin d'accès du fichier nommé server_flask et tapez ensuite la commande dans powershell : python "Chemin d'accès sans les guillemets"
- Les deux fichier doivent être démarré dans deux fenêtres différentes

**Démarrage et accès à l'interface**
- Cliquez sur le lien suivant : http://127.0.0.1:5000/login
- Pour voir la liste des utilisateurs pouvant accéder au serveur, exécutez le programme suivant dans powershell : python "Chemin d'accès au fichier liste_utilisateurs.py"
- Pour ajouter un utilisateur, ouvrez le fichier "ajout utilisateur" dans VS Code et modifiez les deux textes entre guillemets dans la ligne add_user, le premier est le nom d'utilisateur et le second est le mot de passe, exécutez ensuite le programme dans powershell
- Pour supprimer un utilisateur, ouvrez le fichier "supprimer utilisateur" dans VS Code et modifier le texte entre guillements dans la ligne username_to_delete, le texte à mettre est le nom d'utilisateur, exécutez le programme dans powershell
- Une fois connecté, vous pouvez télécharger un fichier csv avec toutes les données sur la page principale
