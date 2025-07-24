from .base_popup import BasePopup
from kivy.uix.label import Label

class BarracksPopup(BasePopup):
    def __init__(self, building_data, update_city_callback, update_header_callback, **kwargs):
        super().__init__("Caserne", building_data, update_city_callback, update_header_callback, **kwargs)
        self.add_dynamic_info()

    def add_dynamic_info(self):
        self.layout.add_widget(
            Label(
                text="Permet de produire des unités militaires pour défendre ou attaquer.",
                size_hint_y=None,
                height=40,
            )
        )