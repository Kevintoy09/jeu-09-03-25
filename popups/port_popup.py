from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.button import Button
from .base_popup import BasePopup
from popups.transport_list_popup import PortTransportsManager
from models.transport import open_transport_popup_generic
import math

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

class PortPopup(BasePopup):
    def __init__(
        self,
        title,
        port_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city=None,
        city_id=None,
        transport_manager=None,
        network_manager=None,
        **kwargs
    ):
        # Nettoyage kwargs pour ne RIEN passer à Kivy qui serait métier ou non-attendu
        for key in ["city_id", "manager", "transport_manager", "network_manager", "city"]:
            kwargs.pop(key, None)

        self.city_id = city_id or (getattr(city, "id", None) if city is not None else None)
        self.resource_manager = getattr(buildings_manager, "resource_manager", None)
        self.transport_manager = transport_manager
        self.network_manager = network_manager
        self.port_data = port_data
        self.update_all_callback = update_all_callback

        self.port_data.setdefault("level", 1)
        self.port_data.setdefault("ships", 1)
        self.levels = self.port_data.get("levels", [])

        if custom_content_callback is None:
            custom_content_callback = self.add_dynamic_info

        super().__init__(
            title,
            port_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=custom_content_callback,
            city_id=self.city_id,
            network_manager=network_manager,
            **kwargs
        )

        self.port_info_event = Clock.schedule_interval(self.update_port_info, 1)

    def get_city(self):
        # Recherche la ville à partir de city_id si possible (game_data accessible via buildings_manager)
        if hasattr(self, "city_id") and self.city_id is not None:
            game_data = getattr(self.resource_manager, "game_data", None)
            if game_data and hasattr(game_data, "city_manager"):
                return game_data.city_manager.get_city_by_id(self.city_id)
        return None

    def add_dynamic_info(self, layout):
        label_height = 22
        info_labels = [
            "level_label", "loading_speed_label", "transport_speed_label",
            "ships_label", "gold_label", "next_ship_price_label", "upgrade_price_label"
        ]
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))

        for label_attr in info_labels:
            lbl = make_adaptive_label("", min_height=label_height)
            setattr(self, label_attr, lbl)
            self.dynamic_info_layout.add_widget(lbl)

        # Label d'erreur pour retour utilisateur
        self.error_label = make_adaptive_label("", min_height=label_height, color=(1,0,0,1))
        self.dynamic_info_layout.add_widget(self.error_label)

        # Bouton achat bateau
        buy_ship_button = Button(text="Acheter un bateau", size_hint_y=None, height=label_height+4)
        buy_ship_button.bind(on_press=lambda instance: self.buy_ship())
        self.dynamic_info_layout.add_widget(buy_ship_button)

        layout.add_widget(self.dynamic_info_layout)
        self.update_port_info()

        player = self.resource_manager.game_data.get_current_player()
        city_origin = self.get_city()
        if not city_origin:
            layout.add_widget(make_adaptive_label("[ERREUR] City non initialisée pour ce popup", min_height=30))
            return
        city_manager = self.resource_manager.game_data.city_manager
        cities = [city for city in city_manager.get_cities_for_player(getattr(player, "id_player", None)) if city != city_origin]

        self.cities_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        if not cities:
            self.cities_layout.add_widget(make_adaptive_label("Aucune autre ville pour ce joueur.", min_height=40, size_hint_x=1))
        for city in cities:
            btn_text = f"{city.name} {getattr(city, 'island_coords', '')}"
            btn = Button(text=btn_text, size_hint_x=None, width=150)
            btn.bind(on_press=lambda instance, city=city: self.open_transport_popup(city))
            self.cities_layout.add_widget(btn)
        layout.add_widget(self.cities_layout)

        self.transports_manager = PortTransportsManager(self)
        self.transports_manager.build_transports_list_layout(layout)

    def get_player_name_by_id(self, player_id):
        game_data = self.resource_manager.game_data
        try:
            player = game_data.player_manager.get_player(player_id)
            return player.username
        except Exception:
            return "Joueur ?"

    def has_port(self, city):
        for b in getattr(city, "buildings", []):
            if b and getattr(b, "name", "").lower() == "port":
                return getattr(b, "level", 1) >= 1
        return False

    def open_transport_popup(self, city_dest):
        city_data = self.get_city()
        if not city_data:
            return
        from_city = city_data
        player = self.resource_manager.game_data.get_current_player()
        open_transport_popup_generic(
            from_city=from_city,
            city_dest=city_dest,
            player=player,
            port_data=self.port_data,
            transport_manager=self.transport_manager,
            network_manager=self.network_manager,
            joueur_dest=None,
            parent_popup=None
        )

    def get_loading_speed(self):
        level = self.port_data.get("level", 1)
        if self.levels and 1 <= level <= len(self.levels):
            return self.levels[level - 1].get("effect", {}).get("loading_speed", 10)
        return level * 10

    def get_transport_speed(self):
        return 12.2

    def get_next_ship_price(self):
        player = self.resource_manager.game_data.get_current_player()
        ships = getattr(player, "ships", 1)
        base = 100
        return int(math.ceil(base * (1.5 ** (ships - 1))))

    def get_upgrade_price(self):
        return int(200 * self.port_data.get("level", 1))

    def buy_ship(self):
        city_data = self.get_city()
        if not city_data:
            if hasattr(self, "error_label"):
                self.error_label.text = "Erreur : ville non trouvée."
            return
        city = city_data
        player = self.resource_manager.game_data.get_current_player()
        if not self.network_manager:
            if hasattr(self, "error_label"):
                self.error_label.text = "Erreur : pas de connexion réseau."
            return

        response = self.network_manager.buy_ship(player.id_player, city.id)
        if response and response.get("success"):
            player.ships = response["ships"]
            player.ships_available = response["ships_available"]
            if "gold" in response:
                city.resources["gold"] = response["gold"]
            if hasattr(self, "update_header_callback") and self.update_header_callback:
                self.update_header_callback()
            if self.update_all_callback:
                self.update_all_callback()
            self.update_port_info()
            if hasattr(self, "error_label"):
                self.error_label.text = ""  # Efface message d'erreur précédent
        else:
            error_msg = "Achat de bateau impossible."
            if response and "error" in response:
                error_msg += f" {response['error']}"
            if hasattr(self, "error_label"):
                self.error_label.text = error_msg

    def update_port_info(self, *args):
        try:
            city_data = self.get_city()
            if not city_data:
                return
            city = city_data
            resources = city.get_resources()
            lspeed = self.get_loading_speed()
            tspeed = self.get_transport_speed()
            next_ship_price = self.get_next_ship_price()
            upgrade_price = self.get_upgrade_price()

            player = self.resource_manager.game_data.get_current_player()
            ships_total = getattr(player, "ships", 0)
            ships_available = getattr(player, "ships_available", ships_total)

            self.level_label.text = f"Niveau du port : {self.port_data.get('level', 1)}"
            self.loading_speed_label.text = f"Vitesse de chargement : {lspeed} unités/sec"
            self.transport_speed_label.text = f"Vitesse de transport : {tspeed} unités/sec"
            self.ships_label.text = f"Bateaux : {ships_available} / {ships_total}"
            self.gold_label.text = f"Or disponible : {int(resources.get('gold', 0))}"
            self.next_ship_price_label.text = f"Prix du prochain bateau : {next_ship_price} or"
            self.upgrade_price_label.text = f"Prix amélioration port : {upgrade_price} or"
        except Exception:
            pass

    def close(self):
        if hasattr(self, 'port_info_event') and self.port_info_event:
            self.port_info_event.cancel()
        self.dismiss()