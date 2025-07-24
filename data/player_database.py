import sqlite3

def create_connection(db_path):
    """ Crée une connexion à la base de données SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print("Connexion établie avec SQLite")
    except sqlite3.Error as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
    return conn

def create_table(db_path):
    """ Crée la table des utilisateurs si elle n'existe pas déjà """
    conn = create_connection(db_path)
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                );
            """)
            conn.commit()
            print("Table des utilisateurs créée avec succès")
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table : {e}")
        finally:
            conn.close()

def create_player_table(db_path):
    """ Crée la table des joueurs si elle n'existe pas déjà """
    conn = create_connection(db_path)
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    player_id TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """)
            conn.commit()
            print("Table des joueurs créée avec succès")
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table des joueurs : {e}")
        finally:
            conn.close()

def add_user(db_path, username, password):
    """ Ajoute un nouvel utilisateur et crée un joueur associé """
    conn = create_connection(db_path)
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            user_id = cursor.lastrowid

            # Créer le joueur associé
            player_id = get_next_player_id(db_path)
            if player_id:
                cursor.execute("INSERT INTO players (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
                conn.commit()
                print("Utilisateur et joueur ajoutés avec succès")
            else:
                print("Erreur lors de la génération de l'identifiant du joueur")
        except sqlite3.IntegrityError:
            print("Erreur : Le nom d'utilisateur existe déjà")
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout de l'utilisateur : {e}")
        finally:
            conn.close()

def authenticate_user(db_path, username, password):
    """ Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe """
    conn = create_connection(db_path)
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                return user[0]  # Retourner l'identifiant de l'utilisateur
            return None
        except sqlite3.Error as e:
            print(f"Erreur lors de l'authentification de l'utilisateur : {e}")
            return None
        finally:
            conn.close()

# Crée les tables au démarrage
db_path = 'game_users.db'
create_table(db_path)
create_player_table(db_path)