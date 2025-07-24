from .base_popup import BasePopup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock

def make_adaptive_label(text, min_height=22, **kwargs):
    if 'halign' not in kwargs:
        kwargs['halign'] = 'left'
    if 'valign' not in kwargs:
        kwargs['valign'] = 'middle'
    lbl = Label(
        text=text,
        markup=True,
        size_hint_y=None,
        **kwargs
    )
    lbl.bind(
        width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
        texture_size=lambda instance, value: setattr(instance, 'height', max(value[1], min_height)),
    )
    return lbl

class AcademyPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_id=None,
        resource_manager=None,
        network_manager=None,
        **kwargs
    ):
        # Nettoyage kwargs pour ne rien passer de métier à Kivy
        for key in [
            "city_id", "manager", "resource_manager", "network_manager", "custom_content_callback"
        ]:
            kwargs.pop(key, None)

        self.city_id = city_id
        self.resource_manager = resource_manager
        self.building_data = building_data
        self.buildings_manager = buildings_manager
        self.update_all_callback = update_all_callback
        self.network_manager = network_manager

        actual_custom_content_callback = custom_content_callback if custom_content_callback is not None else self.add_dynamic_info

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=actual_custom_content_callback,
            network_manager=network_manager,
            city_id=city_id,
            **kwargs
        )

        self.generate_research_points()

    def get_city(self):
        city = None
        if self.resource_manager and hasattr(self.resource_manager, "game_data"):
            game_data = self.resource_manager.game_data
            if hasattr(game_data, "city_manager"):
                city = game_data.city_manager.get_city_by_id(self.city_id)
        return city

    def get_effect_data(self):
        effect_data = self.building_data.get("effect", {})
        if not effect_data or not effect_data.get("max_workers"):
            level = int(self.building_data.get("level", 1))
            try:
                from data.buildings_database import buildings_database
                name = self.building_data.get("name") or "Académie"
                levels = buildings_database.get(name, {}).get("levels", [])
                if 0 < level <= len(levels):
                    effect_data = levels[level-1].get("effect", {})
            except Exception:
                pass
        return effect_data

    def add_dynamic_info(self, layout):
        self.dynamic_info_layout = layout  # Pour pouvoir rafraîchir plus tard

        city = self.get_city()
        if not city:
            layout.add_widget(make_adaptive_label("[b]Erreur : ville non initialisée[/b]", markup=True, min_height=30))
            return

        effect_data = self.get_effect_data()

        player = None
        if self.resource_manager and hasattr(self.resource_manager, "game_data") and self.resource_manager.game_data:
            player_manager = getattr(self.resource_manager.game_data, "player_manager", None)
            if player_manager:
                player = player_manager.get_player(getattr(city, "owner", None))

        max_workers = int(effect_data.get("max_workers", 0))
        research_points_per_worker = float(effect_data.get("research_points_per_worker", 0))
        current_workers = int(getattr(city, "workers_assigned", {}).get("academy", 0))
        free_population = int(getattr(getattr(city, "resources", {}), "get", lambda k, d=0: 0)("population_free", 0))
        research_points = int(getattr(player, "research_points", 0) if player else 0)

        total_productivity = current_workers * research_points_per_worker

        layout.add_widget(make_adaptive_label(f"Points de recherche : {research_points}", min_height=30))
        layout.add_widget(make_adaptive_label(f"Population libre : {free_population}", min_height=30))
        layout.add_widget(make_adaptive_label(f"Ouvriers affectés : {current_workers} / {max_workers}", min_height=30))
        layout.add_widget(make_adaptive_label(f"Productivité : {research_points_per_worker} points/ouvrier/5s", min_height=30))
        layout.add_widget(make_adaptive_label(f"Productivité totale : {total_productivity} points/5s", min_height=30))

        worker_control_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        worker_input = TextInput(text=str(current_workers), multiline=False, size_hint_x=0.5, input_filter="int")
        confirm_button = Button(text="Confirmer", size_hint_x=0.5)
        confirm_button.bind(on_press=lambda instance: self.confirm_worker_allocation(worker_input, player))
        worker_control_layout.add_widget(worker_input)
        worker_control_layout.add_widget(confirm_button)
        layout.add_widget(worker_control_layout)

    def refresh_dynamic_info(self):
        if hasattr(self, "dynamic_info_layout"):
            layout = self.dynamic_info_layout
            layout.clear_widgets()
            self.add_dynamic_info(layout)

    def confirm_worker_allocation(self, worker_input, player):
        try:
            new_worker_count = int(worker_input.text)
            city = self.get_city()
            if not city:
                return
            effect_data = self.get_effect_data()
            max_workers = int(effect_data.get("max_workers", 0))
            current_workers = int(getattr(city, "workers_assigned", {}).get("academy", 0))
            free_population = int(getattr(getattr(city, "resources", {}), "get", lambda k, d=0: 0)("population_free", 0))
            if new_worker_count < 0 or new_worker_count > max_workers or (new_worker_count - current_workers > free_population):
                return

            if hasattr(city, "workers_assigned") and isinstance(city.workers_assigned, dict):
                city.workers_assigned["academy"] = new_worker_count
            elif hasattr(city, "workers_assigned"):
                setattr(city.workers_assigned, "academy", new_worker_count)
            else:
                city.workers_assigned = {"academy": new_worker_count}

            if self.network_manager and player:
                self.network_manager.assign_workers(
                    getattr(city, "id", None),
                    "academy",
                    new_worker_count,
                    player_id=getattr(player, "id_player", None)
                )

            if self.update_all_callback:
                self.update_all_callback()
            # Rafraîchir dynamiquement le contenu du popup sans le fermer/réouvrir
            self.refresh_dynamic_info()
        except ValueError:
            pass

    def generate_research_points(self):
        def add_points(dt):
            city = self.get_city()
            if not city:
                return
            workers = int(getattr(city, "workers_assigned", {}).get("academy", 0))
            if workers > 0:
                effect_data = self.get_effect_data()
                points_to_add = workers * float(effect_data.get("research_points_per_worker", 0))
                player = None
                if self.resource_manager and hasattr(self.resource_manager, "game_data") and self.resource_manager.game_data:
                    player_manager = getattr(self.resource_manager.game_data, "player_manager", None)
                    if player_manager:
                        player = player_manager.get_player(getattr(city, "owner", None))
                if player:
                    player.research_points += points_to_add
                self.refresh_dynamic_info()
        if not self.building_data.get("is_generating", False):
            Clock.schedule_interval(add_points, 5)
            self.building_data["is_generating"] = True