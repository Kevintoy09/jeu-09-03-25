from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
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

class GranaryPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_id=None,
        manager=None,
        network_manager=None,
        **kwargs
    ):
        for key in ["city_id", "manager", "network_manager"]:
            kwargs.pop(key, None)

        self.city_id = city_id
        self.manager = manager
        self.network_manager = network_manager
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
            city_id=city_id,
            **kwargs
        )

    def get_city(self):
        if self.manager and hasattr(self.manager, "game_data") and hasattr(self.manager.game_data, "city_manager"):
            return self.manager.game_data.city_manager.get_city_by_id(self.city_id)
        return None

    def add_dynamic_info(self, layout):
        city = self.get_city()
        if not city:
            layout.add_widget(make_adaptive_label("[b]Erreur : ville non initialisée[/b]", markup=True, min_height=40))
            return

        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))

        self.dynamic_info_layout.add_widget(make_adaptive_label("[b]Détails spécifiques :[/b]", markup=True, min_height=40))
        normal_rate = getattr(city, "cereal_consumption_rate", 0.1)
        self.cereal_per_capita_label = make_adaptive_label(f"Consommation de céréales / habitant : {normal_rate:.2f}", min_height=30)
        self.dynamic_info_layout.add_widget(self.cereal_per_capita_label)

        layout.add_widget(self.dynamic_info_layout)

    def apply_cereal_multiplier(self):
        city = self.get_city()
        if not city:
            return
        city.granary_consumption_multiplier = self.multiplier
        if self.update_all_callback:
            self.update_all_callback(city)