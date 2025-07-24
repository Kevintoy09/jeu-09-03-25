import threading
import time
from datetime import datetime
from config.config import TIME_SCALE  # À ajouter dans config/config.py

class GameLoopManager:
    """
    Centralise les tâches périodiques du jeu (tick ressources, sauvegarde automatique, gestion des constructions, etc.)
    Permet aussi d'enregistrer des callbacks à appeler à chaque tick (ex: progression des transports).
    Prend en compte un facteur d'accélération/ralentissement du temps (TIME_SCALE).
    """
    def __init__(self, game_data, save_load_manager, save_interval=10, tick_interval=1, time_scale=None):
        self.game_data = game_data
        self.save_load_manager = save_load_manager
        self.save_interval = save_interval
        self.tick_interval = tick_interval
        self.time_scale = time_scale if time_scale is not None else TIME_SCALE
        self._stop_flag = False
        self._save_thread = None
        self._tick_thread = None
        self.callbacks = []  # Liste des callbacks à appeler à chaque tick

        # Initialisation du temps accumulé pour un tick régulier
        self.game_data.last_update_time = datetime.utcnow()
        self.game_data.accumulated_dt = 0.0

    def register_callback(self, cb):
        """Ajoute un callback à appeler à chaque tick."""
        self.callbacks.append(cb)

    def start(self):
        """Démarre les threads/timers périodiques"""
        self._stop_flag = False
        self._save_thread = threading.Thread(target=self._periodic_save, daemon=True)
        self._tick_thread = threading.Thread(target=self._periodic_tick, daemon=True)
        self._save_thread.start()
        self._tick_thread.start()

    def stop(self):
        """Arrête proprement les threads"""
        self._stop_flag = True

    def _periodic_save(self):
        while not self._stop_flag:
            try:
                self.save_load_manager.save_game()
            except Exception:
                # On ignore les erreurs de sauvegarde silencieusement (pas de print/log ici)
                pass
            time.sleep(self.save_interval)

    def _periodic_tick(self):
        while not self._stop_flag:
            try:
                now = datetime.utcnow()
                dt = (now - self.game_data.last_update_time).total_seconds() * self.time_scale
                self.game_data.last_update_time = now
                self.game_data.accumulated_dt += dt

                # À chaque tick virtuel (1.0 "seconde" de jeu accélérée), on update tous les systèmes
                while self.game_data.accumulated_dt >= 1.0:
                    self.game_data.resource_manager.update_all(1.0)
                    self.game_data.transport_manager.update_transports(1.0)
                    # Ajout : gestion du tick pour les constructions de bâtiments
                    self._update_all_constructions()
                    self.game_data.accumulated_dt -= 1.0

                # Appelle tous les callbacks enregistrés (ex: progression des transports)
                for cb in self.callbacks:
                    cb()
            except Exception:
                # On ignore les erreurs du tick de manière silencieuse (pas de print/log ici)
                pass
            time.sleep(self.tick_interval)

    def _update_all_constructions(self):
        """
        Scanne toutes les villes et tous les bâtiments "En construction".
        Si un timer est fini, déclenche la complétion du bâtiment (appel à BuildingsManager.complete_task).
        """
        # On récupère le BuildingsManager central
        buildings_manager = getattr(self.game_data, "buildings_manager", None)
        if buildings_manager is None:
            return

        for city in self.game_data.city_manager.get_all_cities():
            for i, building in enumerate(city.get_buildings()):
                if building and getattr(building, "status", None) == "En construction":
                    if buildings_manager.get_remaining_time(building) <= 0:
                        construction_key = (city.coords, city.name, i)
                        buildings_manager.complete_task(
                            construction_key=construction_key,
                            city_data=city,
                            slot_index=i
                        )