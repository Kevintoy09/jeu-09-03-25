from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from config.style import apply_button_style, apply_label_style
import os

class IslandSelectionScreen(BoxLayout):
    def __init__(self, switch_view_callback, game_data, manager=None, **kwargs):
        super(IslandSelectionScreen, self).__init__(**kwargs)
        self.switch_view_callback = switch_view_callback
        self.game_data = game_data
        self.manager = manager
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = [20, 20, 20, 20]

        self.title = Label(text='Sélection de l\'Île', font_size='40sp', size_hint=(1, 0.1))
        apply_label_style(self.title)
        self.add_widget(self.title)

        if not getattr(self.game_data, "islands", None) or not self.game_data.islands:
            no_island_label = Label(text="Aucune île disponible dans les données de jeu.", size_hint=(1, 0.5))
            apply_label_style(no_island_label)
            self.add_widget(no_island_label)
            return

        def create_island_section(image_path, description, island_type, island_coords):
            section_layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, None), height=200)
            if not os.path.isfile(image_path):
                image_path = 'assets/island_selection/default_island.png'
            island_button = Button(background_normal=image_path, size_hint=(1, None), height=150)
            island_button.bind(on_press=lambda x: self.select_island(island_type, island_coords))
            apply_button_style(island_button)

            description_label = Label(text=description, size_hint=(1, None), height=50)
            apply_label_style(description_label)

            section_layout.add_widget(island_button)
            section_layout.add_widget(description_label)
            return section_layout

        for island in self.game_data.islands:
            base_resource = island.get("base_resource", "mystère")
            description = f"Île {base_resource.capitalize()} : {base_resource.capitalize()}"
            image_path = f'assets/island_selection/{base_resource}_island.png'
            self.add_widget(create_island_section(
                image_path,
                description,
                base_resource,
                island["coords"]
            ))

    def select_island(self, island_type, island_coords):
        self.show_select_city_popup(island_type, island_coords)

    def show_select_city_popup(self, island_type, island_coords):
        free_cities = [
            city for city in self.game_data.city_manager.get_all_cities()
            if getattr(city, 'island_coords', None) == island_coords and (getattr(city, 'owner', '') in ('', 0))
        ]
        if not free_cities:
            self.show_info_popup("Aucune ville sans propriétaire trouvée sur cette île.")
            return

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        message = Label(
            text=f"Sélectionnez une ville libre sur l'île {island_type.capitalize()} :",
            size_hint=(1, 0.3)
        )
        content.add_widget(message)

        for city in free_cities:
            city_name = getattr(city, "name", "Ville ?")
            btn = Button(text=f"{city_name}", size_hint=(1, None), height=40)
            btn.bind(on_press=lambda instance, c=city: self.select_city_on_server(c, island_coords))
            apply_button_style(btn)
            content.add_widget(btn)

        popup = Popup(title="Choix de la ville", content=content, size_hint=(0.8, 0.7))
        popup.open()
        self._current_city_popup = popup

    def select_city_on_server(self, city, island_coords):
        if hasattr(self, '_current_city_popup') and self._current_city_popup:
            self._current_city_popup.dismiss()
            self._current_city_popup = None
        self.assign_city_to_player(city, island_coords)

    def assign_city_to_player(self, city, island_coords):
        from kivy.app import App
        manager = self.manager
        if not manager and hasattr(self.switch_view_callback, "__self__"):
            manager = getattr(self.switch_view_callback, "__self__", None)
        network_manager = getattr(manager, "network_manager", None)
        player = self.game_data.player_manager.get_player(self.game_data.current_player_id) if self.game_data.current_player_id else None
        username = player.username if player else None
        city_id = getattr(city, "id", None)
        if username and city_id and network_manager:
            try:
                resp = network_manager.select_city(username, city_id)
                if resp and resp.get("city"):
                    if manager and hasattr(manager, "sync_from_server"):
                        manager.sync_from_server()
                    if self.switch_view_callback:
                        self.switch_view_callback("city_view")
                else:
                    self.show_info_popup("Le serveur a refusé la sélection de cette ville.")
            except Exception:
                self.show_info_popup("Erreur réseau lors de la sélection de la ville.")
                return
        else:
            self.show_info_popup("Impossible d'assigner la ville : identifiants manquants.")

    def show_info_popup(self, message):
        popup = Popup(title="Info", size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical')
        msg_label = Label(text=message)
        content.add_widget(msg_label)
        close_button = Button(text='OK', size_hint_y=None, height='40dp')
        close_button.bind(on_press=popup.dismiss)
        content.add_widget(close_button)
        popup.content = content
        popup.open()