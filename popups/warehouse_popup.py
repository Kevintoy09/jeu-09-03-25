from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from .base_popup import BasePopup
from data.buildings_database import buildings_database
from models.constants import DEFAULT_STORAGE_CAPACITY

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

class WarehousePopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_id=None,
        **kwargs
    ):
        # Nettoyage kwargs pour ne rien passer de métier à Kivy
        kwargs.pop("city_id", None)
        kwargs.pop("manager", None)

        self.city_id = city_id
        self.resource_manager = getattr(buildings_manager, 'resource_manager', None)

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
        self.warehouse_info_event = Clock.schedule_interval(self.update_warehouse_info, 1)

    def get_city(self):
        # Recherche la ville à partir de city_id si possible (game_data accessible via buildings_manager)
        if hasattr(self, "city_id") and self.city_id is not None:
            game_data = getattr(self.buildings_manager, "game_data", None)
            if game_data and hasattr(game_data, "city_manager"):
                return game_data.city_manager.get_city_by_id(self.city_id)
        return None

    def add_dynamic_info(self, layout):
        from kivy.uix.gridlayout import GridLayout
        from data.resources_database import RESOURCES

        self.table_layout = GridLayout(cols=5, size_hint_y=None, spacing=10, padding=20)
        self.table_layout.bind(minimum_height=self.table_layout.setter('height'))

        # En-têtes
        headers = ["Ressource", "Quantité", " Qté sécurisée", "Pillable", "Capacité max"]
        for h in headers:
            self.table_layout.add_widget(make_adaptive_label(f"[b]{h}[/b]", min_height=40, bold=True))

        self.resource_rows = {}
        for res_key, res_data in RESOURCES.items():
            row = []
            for _ in range(5):
                lbl = make_adaptive_label("", min_height=30)
                self.table_layout.add_widget(lbl)
                row.append(lbl)
            self.resource_rows[res_key] = row

        layout.add_widget(self.table_layout)
        self.update_warehouse_info()

    def update_warehouse_info(self, *args):
        from data.resources_database import RESOURCES

        city = self.get_city()
        if not city:
            for row in self.resource_rows.values():
                for lbl in row:
                    lbl.text = ""
            return

        # Cumul des capacités de tous les entrepôts terminés
        secure_storage_total = {}
        storage_total = {}
        for building in city.get_buildings():
            if building and building.get_name() == "Entrepôt" and building.get_status() == "Terminé":
                level = building.get_level()
                effects = buildings_database["Entrepôt"]["levels"][level - 1]["effect"]
                for res, val in effects.get("secure_storage", {}).items():
                    secure_storage_total[res] = secure_storage_total.get(res, 0) + val
                for res, val in effects.get("storage", {}).items():
                    storage_total[res] = storage_total.get(res, 0) + val

        resources = city.get_resources()
        for res_key, row in self.resource_rows.items():
            res_name = RESOURCES[res_key]["name"]
            qty = int(resources.get(res_key, 0))
            secure = int(secure_storage_total.get(res_key, 0))
            base = DEFAULT_STORAGE_CAPACITY.get(res_key, 0)
            bonus = int(storage_total.get(res_key, 0)) if res_key in storage_total else 0
            cap = base + bonus if (base + bonus) > 0 else ""
            pillable = max(qty - secure, 0)
            row[0].text = res_name
            row[1].text = str(qty)
            row[2].text = str(secure)
            row[3].text = str(pillable)
            row[4].text = str(cap) if cap != "" else "-"

    def close(self):
        if hasattr(self, 'warehouse_info_event'):
            self.warehouse_info_event.cancel()
        self.dismiss()