import os
import logging

# --- Désactiver les logs HTTP de requests et urllib3 ---
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# --- Réduire les logs Kivy à warning pour éviter le flood ---
os.environ["KIVY_LOG_LEVEL"] = "warning"

# Import de la configuration mobile
from config.mobile_config import (
    IS_MOBILE, IS_ANDROID, WINDOW_WIDTH, WINDOW_HEIGHT,
    request_android_permissions, configure_touch_settings, get_server_url
)

from kivy.config import Config
Config.set('graphics', 'width', str(WINDOW_WIDTH))
Config.set('graphics', 'height', str(WINDOW_HEIGHT))
Config.set('graphics', 'resizable', False)
Config.write()

from kivy.core.window import Window
Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
Window.minimum_width = WINDOW_WIDTH
Window.minimum_height = WINDOW_HEIGHT

# Configuration spécifique mobile
if IS_MOBILE:
    configure_touch_settings()
    request_android_permissions()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from models.game_data import GameData
from managers.buildings_manager import BuildingsManager
from managers.ai_manager import AIManager
from managers.building_popup_manager import BuildingPopupManager
from managers.menu_manager import MenuManager
from managers.resource_manager import ResourceManager
from managers.game_manager import GameManager
from managers.player_manager import PlayerManager
from managers.population_manager import PopulationManager
from config.config import TIME_SCALE, GameUpdateManager
from database.sauvegarde import Database
from views.view_manager import ViewManager
from network.network_manager import NetworkManager
from managers.transport_manager import TransportManager

SERVER_URL = get_server_url()  # URL adaptée à la plateforme

class MainWidget(BoxLayout):
    """
    Widget principal de l'application.
    Initialise et connecte tous les managers, charge GameData, et gère la synchronisation UI/serveur.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.username = None
        self.player_id = None
        self.server_url = SERVER_URL
        self.network_manager = NetworkManager(self.server_url)

        # GameData local pour l'UI, synchronisé par HTTP
        self.game_data = GameData()
        # Passe la MEME instance partout !
        self.player_manager = PlayerManager(self.game_data)
        self.game_data.player_manager = self.player_manager

        self.resource_manager = ResourceManager(self.game_data)
        self.game_data.resource_manager = self.resource_manager

        self.buildings_manager = BuildingsManager(
            self.game_data,
            None
        )
        self.population_manager = PopulationManager(self.game_data)

        # TransportManager branché au network_manager
        self.transport_manager = TransportManager(self.game_data)
        self.game_data.transport_manager = self.transport_manager

        self.building_popup_manager = BuildingPopupManager(
            None, 
            self.buildings_manager, 
            self.resource_manager, 
            self.population_manager,
            network_manager=self.network_manager,
            transport_manager=self.transport_manager
        )
        self.game_manager = GameManager(self.resource_manager, self.buildings_manager)

        # VIEW_MANAGER doit recevoir la MEME instance de game_data !
        self.view_manager = ViewManager(
            game_data=self.game_data,
            player_manager=self.player_manager,
            resource_manager=self.resource_manager,
            buildings_manager=self.buildings_manager,
            building_popup_manager=self.building_popup_manager,
            game_manager=self.game_manager,
            transport_manager=self.transport_manager,
            network_manager=self.network_manager,
        )
        self.add_widget(self.view_manager)

        # Relie city_view et building_popup_manager
        if self.view_manager.city_view:
            self.view_manager.city_view.popup_manager = self.building_popup_manager
            if hasattr(self.view_manager.city_view, "update_all_callback"):
                self.view_manager.city_view.update_all_callback = self.refresh_after_action
        self.buildings_manager.city_view = self.view_manager.city_view

        if hasattr(self.building_popup_manager, "update_all_callback"):
            self.building_popup_manager.update_all_callback = self.refresh_after_action

        self.network_manager.set_game_data(self.game_data)

    def sync_userview(self):
        """Synchronise l'identité utilisateur avec la vue."""
        self.view_manager.username = self.username
        self.view_manager.player_id = self.player_id
        self.game_data.current_player_id = self.player_id

    def sync_from_server(self):
        """Synchronise GameData et les vues depuis le serveur central."""
        try:
            data = self.network_manager.get_state()
            if data:
                self.game_data.from_dict(data)
                self.sync_userview()
                self.view_manager.sync_from_server()
                self.view_manager.refresh_all_views()
            else:
                logging.error(f"[MainWidget] sync_from_server: Pas de données reçues du serveur.")
        except Exception as e:
            logging.error(f"[MainWidget] Exception during sync_from_server: {e}")

    def after_city_selected(self, player_id=None, city_id=None):
        """À appeler après sélection de ville ou de joueur côté UI/serveur."""
        if player_id:
            self.player_id = player_id
        if city_id:
            try:
                resp = self.network_manager.select_city(self.username, city_id)
                if resp and resp.get("city"):
                    city = resp["city"]
                    owner = city.get("owner")
                    if owner:
                        self.player_id = owner
                    self.sync_userview()
                    self.buildings_manager.set_network_config(self.network_manager, self.username)
                    self.sync_from_server()
                else:
                    logging.error(f"[MainWidget] after_city_selected: Réponse invalide ou vide du serveur.")
            except Exception as e:
                logging.error(f"[MainWidget] Exception during after_city_selected: {e}")
        else:
            self.sync_userview()
            self.buildings_manager.set_network_config(self.network_manager, self.username)
            self.sync_from_server()

    def refresh_after_action(self):
        """
        Callback centralisé : toute action majeure (construction, upgrade, etc.) appelle ce refresh.
        Rafraîchit l'état complet local depuis le serveur, ce qui met à jour les timers affichés.
        """
        self.sync_from_server()

class GameApp(App):
    def build(self):
        return MainWidget()

if __name__ == "__main__":
    import sys
    import traceback
    def excepthook(type, value, tb):
        traceback.print_exception(type, value, tb)
    sys.excepthook = excepthook

    GameApp().run()
    # Suppression du input final : inutile en prod, garde la main à la fenêtre Kivy