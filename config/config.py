# Configuration globale pour le jeu

# Échelle de temps
TIME_SCALE = 1.0  # 1.0 = temps normal, >1.0 = accéléré, <1.0 = ralenti

from kivy.clock import Clock

class GameUpdateManager:
    def __init__(self, resource_manager, game_manager, ai_manager=None):
        self.resource_manager = resource_manager
        self.game_manager = game_manager
        self.ai_manager = ai_manager
        self.time_scale = TIME_SCALE  # Utiliser TIME_SCALE comme valeur par défaut

    def update_game_state(self, dt):
        # Mettre à jour les ressources
        self.resource_manager.update_all(dt)

        # Mettre à jour les villes
        self.game_manager.update_all_cities(dt)

        # Simuler les actions de l'IA si l'IA est activée
        if self.ai_manager:
            self.ai_manager.simulate_ai_actions(dt)

    def start_update_schedule(self):
        Clock.schedule_interval(self.update_game_state, 1 / self.time_scale)  # Appeler toutes les secondes

    def set_time_scale(self, time_scale):
        self.time_scale = time_scale
        Clock.unschedule(self.update_game_state)
        Clock.schedule_interval(self.update_game_state, 1 / self.time_scale)