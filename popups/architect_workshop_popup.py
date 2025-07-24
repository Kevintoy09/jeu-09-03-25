from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from .base_popup import BasePopup

class ArchitectWorkshopPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        city_view=None,
        **kwargs
    ):
        self.city_view = city_view
        self.building_data = building_data
        self.update_all_callback = update_all_callback

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            city_view=city_view,
            **kwargs
        )
        # Ajoute la section dynamique bonus architecte en bas du layout principal
        self.add_dynamic_info(self.main_layout)
        self.architect_info_event = Clock.schedule_interval(self.update_architect_info, 1)

    def add_dynamic_info(self, layout):
        # Layout dynamique avec hauteur auto
        self.dynamic_info_layout = BoxLayout(orientation='vertical', spacing=30, padding=30, size_hint_y=None)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))

        # Section effets
        effects_section = BoxLayout(orientation='vertical', spacing=20, padding=20, size_hint_y=None)
        effects_section.bind(minimum_height=effects_section.setter('height'))
        effects_title = Label(text="Effets Actuels", size_hint_y=None, height=40, bold=True)
        self.effects_label = Label(size_hint_y=None, height=40)
        effects_section.add_widget(effects_title)
        effects_section.add_widget(self.effects_label)

        self.dynamic_info_layout.add_widget(effects_section)
        layout.add_widget(self.dynamic_info_layout)
        self.update_architect_info()

    def update_architect_info(self, *args):
        # Robustesse : vérifie que le label existe et que city_view/city_data existent
        if not hasattr(self, 'effects_label') or self.effects_label is None:
            return
        if not self.city_view or not hasattr(self.city_view, "city_data") or self.city_view.city_data is None:
            self.effects_label.text = "Erreur : ville non initialisée"
            return

        city = self.city_view.city_data
        effects = {
            "construction_speed": city.resources.get("construction_speed_bonus", 0) if hasattr(city, "resources") else 0,
            "maintenance_cost": city.resources.get("maintenance_cost_reduction", 0) if hasattr(city, "resources") else 0
        }
        effects_text = "\n".join([f"{effect}: {value}%" for effect, value in effects.items()])

        self.effects_label.text = effects_text

    def close(self):
        if hasattr(self, 'architect_info_event'):
            self.architect_info_event.cancel()
        self.dismiss()