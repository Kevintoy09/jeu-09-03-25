from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

from views.header_bar import HeaderBar
from views.world_view import WorldView
from views.island_view import IslandView
from views.city_view import CityView
from views.resource_view import ResourceView
from views.research_view import ResearchView, ResearchTreePopup, ResearchTablePopup
from views.login_screen import LoginScreen
from views.create_account_screen import CreateAccountScreen
from views.island_selection_screen import IslandSelectionScreen
from models.game_data import City
from managers.menu_manager import MenuManager
from managers.resource_manager import update_resource

class ViewManager(FloatLayout):
    """
    Gère les changements de vues principaux et le routage UI côté client.
    Toute logique métier reste dans les managers spécialisés.
    """
    def __init__(
        self, 
        game_data, 
        player_manager, 
        resource_manager, 
        buildings_manager,
        building_popup_manager, 
        game_manager, 
        transport_manager=None, 
        network_manager=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.server_url = "http://127.0.0.1:5000"
        self.network_manager = network_manager
        self.username = None
        self.player_id = None

        self._active_city_id = None
        self.active_island_index = None
        self.game_data = game_data
        self.city_view = None
        self.player_manager = player_manager
        self.resource_manager = resource_manager
        self.buildings_manager = buildings_manager
        self.building_popup_manager = building_popup_manager
        self.game_manager = game_manager
        self.transport_manager = transport_manager

        self.menu_manager = MenuManager(self.switch_view, self.game_data)
        self.city_view = (
            CityView(
                self, 
                game_data,
                buildings_manager,
                update_all_callback=self.refresh_after_action,  # <-- Ajout/Correction ici
                popup_manager=building_popup_manager,
                network_manager=self.network_manager
            )
            if buildings_manager and building_popup_manager else None
        )
        # PATCH: s'assurer que city_view.city_data existe
        if self.city_view and not hasattr(self.city_view, "city_data"):
            self.city_view.city_data = None

        self.resource_view = ResourceView(manager=self, site_type="forest")
        self.header = HeaderBar(
            switch_view_callback=self.switch_view,
            menu_manager=self.menu_manager,
            resource_view=self.resource_view,
            manager=self,
            game_manager=game_manager,
            transport_manager=self.transport_manager,
        )
        self.header.size_hint = (1, None)
        self.header.height = 50
        self.header.pos_hint = {"top": 1}
        self.game_data.set_header_bar(self.header)

        self.view_space = BoxLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.view_space)
        self.add_widget(self.header)

        self.world_view = (
            WorldView(self, game_data)
            if resource_manager and game_manager else None
        )
        self.island_view = IslandView(self, game_data, network_manager=self.network_manager)
        self.base_resource_view = ResourceView(manager=self, site_type="base_resource")
        self.research_view = ResearchView(
            open_research_tree_callback=self.open_research_tree,
            go_back_callback=self.go_back_to_previous_view,
            open_research_table_callback=self.open_research_table,
            game_data=game_data,
            network_manager=self.network_manager
        )
        self.forest_view = ResourceView(manager=self, site_type="forest")

        self.previous_view = None
        self.current_view = None

        self.switch_view("login_screen")
        Window.bind(on_key_down=self.on_key_down)

    # --- GESTION VILLE ACTIVE ---
    def set_active_city(self, city):
        """Définit la ville active (et stocke uniquement son id)."""
        city_id = getattr(city, "id", None)
        if city_id is not None:
            self._active_city_id = city_id
            self.game_data.set_active_city(city)  # garde compatibilité
            # PATCH: toujours synchroniser city_view.city_data
            if self.city_view:
                self.city_view.city_data = city
        else:
            self._active_city_id = None
            if self.city_view:
                self.city_view.city_data = None

    def get_active_city(self):
        """Retourne l'objet Ville actif à partir de son id (toujours à jour)."""
        if self._active_city_id is not None:
            return self.game_data.city_manager.get_city_by_id(self._active_city_id)
        return None

    # --- MULTIJOUEUR / SYNCHRONISATION ---
    def sync_from_server(self, on_done=None):
        try:
            city_before = self.get_active_city()
            data = self.network_manager.get_state() if self.network_manager else None
            if data:
                self.game_data.from_dict(data)
                # Correction : recoller la ville active sur la nouvelle instance
                ac_id = self._active_city_id
                if ac_id:
                    new_city = self.game_data.city_manager.get_city_by_id(ac_id)
                    if new_city:
                        self.set_active_city(new_city)
                active_city = self.get_active_city()
                if self.city_view and active_city:
                    self.city_view.city_data = active_city
                    self.city_view.update_city(active_city)
                self.refresh_all_views()
                self.switch_view("city_view", city_data=active_city)
            if on_done:
                on_done()
        except Exception:
            if on_done:
                on_done()
            pass  # Optionally, add a print or pass silently

    def refresh_all_views(self):
        active_city = self.get_active_city()
        if self.current_view in ["city_view", "view_city"] and active_city:
            self.city_view.city_data = active_city # PATCH sync
            self.city_view.update_city(active_city)
        elif self.current_view == "world_view" and self.world_view:
            self.world_view.refresh_island_markers()
        elif self.current_view == "header" and self.header:
            self.header.update_resources(
                active_city.resources if active_city else {}, active_city
            )

    def refresh_ui(self):
        """Rafraîchit uniquement l'UI locale sans aucune synchronisation serveur."""
        self.refresh_all_views()

    def refresh_after_action(self):
        """Callback centralisé à utiliser après une action de jeu majeure (construction, upgrade, etc.)."""
        self.sync_from_server()

    def select_city_on_server(self, city):
        if not self.username or not city or not getattr(city, "id", None):
            return False
        try:
            ok = self.network_manager.select_city(self.username, city.id) if self.network_manager else False
            return ok
        except Exception:
            return False

    def create_view(self, view_name):
        if view_name == "login_screen":
            return LoginScreen(
                switch_view_callback=self.switch_view,
                game_data=self.game_data,
                header=self.header
            )
        if view_name == "create_account_screen":
            return CreateAccountScreen(switch_view_callback=self.switch_view, game_data=self.game_data)
        if view_name == "island_selection_screen":
            return IslandSelectionScreen(switch_view_callback=self.switch_view, game_data=self.game_data)
        if view_name == "world_view" and self.world_view:
            return self.world_view
        if view_name == "island_view":
            return self.island_view
        if view_name in ["city_view", "view_city"] and self.city_view:
            return self.city_view
        if view_name == "forest_view":
            return self.forest_view
        if view_name == "base_resource_view":
            return self.base_resource_view
        if view_name == "research_view":
            return self.research_view
        if view_name == "resource_view":
            return self.resource_view
        return BoxLayout()

    def switch_view(self, view_name, **kwargs):
        self.previous_view = getattr(self, "current_view", None)
        self.current_view = view_name

        # --- PATCH pour la ressource : toujours mettre à jour la ville et le site ---
        if view_name == "resource_view":
            from views.resource_view import SITE_TO_RESOURCE
            site_type = kwargs.get("site_type", None)
            city_data = kwargs.get("city_data", None)
            island_coords = kwargs.get("island_coords", None)
            if site_type is not None:
                self.resource_view.site_type = site_type
                self.resource_view.resource_key = SITE_TO_RESOURCE.get(site_type, site_type)
            if city_data is not None:
                self.resource_view.set_city_data(city_data)
            if island_coords is not None:
                self.resource_view.island_coords = island_coords

        self.view_space.clear_widgets()
        view = self.create_view(view_name)
        self.view_space.add_widget(view)

        if view_name in ["login_screen", "create_account_screen"]:
            if self.header.parent:
                self.remove_widget(self.header)
        else:
            if not self.header.parent:
                self.add_widget(self.header)

        if view_name == "world_view" and hasattr(self.world_view, "refresh_island_markers"):
            self.world_view.refresh_island_markers()

        data = kwargs.get("data", None)
        site_type = kwargs.get("site_type", None)
        city_data = kwargs.get("city_data", None)

        if view_name == "island_view" and isinstance(data, int):
            self.active_island_index = data
            self.island_view.update_island(self.active_island_index)
        elif view_name == "island_view" and data is not None:
            self.island_view.update_island(data)
        elif view_name == "city_view" and self.city_view:
            param = city_data if city_data is not None else data
            self._handle_city_view(param)
        elif view_name == "select_city":
            self._handle_select_city(data)
        elif view_name == "view_city" and self.city_view:
            self._handle_view_city(city_data if city_data is not None else data)
        elif view_name in ["forest_view", "base_resource_view"]:
            self._handle_resource_views(view)
        elif view_name == "resource_view":
            if site_type is not None and city_data is not None:
                city_id = getattr(city_data, "id", None)
                if city_id is not None:
                    real_city = self.game_data.city_manager.get_city_by_id(city_id)
                else:
                    real_city = city_data if isinstance(city_data, City) else None
                self.resource_view = ResourceView(
                    manager=self,
                    site_type=site_type,
                    city_data=city_data,
                    island_coords=island_coords
                )
                self.resource_view.set_city_data(real_city)
                self.view_space.clear_widgets()
                self.view_space.add_widget(self.resource_view)
        if view_name == "world_view" and self.world_view:
            if data and isinstance(data, dict) and "center_coords" in data:
                self.world_view.update_world(data)

    def _handle_city_view(self, data=None):
        if not self.city_view:
            return
        city = None
        if data is not None:
            if isinstance(data, City):
                city = self.game_data.city_manager.get_city_by_id(data.id)
            elif isinstance(data, dict):
                city_id = data.get("id")
                city = self.game_data.city_manager.get_city_by_id(city_id)
            else:
                city = self.get_active_city()
            if city:
                self.set_active_city(city)
        else:
            city = self.get_active_city()
            if city:
                self.set_active_city(city)
        if city:
            # Calcul de la population libre uniquement pour l'affichage, sans modifier city.resources
            total_population = city.get_resources().get("population_total", 0)
            workers_used = sum(
                city.get_resources().get(f"{res}_workers", 0)
                for res in ["wood", "stone", "cereal", "papyrus", "iron"]
            )
            population_free = max(0, total_population - workers_used)
            # On passe une copie des ressources avec population_free calculée uniquement pour l'affichage
            resources_for_display = dict(city.get_resources())
            resources_for_display["population_free"] = population_free
            self.header.update_resources(resources_for_display, city)
            self.city_view.city_data = city  # PATCH sync
            self.city_view.update_city(city)

    def _handle_view_city(self, data):
        if not self.city_view:
            return
        city = None
        if isinstance(data, dict):
            city_id = data.get("id")
            city = self.game_data.city_manager.get_city_by_id(city_id)
        elif isinstance(data, City):
            city = self.game_data.city_manager.get_city_by_id(data.id)
        if city:
            self.set_active_city(city)
            self.city_view.city_data = city  # PATCH sync
            self.city_view.view_city(city)
            
    def _handle_select_city(self, data):
        if isinstance(data, str):
            if self.game_data.current_player_id is not None:
                self.switch_view("island_view", data=self.active_island_index)

    def _handle_resource_views(self, view):
        city = self.get_active_city()
        if city:
            view.set_city_data(city)
            for resource in self.resource_manager.resources.values():
                update_resource(resource, city, 1)

    def open_research_table(self):
        ResearchTablePopup().open()

    def go_back_to_previous_view(self):
        if self.previous_view:
            self.switch_view(self.previous_view)

    def open_research_tree(self, category):
        ResearchTreePopup(category, self.game_data).open()

    def update_header_resources(self):
        city = self.get_active_city()
        if city:
            self.header.update_resources(
                city.resources,
                city
            )

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if 'ctrl' in modifier and key == ord('s'):
            if hasattr(self.parent, 'save_game_data'):
                self.parent.save_game_data()