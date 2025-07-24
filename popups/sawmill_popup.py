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

class SawmillPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_view=None,
        city_id=None,
        **kwargs
    ):
        # Nettoyage des kwargs pour ne RIEN passer à Kivy qui ne soit pas une propriété
        kwargs.pop("manager", None)
        kwargs.pop("city_id", None)
        kwargs.pop("city_view", None)
        kwargs.pop("custom_content_callback", None)

        self.city_id = city_id
        self.city_view = city_view
        self.building_data = building_data
        self.update_all_callback = update_all_callback
        self.buildings_manager = buildings_manager

        if custom_content_callback is None:
            custom_content_callback = self.add_dynamic_info

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=custom_content_callback,
            city_id=city_id,
            city_view=city_view,
            **kwargs
        )
        self.sawmill_info_event = Clock.schedule_interval(self.update_sawmill_info, 1)

    def get_city(self):
        # Recherche la ville à partir de city_id si possible (game_data accessible via buildings_manager)
        if hasattr(self, "city_id") and self.city_id is not None:
            game_data = getattr(self.buildings_manager, "game_data", None)
            if game_data and hasattr(game_data, "city_manager"):
                return game_data.city_manager.get_city_by_id(self.city_id)
        return None

    def add_dynamic_info(self, layout):
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=30, spacing=30)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))

        # Section Production
        production_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        production_section.bind(minimum_height=production_section.setter('height'))
        production_title = make_adaptive_label("Production Actuelle", min_height=40, bold=True)
        self.production_label = make_adaptive_label("", min_height=40)
        production_section.add_widget(production_title)
        production_section.add_widget(self.production_label)

        # Section Ressources
        resource_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        resource_section.bind(minimum_height=resource_section.setter('height'))
        resource_title = make_adaptive_label("Niveaux des Ressources", min_height=40, bold=True)
        self.resource_label = make_adaptive_label("", min_height=40)
        resource_section.add_widget(resource_title)
        resource_section.add_widget(self.resource_label)

        self.dynamic_info_layout.add_widget(production_section)
        self.dynamic_info_layout.add_widget(resource_section)

        layout.add_widget(self.dynamic_info_layout)
        self.update_sawmill_info()

    def update_sawmill_info(self, *args):
        city = self.get_city()
        if not city:
            self.production_label.text = "Erreur : ville non initialisée"
            self.resource_label.text = ""
            return

        # Recherche du resource_manager via buildings_manager
        resource_manager = getattr(self.buildings_manager, "resource_manager", None)
        if not resource_manager:
            self.production_label.text = "Erreur : res. manager manquant"
            self.resource_label.text = ""
            return

        production_rate = resource_manager.calculate_productivity(city, "wood")
        resources = city.get_resources()
        resource_levels = {
            "wood": resources.get("wood", 0)
        }

        production_text = f"Production: {production_rate} unités/seconde"
        resource_text = f"Wood: {resource_levels['wood']}"

        self.production_label.text = production_text
        self.resource_label.text = resource_text

    def close(self):
        if hasattr(self, 'sawmill_info_event'):
            self.sawmill_info_event.cancel()
        self.dismiss()