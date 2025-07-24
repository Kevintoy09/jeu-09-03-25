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

class MinePopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_view=None,
        **kwargs
    ):
        kwargs.pop("city_view", None)

        self.city_view = city_view
        self.building_data = building_data
        self.update_all_callback = update_all_callback

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
        self.mine_info_event = Clock.schedule_interval(self.update_mine_info, 1)

    def add_dynamic_info(self, layout):
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=30, spacing=30)

        production_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        production_title = make_adaptive_label("Production Actuelle", min_height=40, bold=True)
        self.production_label = make_adaptive_label("", min_height=40)
        production_section.add_widget(production_title)
        production_section.add_widget(self.production_label)

        resource_section = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        resource_title = make_adaptive_label("Niveaux des Ressources", min_height=40, bold=True)
        self.resource_label = make_adaptive_label("", min_height=40)
        resource_section.add_widget(resource_title)
        resource_section.add_widget(self.resource_label)

        self.dynamic_info_layout.add_widget(production_section)
        self.dynamic_info_layout.add_widget(resource_section)

        layout.add_widget(self.dynamic_info_layout)
        self.update_mine_info()

    def update_mine_info(self, *args):
        if not self.city_view or not hasattr(self.city_view, "city_data") or self.city_view.city_data is None:
            self.production_label.text = "Erreur : ville non initialisée"
            self.resource_label.text = ""
            return

        city = self.city_view.city_data

        resource_manager = getattr(self.city_view.manager.game_data, "resource_manager", None)
        if not resource_manager:
            self.production_label.text = "Erreur : gestionnaire de ressources manquant"
            self.resource_label.text = ""
            return

        production_rate = resource_manager.calculate_productivity(city, "iron")

        resources = getattr(city, "resources", {})
        resource_levels = {
            "iron": resources.get("iron", 0),
            "gold": resources.get("gold", 0),
            "stone": resources.get("stone", 0)
        }

        production_text = f"Production: {production_rate} unités/seconde"
        resource_text = "\n".join([f"{resource.capitalize()}: {level}" for resource, level in resource_levels.items()])

        self.production_label.text = production_text
        self.resource_label.text = resource_text

    def close(self):
        if hasattr(self, 'mine_info_event'):
            self.mine_info_event.cancel()
        self.dismiss()