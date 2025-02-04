import sqlite3
import getpass
import os
import hashlib

import connector
import maj

class Login:
    def __init__(self, db_name="bdd.db"):
        self.conn = connector.conn
        self.cursor = self.conn.cursor()
        self.userConnected = False
        self.current_user = None
        self.current_rank = None
        self.erreur = None

    def user_exists(self, username):
        """Check if a user exists in the database."""
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone() is not None

    def validate_password(self, username, password):
        """Validate the password for a given username."""
        self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result and result[0] == password:
            return True
        return False
    def logout(self):
        self.userConnected = None
        self.current_user = None
        self.current_rank = None
        print("Vous avez bien été déconnecté.")
        self.interface_one()

    def user_is_desactive(self, username):
        """Check if the user is already disabled"""
        self.cursor.execute("SELECT disabled FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result and result[0] == 1:
            return True
        return False
    def desactive_user(self,username):
        self.cursor.execute("UPDATE users SET disabled = ? WHERE username = ?", (1, username,))
        self.conn.commit()
        print(f"L'utilisateur {username} a bien été désactivé.")
        self.profile_interface()
    def active_user(self,username):
        self.cursor.execute("UPDATE users SET disabled = ? WHERE username = ?", (0, username,))
        self.conn.commit()
        self.erreur = f"L'utilisateur {username} a bien été activé."
        self.profile_interface()


    def message_exist(self, msgid):
        self.cursor.execute("SELECT id FROM messages WHERE id = ?", (msgid,))
        return self.cursor.fetchone() is not None

    def user_destinataire(self, msgid):
        self.cursor.execute("SELECT username_dest FROM messages WHERE id = ?", (msgid,))
        result = self.cursor.fetchone()
        if result[0] == self.current_user:
            return True
        return False
    def awnser_interface(self, username):
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        print(f"=== Réponse au message de : {username}")
        message = input()
        if message:
            self.cursor.execute("INSERT INTO messages(username_exp, username_dest, message, lu) VALUES(?,?,?,?)", (self.current_user, username, message, 0))
            self.conn.commit()
            self.erreur = "Votre réponse a bien été envoyé."
            self.messagerie_interface()
        else:
            self.erreur = "Votre message ne peux pas être vide."
            self.awnser_interface(username)
    
    def show_message_interface(self, msgid):
        os.system("clear")
        if self.erreur:
            print(self.erreur)
            self.erreur = None

        self.cursor.execute("SELECT * FROM messages WHERE id = ?", (msgid,))
        msginfo = self.cursor.fetchone()
        print(f"=== Message de {msginfo[1]} ===")
        print(f"=== ID : {msginfo[0]} ===")
        print(f"=== Message : {msginfo[3]} ===")
        print("Actions possible : ")
        print("1 : Répondre")
        print("2 : Retour à la messagerie")
        print("3 : Retour au profil")

        choice = input("Votre choix : ")
        if choice == "1":
            self.awnser_interface(msginfo[1])
        elif choice == "2":
            self.messagerie_interface()
        elif choice == "3":
            self.profile_interface()

    def messagerie_interface(self):
        os.system("clear")
        print("=== MESSAGERIE INTERNE (q pour partir) ===")
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        # Recup des messages
        self.cursor.execute("SELECT * FROM messages WHERE username_dest = ? ORDER BY id DESC", (self.current_user,))
        idmessage = []
        result = self.cursor.fetchall()
        for info in result:
            idmessage.append(info[0])
            if info[4] == 0:
                status = "(non lu)"
            else:
                status = "(lu)"
            print(f"Expéditeur : {info[1]}")
            print(f"ID pour ouvrir : {info[0]} {status}")
        choice = input("Votre action : ")
        if choice == "q":
            self.profile_interface()
        else:
            if self.message_exist(choice):
                if self.user_destinataire(choice):
                    self.cursor.execute("UPDATE messages SET lu = ? WHERE id = ?", (1,choice,))
                    self.conn.commit()
                    self.show_message_interface(choice)
                else:
                    self.erreur = "Ce message ne vous est pas adressé :/"
                    self.messagerie_interface()
            else:
                self.erreur = "Ce message n'existe pas."
                self.messagerie_interface()
        
    def reactive_interface(self):
        os.system("clear")
        print("=== ZONE DE REACTIVATION DE COMPTE ===")
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        username = input("Entrez le pseudo de l'utilisateur a réactiver : ")
        if self.user_exists(username):
            if self.user_is_desactive(username):
                self.active_user(username)
            else:
                print("Erreur : Cet utilisateur n'est pas désactiver.")
                print("Souhaitez-vous le désactiver ? (o/n)")
                choice = input("Entre votre choix : ")
                if choice == "o":
                    self.desactive_user(username)
                elif choice == "n":
                    print("Retour au profil...")
                    self.profile_interface()
        else:
            self.erreur = "Erreur : Cet utilisateur n'existe pas."
            self.desactive_interface()
    def desactive_interface(self):
        os.system("clear")
        print("=== ZONE DE DÉSACTIVATION ===")
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        username = input("Entrez le pseudo du compte a désactiver : ")
        if self.user_exists(username):
            if not self.user_is_desactive(username):
                self.desactive_user(username)
            else:
                self.erreur = "Cet utilisateur est déjà désactivé."
        else:
            self.erreur = "Cet utilisateur n'existe pas."
            self.desactive_interface()

    def write_message_interface(self):
        os.system("clear")
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        print("=== ÉCRIRE UN MESSAGE ===")
        username_dest = input("À qui voulez vous envoyer votre message ? >")
        if self.user_exists(username_dest) or not self.user_is_desactive(username_dest):
            print("Écrivez ici votre message : ")
            message = input()
            if message:
                self.cursor.execute("INSERT INTO messages(username_exp, username_dest, message, lu) VALUES(?,?,?,?)", (self.current_user,username_dest,message,0,))
                self.conn.commit()
                self.erreur = f"Message envoyé avec succès à {username_dest}"
                self.profile_interface()
            else:
                self.erreur = "Votre message est vide et c'est impossible."
                self.write_message_interface()
        else:
            self.erreur = "Cet utilisateur n'existe pas ou a été désactivé."
            self.write_message_interface()

    def profile_interface(self):
        os.system("clear")
        """Access to a profile page"""
        print("==== PROFILE DE ", self.current_user, "====")
        ecriture = None
        if self.current_rank == "adm":
            ecriture = "Administrateur"
        else:
            ecriture = "Utilisateur"
        print(f"=== COMPTE {ecriture} ===")
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        print("=== DEBUT DU MENU ===")
        print("Que voulez vous faire ?")
        print("1 : Me déconnecter")
        print("2 : Désactiver un compte")
        print("3 : Réactiver un compte")
        print("4 : Messagerie")
        print("5 : Écrire un message")
        action = input("Écrivez votre choix : ")
        if action == "1":
            self.logout()
        if action == "2" and self.current_rank == "adm":
            self.desactive_interface()
        if action == "3" and self.current_rank == "adm":
            self.reactive_interface()
        if action == "4":
            self.messagerie_interface()
        if action == "5":
            self.write_message_interface()
        self.erreur = "Erreur de l'action"
        self.profile_interface()
    def get_user_rank(self, username):
        self.cursor.execute("SELECT rank FROM users WHERE username = ?", (username,))
        result= self.cursor.fetchone()
        if result:
            return result[0]
    def login_interface(self):
        os.system("clear")
        """Handle the login process."""
        print("==== LOGIN ====")
        username = input("Entrez votre pseudo : ")
        if self.user_exists(username):
            password = getpass.getpass(prompt="Entrez votre mot de passe : ")
            if self.validate_password(username, password):
                if not self.user_is_desactive(username):
                    self.userConnected = True
                    self.current_user = username
                    self.current_rank = self.get_user_rank(username)
                    print(f"Connexion effectuée, bienvenue {self.current_user}.")
                    self.profile_interface()
                else:
                    self.erreur = "Ce profil a été désactivé."
                    self.interface_one()
            else:
                self.erreur = "Mot de passe invalide."
                self.interface_one()
        else:
            self.erreur = "Nous ne trouvons pas votre compte dans la base de donnée merci de vous inscrire."
            self.interface_one()

    def register_user(self, username, password):
        """Register a new user in the database."""
        if not self.user_exists(username):
            self.cursor.execute("INSERT INTO users (username, password, rank, disabled) VALUES (?,?,?,?)", (username, password, 'usr', 0,))
            self.conn.commit()
            self.erreur = f"Utilisateur '{username}' créé avec succès."
            self.interface_one()
        else:
            self.erreur = f"Le pseudo '{username}' a déjà été choisi."
        self.register_interface()

    def register_interface(self):
        os.system("clear")
        """Handle the registration process."""
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        print("==== REGISTER ====")
        username = input("Tapez votre pseudo : ")
        password = getpass.getpass(prompt="Créez un mot de passe : ")
        self.register_user(username, password)

    def interface_one(self):
        os.system("clear")
        """Display the main interface for login or registration."""
        if self.erreur:
            print(self.erreur)
            self.erreur = None
        print("==== CHOOSE AN OPTION ====")
        print("1: Connexion")
        print("2: Inscription")
        choice = input("Votre choix : ")
        if choice == '1':
            self.login_interface()
        elif choice == '2':
            self.register_interface()
        else:
            print("Choix inconnue. Sortie de programme ...")
            exit()

    def close(self):
        """Close the database connection."""
        self.conn.close()


if __name__ == "__main__":
    maj.maj()
    login_system = Login()
    login_system.interface_one()
    login_system.close()