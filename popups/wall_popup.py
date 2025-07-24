from .base_popup import BasePopup
from kivy.uix.label import Label

class WallPopup(BasePopup):
    def __init__(self, building_data, update_city_callback, update_header_callback, **kwargs):
        super().__init__("Muraille", building_data, update_city_callback, update_header_callback, **kwargs)
        self.add_dynamic_info()

    def add_dynamic_info(self):
        self.layout.add_widget(
            Label(
                text="Augmente la défense de la ville contre les attaques.",
                size_hint_y=None,
                height=40,
            )
        )