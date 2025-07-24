from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from .base_popup import BasePopup

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

class AmbassadePopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_view=None,
        city_id=None,
        manager=None,
        **kwargs
    ):
        for key in ["city_view", "city_id", "manager", "custom_content_callback"]:
            kwargs.pop(key, None)

        self.city_view = city_view
        self.city_id = city_id
        self.manager = manager or getattr(buildings_manager, "manager", None)
        self.buildings_manager = buildings_manager
        self.building_data = building_data
        self.update_all_callback = update_all_callback
        self.city = None  # Pour fallback direct

        if custom_content_callback is None:
            custom_content_callback = self.add_dynamic_info

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=custom_content_callback,
            city_view=city_view,
            **kwargs
        )

        self.ambassade_info_event = Clock.schedule_interval(self.update_ambassade_info, 1)

    def get_city(self):
        if self.city_view and hasattr(self.city_view, "city_data") and self.city_view.city_data is not None:
            return self.city_view.city_data
        if self.city is not None:
            return self.city
        if self.manager and hasattr(self.manager, "game_data") and hasattr(self.manager.game_data, "city_manager"):
            city = self.manager.game_data.city_manager.get_city_by_id(self.city_id)
            if city:
                self.city = city
                return city
        return None

    def add_dynamic_info(self, layout):
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=30, spacing=30)
        colonies_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        colonies_title = make_adaptive_label("Colonies Possédées", min_height=40, bold=True)
        self.colonies_label = make_adaptive_label("", min_height=40)
        colonies_section.add_widget(colonies_title)
        colonies_section.add_widget(self.colonies_label)
        villes_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        villes_title = make_adaptive_label("Liste des Villes", min_height=40, bold=True)
        self.villes_label = make_adaptive_label("", min_height=40)
        villes_section.add_widget(villes_title)
        villes_section.add_widget(self.villes_label)
        self.dynamic_info_layout.add_widget(colonies_section)
        self.dynamic_info_layout.add_widget(villes_section)
        layout.add_widget(self.dynamic_info_layout)
        self.update_ambassade_info()

    def update_ambassade_info(self, *args):
        city = self.get_city()
        if city is None:
            self.colonies_label.text = "Erreur : ville non initialisée"
            self.villes_label.text = ""
            return

        player_id = getattr(city, "owner", None)
        game_data = getattr(getattr(self.city_view, "manager", None), "game_data", None)
        if not game_data and self.manager and hasattr(self.manager, "game_data"):
            game_data = self.manager.game_data
        if not game_data:
            self.colonies_label.text = "Données de jeu indisponibles."
            self.villes_label.text = ""
            return

        player = None
        if player_id:
            try:
                player = game_data.player_manager.get_player(player_id)
            except Exception:
                player = None
        if not player:
            self.colonies_label.text = "Aucun joueur trouvé."
            self.villes_label.text = ""
            return
        nom_joueur = getattr(player, "username", None) or getattr(player, "name", player_id)
        city_manager = getattr(game_data, "city_manager", None)
        villes_possedees = city_manager.get_cities_for_player(player.id_player) if city_manager else []

        building_data = self.buildings_manager.get_building_details(city, "Ambassade")
        try:
            niveau_ambassade = int(building_data.get("level", 1)) if building_data else 1
        except (TypeError, ValueError):
            niveau_ambassade = 1
        max_colonies = niveau_ambassade
        self.colonies_label.text = f"{nom_joueur} : {len(villes_possedees)} / {max_colonies} colonies"
        if villes_possedees:
            noms_villes = [f"{getattr(v, 'name', 'Ville inconnue')} ({getattr(v, 'x', '?')};{getattr(v, 'y', '?')})" for v in villes_possedees]
            noms_villes_uniques = list(dict.fromkeys(noms_villes))
            self.villes_label.text = "\n".join(f"- {nom}" for nom in noms_villes_uniques)
        else:
            self.villes_label.text = "Aucune colonie pour le moment."

    def close(self):
        if hasattr(self, 'ambassade_info_event'):
            self.ambassade_info_event.cancel()
        self.dismiss()