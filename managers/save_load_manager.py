import json
import logging

class SaveLoadManager:
    def __init__(self, game_data):
        self.game_data = game_data

    def save_game(self, filepath: str = "savegame.json"):
        try:
            game_data_dict = self.game_data.to_dict()
            with open(filepath, "w") as file:
                json.dump(game_data_dict, file, indent=4)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde : {e}")

    def load_game(self, filepath: str = "savegame.json"):
        try:
            with open(filepath, "r") as file:
                data = json.load(file)
                self.game_data.from_dict(data)
                # --- PRINTS SUPPRIMÉS ICI ---
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        except Exception as e:
            logging.error(f"Erreur lors du chargement du jeu : {e}")