import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.c = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.c = self.conn.cursor()
            self.create_tables()
            print("Connexion établie avec la base de données.")
        except sqlite3.Error as e:
            print(f"Erreur lors de la connexion à la base de données: {e}")

    def create_tables(self):
        try:
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                );
            ''')
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    player_id TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            ''')
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS sauvegarde (
                    joueur_id TEXT PRIMARY KEY,
                    score INTEGER,
                    position_x INTEGER,
                    position_y INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(joueur_id) REFERENCES players(player_id)
                );
            ''')
            self.conn.commit()
            print("Tables 'users', 'players' et 'sauvegarde' créées ou déjà existantes.")
        except sqlite3.Error as e:
            print(f"Erreur lors de la création des tables: {e}")

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                print("Connexion fermée.")
            except sqlite3.Error as e:
                print(f"Erreur lors de la fermeture de la connexion: {e}")

    def sauvegarder_jeu(self, joueur_id, score, position_x, position_y):
        try:
            self.c.execute('''
                INSERT OR REPLACE INTO sauvegarde (joueur_id, score, position_x, position_y, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (joueur_id, score, position_x, position_y, datetime.now()))
            self.conn.commit()
            print(f"Données de jeu sauvegardées pour le joueur {joueur_id}.")
        except sqlite3.Error as e:
            print(f"Erreur lors de la sauvegarde des données de jeu : {e}")

    def charger_jeu(self, joueur_id):
        try:
            self.c.execute('SELECT * FROM sauvegarde WHERE joueur_id = ?', (joueur_id,))
            data = self.c.fetchone()
            if data:
                print(f"Données de jeu chargées pour le joueur {joueur_id}.")
            else:
                print(f"Aucune donnée de sauvegarde trouvée pour le joueur {joueur_id}.")
            return data
        except sqlite3.Error as e:
            print(f"Erreur lors du chargement des données de jeu : {e}")
            return None

    def add_user(self, username, password):
        """ Ajoute un nouvel utilisateur et crée un joueur associé """
        try:
            self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            user_id = self.c.lastrowid

            # Créer le joueur associé
            player_id = f'player_{user_id}'
            self.c.execute("INSERT INTO players (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
            self.conn.commit()
            print("Utilisateur et joueur ajoutés avec succès")
        except sqlite3.IntegrityError:
            print("Erreur : Le nom d'utilisateur existe déjà")
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout de l'utilisateur : {e}")

    def authenticate_user(self, username, password):
        """ Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe """
        try:
            self.c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
            user = self.c.fetchone()
            if user:
                print(f"Utilisateur authentifié avec succès: {username}")
                return user[0]  # Retourner l'identifiant du joueur
            print(f"Échec de l'authentification pour l'utilisateur: {username}")
            return None
        except sqlite3.Error as e:
            print(f"Erreur lors de l'authentification de l'utilisateur : {e}")
            return None

def create_connection(db_path):
    """ Crée une connexion à la base de données SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print("Connexion établie avec SQLite")
    except sqlite3.Error as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
    return conn