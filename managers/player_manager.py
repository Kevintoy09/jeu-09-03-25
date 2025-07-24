import json
import logging
from models.player import Player

class PlayerManager:
    """
    Gère la liste centralisée des joueurs (création, authentification, sérialisation...).
    Utilise un fichier 'players_table.json' pour persister les comptes.
    Désormais, la gestion des villes d'un joueur se fait via CityManager.get_cities_for_player.
    """
    PLAYERS_FILE = 'players_table.json'

    def __init__(self, game_data):
        self.game_data = game_data
        self.players = {}  # Clé = id_player

    def authenticate_user(self, username, password):
        """
        Authentifie l'utilisateur et définit le joueur courant si succès.
        Retourne l'id du joueur ou None.
        """
        players = self._load_players_file()
        for player in players:
            if player['username'] == username and player['password'] == password:
                player_obj = Player(player['id_player'], player['username'], player['password'])
                self.set_current_player(player_obj)
                logging.info(f"[PlayerManager] Joueur authentifié : {player_obj.id_player}")
                return player_obj.id_player
        logging.warning(f"[PlayerManager] Échec de l'authentification pour {username}.")
        return None

    def set_current_player(self, player):
        """Définit le joueur courant et ajuste la ville active si possible."""
        self.game_data.current_player_id = player.id_player
        self.players[player.id_player] = player
        logging.info(f"[PlayerManager] Joueur actuel défini : {player.id_player}")

        city_manager = self.game_data.city_manager
        player_cities = city_manager.get_cities_for_player(player.id_player)
        if player_cities:
            city = player_cities[0]
            self.game_data.set_active_city({"id": getattr(city, "id", None), "owner": city.owner})
            logging.info(f"[PlayerManager] Ville active définie pour le joueur : {getattr(city, 'id', None)}")

    def get_player(self, player_id):
        """Retourne un joueur par son ID, ou lève une ValueError s'il n'existe pas."""
        if player_id not in self.players:
            raise ValueError(f"[PlayerManager] Joueur '{player_id}' introuvable.")
        return self.players[player_id]

    def player_owns_city(self, player_id, city_id):
        """
        Renvoie True si le joueur possède la ville d'id donné.
        Désormais, cette méthode interroge CityManager.
        """
        city_manager = self.game_data.city_manager
        return any(getattr(city, "id", None) == city_id for city in city_manager.get_cities_for_player(player_id))

    def save_players_table(self):
        """Sauvegarde les joueurs en mémoire dans le fichier."""
        try:
            players_data = [player.to_dict() for player in self.players.values()]
            with open(self.PLAYERS_FILE, "w") as file:
                json.dump({"players": players_data}, file, indent=4)
        except Exception as e:
            logging.error(f"[PlayerManager] Error saving players table: {e}")

    def load_players_table(self):
        """Charge les joueurs du fichier dans la mémoire."""
        for player in self._load_players_file():
            player_obj = Player(player['id_player'], player['username'], player['password'])
            self.players[player_obj.id_player] = player_obj

    def create_account(self, username, password):
        """Crée un nouveau compte utilisateur si le nom est libre."""
        players = self._load_players_file()
        if any(p['username'] == username for p in players):
            logging.warning(f"[PlayerManager] Utilisateur '{username}' existe déjà.")
            return None

        id_player = f"player_{len(players) + 1}"
        new_player = {
            "id_player": id_player,
            "username": username,
            "password": password
        }
        players.append(new_player)
        self._save_players_file(players)
        logging.info(f"[PlayerManager] Création de compte pour '{username}'")

        player_obj = Player(id_player, username, password)
        self.players[id_player] = player_obj
        return id_player

    def get_all_players(self):
        """
        Retourne la liste des joueurs uniques (mémoire + disque, sans doublons).
        """
        mp = {p.id_player: p for p in self.players.values()}
        for p in self._load_players_file():
            if p['id_player'] not in mp:
                mp[p['id_player']] = Player(p['id_player'], p['username'], p['password'])
        return list(mp.values())

    def get_player_by_username(self, username):
        """Retourne un joueur par son nom d'utilisateur ou None."""
        return next((p for p in self.get_all_players() if getattr(p, "username", None) == username), None)

    def to_dict(self):
        """Sérialise tous les joueurs en dict (pour GameData)."""
        return {player.id_player: player.to_dict() for player in self.players.values()}

    def from_dict(self, data, game_data):
        """Reconstruit la liste des joueurs à partir d'un dict sauvegardé (pour GameData)."""
        self.players = {
            player_id: Player.from_dict(player_data, game_data)
            for player_id, player_data in data.items()
        }

    # --- Helpers privés pour accès fichier ---
    def _load_players_file(self):
        """Charge la liste des joueurs depuis le fichier persistant."""
        try:
            with open(self.PLAYERS_FILE, 'r') as file:
                data = json.load(file)
                return data.get('players', [])
        except FileNotFoundError:
            return []
        except Exception as e:
            logging.error(f"[PlayerManager] Impossible de charger {self.PLAYERS_FILE}: {e}")
            return []

    def _save_players_file(self, players):
        """Sauvegarde la liste complète des joueurs dans le fichier."""
        try:
            with open(self.PLAYERS_FILE, 'w') as file:
                json.dump({"players": players}, file, indent=4)
        except Exception as e:
            logging.error(f"[PlayerManager] Impossible de sauvegarder {self.PLAYERS_FILE}: {e}")