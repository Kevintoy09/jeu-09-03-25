# Activer ou désactiver les actions de l'IA
AI_ENABLED = False

from kivy.clock import Clock
import random


class AIManager:
    def __init__(self, game_data, update_header_callback):
        """
        Initialisation du gestionnaire IA.
        - game_data : données du jeu.
        - update_header_callback : fonction pour mettre à jour l'affichage des ressources dans le HeaderBar.
        """
        self.game_data = game_data
        self.update_header_callback = update_header_callback
        Clock.schedule_interval(self.simulate_ai_actions, 10)  # Actions toutes les 10 secondes

    def simulate_ai_actions(self, dt):
        """Simule les actions des villes IA."""
        if not AI_ENABLED:
            return  # Si l'IA est désactivée, ignorer les actions

        for island in self.game_data.islands:
            for city in island["cities"]:
                if city["type"] == "ai":  # Agir uniquement sur les villes IA
                    self.perform_ai_actions(city)

    def perform_ai_actions(self, city):
        """Prend des décisions simples pour une ville IA."""
        print(f"[INFO] Actions pour la ville IA {city['name']}")

        # Collecter des ressources
        self.collect_resources(city)

        # Construire ou améliorer des bâtiments
        if self.should_build_or_upgrade(city):
            self.build_or_upgrade(city)

        # Produire des soldats si nécessaire
        if self.should_train_army(city):
            self.train_army(city)

    def collect_resources(self, city):
        """Collecte automatique de ressources."""
        city["resources"]["wood"] += 20
        city["resources"]["stone"] += 10
        city["resources"]["gold"] += 5
        city["resources"]["population_free"] += 1  # Croissance de la population
        print(f"[INFO] Ville IA {city['name']} a collecté des ressources.")
        self.update_header_callback()  # Mettre à jour l'affichage si nécessaire

    def should_build_or_upgrade(self, city):
        """Définit si une construction ou une amélioration est nécessaire."""
        return any(slot is None for slot in city["buildings"]) or random.random() < 0.3

    def build_or_upgrade(self, city):
        """Construit ou améliore un bâtiment."""
        for i, slot in enumerate(city["buildings"]):
            if slot is None:  # Construire un nouveau bâtiment
                city["buildings"][i] = {"name": "Entrepôt", "level": 1}
                print(f"[INFO] Ville IA {city['name']} a construit un Entrepôt dans le slot {i + 1}.")
                return
            elif slot["level"] < 3:  # Améliorer un bâtiment existant
                slot["level"] += 1
                print(f"[INFO] Ville IA {city['name']} a amélioré {slot['name']} au niveau {slot['level']}.")
                return

    def should_train_army(self, city):
        """Vérifie si l'entraînement d'une armée est nécessaire."""
        return "barracks" in [b["name"] for b in city["buildings"] if b] and random.random() < 0.3

    def train_army(self, city):
        """Entraîne des soldats pour la défense ou l'attaque."""
        if "army" not in city:
            city["army"] = {"soldiers": 0, "archers": 0, "cavalry": 0}
        city["army"]["soldiers"] += random.randint(5, 15)
        print(f"[INFO] Ville IA {city['name']} a entraîné des soldats.")
