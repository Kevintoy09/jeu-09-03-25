import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from config.style import STYLES, apply_button_style

from data.buildings_database import buildings_database
from models.city import City
from popups.transport_list_popup import TransportsListPopup
from widgets.menu_button import MenuButton

# === POPUPS SPÉCIAUX ===

class ResourcePopup(Popup):
    def __init__(self, resource_name, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Informations : {resource_name.capitalize()}"
        self.size_hint = (0.7, 0.6)
        self.resource_name = resource_name
        self.update_callback = update_callback

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.quantity_label = Label(text="Quantité actuelle : 0")
        self.capacity_label = Label(text="Capacité maximale : 0")
        self.productivity_label = Label(text="Productivité : 0 / sec")

        layout.add_widget(self.quantity_label)
        layout.add_widget(self.capacity_label)
        layout.add_widget(self.productivity_label)
        self.add_widget(layout)

        # Met à jour les données toutes les secondes
        self._event = Clock.schedule_interval(self.update_data, 1)
        self.update_data(0)

    def update_data(self, dt):
        data = self.update_callback(self.resource_name)
        self.quantity_label.text = f"Quantité actuelle : {int(data.get('current_quantity', 0))}"
        self.capacity_label.text = f"Capacité maximale : {int(data.get('max_quantity', 0))}"
        base_productivity = data.get('base_productivity', 0)
        building_bonus = data.get('building_bonus', 0)
        research_bonus = data.get('research_bonus', 0)
        special_bonus = data.get('special_bonus', 0)
        total_productivity = data.get('total_productivity', 0)
        self.productivity_label.text = (
            f"Productivité de base : {int(base_productivity)} / sec\n"
            f"+ Bonus bâtiment : {int(building_bonus)}%\n"
            f"+ Bonus recherche : {int(research_bonus)}%\n"
            f"+ Bonus spécial : {int(special_bonus)}%\n"
            f"= Total productivité : {int(total_productivity)} / sec"
        )

    def on_dismiss(self):
        Clock.unschedule(self._event)

class GoldPopup(Popup):
    def __init__(self, city_data, manager, **kwargs):
        super().__init__(title="Informations : Or", size_hint=(0.6, 0.5), **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        if not city_data:
            layout.add_widget(Label(text="[b]Aucune ville sélectionnée[/b]", markup=True))
        else:
            resources = city_data.get_resources()
            pop_libre = resources.get('population_free', 0)
            gold_per_pop = getattr(city_data, "gold_rate", 1)
            gold_prod = pop_libre * gold_per_pop
            layout.add_widget(Label(text=f"Population libre : {pop_libre:.2f}"))
            layout.add_widget(Label(text=f"Or par habitant libre : {gold_per_pop}"))
            layout.add_widget(Label(text=f"Production totale (tick) : {gold_prod:.2f}"))
        self.add_widget(layout)

class PopulationPopup(Popup):
    def __init__(self, city_data, manager, **kwargs):
        super().__init__(title="Informations : Population", size_hint=(0.6, 0.5), **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        if not city_data:
            layout.add_widget(Label(text="[b]Aucune ville sélectionnée[/b]", markup=True))
        else:
            resources = city_data.get_resources()
            pop_totale = int(resources.get("population_total", 0))
            pop_libre = int(resources.get("population_free", pop_totale))
            pop_max = int(manager.resource_manager.get_population_data(city_data).get("max", pop_totale))
            croissance = resources.get("population_growth", 0.0)
            cereal_consumption = resources.get("cereal_needed", 0.0)
            layout.add_widget(Label(text=f"Croissance : {croissance:.2f} / tick"))
            layout.add_widget(Label(text=f"Population actuelle : {pop_totale} (libre : {pop_libre})"))
            layout.add_widget(Label(text=f"Capacité maximale : {pop_max}"))
            layout.add_widget(Label(text=f"Consommation de céréales : {cereal_consumption:.2f} / tick"))
        self.add_widget(layout)

class ResearchPopup(Popup):
    def __init__(self, city_data, manager, **kwargs):
        super().__init__(title="Informations : Recherche", size_hint=(0.6, 0.3), **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        if not city_data:
            layout.add_widget(Label(text="[b]Aucune ville sélectionnée[/b]", markup=True))
        else:
            resources = city_data.get_resources()
            workers = city_data.get_workers_assigned('academy') if hasattr(city_data, 'get_workers_assigned') else 0
            base_rate = 1
            research_per_tick = workers * base_rate
            layout.add_widget(Label(text=f"Chercheurs assignés : {workers}"))
            layout.add_widget(Label(text=f"Points de recherche par tick : {research_per_tick}"))
        self.add_widget(layout)

# === HEADER BAR ===
class HeaderBar(BoxLayout):
    """
    Barre d'entête affichant les ressources, la sélection de ville et les accès principaux.
    Synchronise l'état local avec le serveur régulièrement.
    """
    def __init__(self, switch_view_callback, menu_manager, resource_view, manager, game_manager, transport_manager=None, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(*STYLES["header_bar"]["background_color"])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg_rect, size=self._update_bg_rect)

        self.size_hint = (1, None)
        self.size_hint_y = None
        self.height = 120
        self.minimum_height = 120
        Clock.schedule_once(lambda dt: setattr(self, "height", 120), 0)

        self.pos_hint = {"top": 1}
        self.manager = manager
        self.game_manager = game_manager
        self.resource_view = resource_view
        self.transport_manager = transport_manager
        # self.city_data = None  # REMOVE: always use getter
        self._init_spinner = True

        # Ligne 1 : boutons principaux et spinner
        self.line1 = BoxLayout(orientation="horizontal", size_hint_y=0.33, spacing=10)

        # Initialisation du joueur courant
        player = manager.game_data.get_current_player()
        joueur_id = player.id_player if player else None

        self.menu_button = MenuButton(
            joueur_id=joueur_id,
            notification_manager=manager.game_data.notification_manager,
            text="MENU", size_hint=(0.2, 1)
        )
        apply_button_style(self.menu_button)
        self.menu_button.bind(on_press=lambda instance: menu_manager.open_menu())
        self.line1.add_widget(self.menu_button)
        self.menu_button.update_badge()

        self.switch_view_callback = switch_view_callback

        self.city_spinner = Spinner(
            text="Sélectionnez ville",
            values=[],
            size_hint=(0.3, 1)
        )
        apply_button_style(self.city_spinner)
        self.city_spinner.bind(text=self.on_spinner_select)
        self.line1.add_widget(self.city_spinner)

        self.world_button = Button(text="Monde", size_hint=(0.15, 1))
        apply_button_style(self.world_button)
        self.world_button.bind(on_press=lambda instance: self._switch_and_update("world_view", switch_view_callback))
        self.line1.add_widget(self.world_button)

        self.island_button = Button(text="Île", size_hint=(0.15, 1))
        apply_button_style(self.island_button)
        self.island_button.bind(on_press=lambda instance: self._switch_and_update("island_view", switch_view_callback))
        self.line1.add_widget(self.island_button)

        self.city_button = Button(text="Ville", size_hint=(0.15, 1))
        apply_button_style(self.city_button)
        self.city_button.bind(on_press=lambda instance: self._switch_and_update("city_view", switch_view_callback))
        self.line1.add_widget(self.city_button)

        self.reduce_button = Button(text="Réduire", size_hint=(0.15, 1))
        apply_button_style(self.reduce_button)
        self.reduce_button.bind(on_press=self.toggle_header_visibility)
        self.line1.add_widget(self.reduce_button)

        self.add_widget(self.line1)

        # Ligne 2 : ressources globales
        self.line2 = BoxLayout(orientation="horizontal", size_hint_y=0.33)
        self.gold_label = Label(text="Or: 0", size_hint=(0.15, 1))
        self.gold_label.bind(on_touch_down=self.open_gold_popup)
        self.line2.add_widget(self.gold_label)

        self.ships_label = Label(text="Bateaux: 0/0", size_hint=(0.15, 1))
        self.ships_label.bind(on_touch_down=self.open_transports_popup)
        self.line2.add_widget(self.ships_label)

        self.research_label = Label(text="Rch: 0", size_hint=(0.20, 1))
        self.research_label.bind(on_touch_down=self.open_research_popup)
        self.line2.add_widget(self.research_label)

        self.population_label = Label(text="Pop: 0/0 (L:0)", size_hint=(0.30, 1))
        self.population_label.bind(on_touch_down=self.open_population_popup)
        self.line2.add_widget(self.population_label)

        # Suppression de la barre de progression de la population

        self.diamonds_label = Label(text="Diamonds: 0", size_hint=(0.15, 1))
        self.line2.add_widget(self.diamonds_label)

        self.add_widget(self.line2)

        # Ligne 3 : ressources détaillées
        resources_ligne1 = ["wood", "cereal", "stone", "iron", "papyrus"]
        resources_ligne2 = ["meat", "marble", "horse", "glass"]
        resources_ligne3 = ["gunpowder", "coal", "cotton", "spices"]

        self.resources_labels = {}

        # Ligne 1
        self.line_ress1 = BoxLayout(orientation="horizontal", size_hint_y=0.20)
        for resource in resources_ligne1:
            label = Label(text=f"{resource.capitalize()}: 0", size_hint=(0.18, 1))
            label.bind(
                on_touch_down=lambda instance, touch, res=resource:
                self.open_resource_popup(res) if instance.collide_point(*touch.pos) else None
            )
            self.resources_labels[resource] = label
            self.line_ress1.add_widget(label)
        self.add_widget(self.line_ress1)

        # Ligne 2
        self.line_ress2 = BoxLayout(orientation="horizontal", size_hint_y=0.20)
        for resource in resources_ligne2:
            label = Label(text=f"{resource.capitalize()}: 0", size_hint=(0.18, 1))
            label.bind(
                on_touch_down=lambda instance, touch, res=resource:
                self.open_resource_popup(res) if instance.collide_point(*touch.pos) else None
            )
            self.resources_labels[resource] = label
            self.line_ress2.add_widget(label)
        self.add_widget(self.line_ress2)

        # Ligne 3
        self.line_ress3 = BoxLayout(orientation="horizontal", size_hint_y=0.20)
        for resource in resources_ligne3:
            label = Label(text=f"{resource.capitalize()}: 0", size_hint=(0.18, 1))
            label.bind(
                on_touch_down=lambda instance, touch, res=resource:
                self.open_resource_popup(res) if instance.collide_point(*touch.pos) else None
            )
            self.resources_labels[resource] = label
            self.line_ress3.add_widget(label)
        self.add_widget(self.line_ress3)

        # Rafraîchit l'UI locale ET synchronise les ressources serveur toutes les secondes
        Clock.schedule_interval(self.update_resources_from_game, 1)
        Clock.schedule_once(lambda dt: self.update_city_spinner(), 0)
        # Ajoute un polling régulier pour les notifications (badge)
        Clock.schedule_interval(self.refresh_badges, 5)

    def _update_bg_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def get_city_data(self):
        # Toujours retourner la ville active à jour depuis le modèle central
        return self.manager.game_data.get_active_city()

    def update_city_spinner(self):
        self._init_spinner = True
        player = self.manager.game_data.get_current_player()
        city_manager = self.manager.game_data.city_manager
        # Met à jour joueur_id du bouton menu si le joueur change
        if player and self.menu_button.joueur_id != player.id_player:
            self.menu_button.joueur_id = player.id_player
            self.menu_button.update_badge()
        if player:
            player_cities = city_manager.get_cities_for_player(player.id_player)
            city_names = [
                f"{city.name} ({city.island_coords[0]},{city.island_coords[1]})"
                for city in player_cities if hasattr(city, "name") and city.island_coords is not None
            ]
            if list(self.city_spinner.values) != city_names:
                self.city_spinner.values = city_names
            active_city = self.get_city_data()
            active_city_display = (
                f"{active_city.name} ({active_city.island_coords[0]},{active_city.island_coords[1]})"
                if active_city and active_city.island_coords is not None else None
            )
            if active_city and active_city_display in city_names:
                self.city_spinner.text = active_city_display
            else:
                self.city_spinner.text = city_names[0] if city_names else "Aucune ville"
            self.city_spinner.disabled = False if city_names else True
            chosen_display = self.city_spinner.text
            chosen_city = None
            for city in player_cities:
                display = f"{city.name} ({city.island_coords[0]},{city.island_coords[1]})"
                if display == chosen_display:
                    chosen_city = city
                    break
            # self.city_data = chosen_city  # REMOVE: always use get_city_data
        else:
            self.city_spinner.values = []
            self.city_spinner.text = "Aucune ville"
            self.city_spinner.disabled = True
            # self.city_data = None  # REMOVE
        self._init_spinner = False

    def force_update_city_spinner(self):
        self._init_spinner = True
        Clock.schedule_once(lambda dt: self.update_city_spinner(), 0)

    def on_spinner_select(self, spinner, text):
        if self._init_spinner or not text or text == "Aucune ville":
            return
        player = self.manager.game_data.get_current_player()
        city_manager = self.manager.game_data.city_manager
        # Met à jour joueur_id du bouton menu si le joueur change via spinner
        if player and self.menu_button.joueur_id != player.id_player:
            self.menu_button.joueur_id = player.id_player
            self.menu_button.update_badge()
        selected_city = None
        if player:
            for city in city_manager.get_cities_for_player(player.id_player):
                display = f"{city.name} ({city.island_coords[0]},{city.island_coords[1]})"
                if display == text:
                    selected_city = city
                    break
        if selected_city is None:
            return
        self.manager.game_data.set_active_city(selected_city)
        if self.switch_view_callback:
            self.switch_view_callback("city_view", data=selected_city)
        # self.city_data = selected_city  # REMOVE
        self.update_resources(selected_city.get_resources(), selected_city)
        self.update_city_name(selected_city.name)

    def update_city_name(self, city_id):
        self.force_update_city_spinner()

    def toggle_header_visibility(self, instance):
        self.height = 170 if self.height == 120 else 120

    def update_resources(self, resources, city_data):
        player = self.manager.game_data.get_current_player()
        if not player:
            print("[ERREUR] Aucun joueur courant défini, impossible de mettre à jour les ressources.")
            return
        if not city_data:
            print("[ERREUR] Aucune ville active définie, impossible de mettre à jour les ressources.")
            return
        if not resources:
            print("[ERREUR] Les ressources de la ville sont indisponibles.")
            return
        self.gold_label.text = f"Or: {format_number_short(resources.get('gold', 0))}"
        ships_total = getattr(player, "ships", 0)
        ships_available = getattr(player, "ships_available", ships_total)
        self.ships_label.text = f"Bateaux: {ships_available}/{ships_total}"
        research_points = int(getattr(player, "research_points", 0))
        self.research_label.text = f"Rch: {format_number_short(research_points)}"
        max_population = int(self.manager.resource_manager.get_population_data(city_data).get("max", 0))
        current_population = int(resources.get("population_total", 0))
        free_population = int(resources.get("population_free", 0))
        self.population_label.text = f"Pop: {current_population}/{max_population} (L:{free_population})"
        self.diamonds_label.text = f"Diamonds: {getattr(player, 'diamonds', 0)}"
        for resource, label in self.resources_labels.items():
            data = self.manager.resource_manager.get_resource_data(city_data, resource)
            label.text = f"{resource.capitalize()}: {format_number_short(data.get('current_quantity', 0))}"

    def update_resources_from_game(self, dt):
        def fetch_and_update():
            try:
                state = self.manager.network_manager.get_state()
                if state:
                    def update_ui(dt):
                        self.manager.game_data.from_dict(state)
                        active_city = self.get_city_data()
                        if active_city:
                            resources = active_city.get_resources()
                            self.update_resources(resources, active_city)
                        self.menu_button.update_badge()
                        self.update_city_spinner()
                    Clock.schedule_once(update_ui, 0)
            except Exception as e:
                pass
        threading.Thread(target=fetch_and_update, daemon=True).start()

    def open_transports_popup(self, instance, touch):
        if instance.collide_point(*touch.pos):
            popup = TransportsListPopup(
                self.manager.game_data,
                self.transport_manager,
                network_manager=getattr(self.manager, "network_manager", None)
            )
            popup.open()

    def open_resource_popup(self, resource_name):
        city_data = self.get_city_data()
        if city_data:
            popup = ResourcePopup(
                resource_name=resource_name,
                update_callback=lambda res: self.manager.resource_manager.get_resource_data(city_data, res)
            )
            popup.open()

    def open_population_popup(self, instance, touch):
        city_data = self.get_city_data()
        if instance.collide_point(*touch.pos) and city_data:
            PopulationPopup(city_data, self.manager).open()

    def open_gold_popup(self, instance, touch):
        city_data = self.get_city_data()
        if instance.collide_point(*touch.pos) and city_data:
            GoldPopup(city_data, self.manager).open()

    def open_research_popup(self, instance, touch):
        city_data = self.get_city_data()
        if instance.collide_point(*touch.pos) and city_data:
            ResearchPopup(city_data, self.manager).open()

    def _switch_and_update(self, view_name, switch_view_callback):
        active_city = self.get_city_data()
        if view_name == "city_view":
            def after_sync(dt):
                if active_city:
                    self.update_resources(active_city.get_resources(), active_city)
                switch_view_callback(view_name, data=active_city)
            self.update_resources_from_game(0)
            Clock.schedule_once(after_sync, 0.2)
        elif view_name == "island_view":
            # Récupère l’île de la ville active
            island = None
            if active_city and hasattr(active_city, "island_coords"):
                coords = getattr(active_city, "island_coords", None)
                if coords:
                    island = self.manager.game_data.get_island_by_coords(coords)
            switch_view_callback(view_name, data=island)
            if active_city:
                self.update_resources(active_city.get_resources(), active_city)
        elif view_name == "world_view":
            # Centre la vue sur l’île de la ville active
            coords = None
            if active_city and hasattr(active_city, "island_coords"):
                coords = getattr(active_city, "island_coords", None)
            if coords:
                # Passe un dict avec les coordonnées pour forcer le centrage
                switch_view_callback(view_name, data={"center_coords": coords})
            else:
                switch_view_callback(view_name)
            if active_city:
                self.update_resources(active_city.get_resources(), active_city)
        else:
            switch_view_callback(view_name, data=active_city)
            if active_city:
                self.update_resources(active_city.get_resources(), active_city)

    def refresh_badges(self, dt):
        self.menu_button.update_badge()

    def force_refresh_resources(self):
        """A appeler quand la ville active a été modifiée côté modèle (ex: après patch serveur)."""
        active_city = self.get_city_data()
        if active_city:
            resources = active_city.get_resources()
            self.update_resources(resources, active_city)

def format_number_short(n):
    n = float(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}m".rstrip('0').rstrip('.')
    elif n >= 1_000:
        return f"{n/1_000:.1f}k".rstrip('0').rstrip('.')
    else:
        return str(int(n))