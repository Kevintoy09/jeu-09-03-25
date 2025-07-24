from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window

from data.buildings_database import buildings_database
from widgets.slot_widget import SlotWidget

class CityView(RelativeLayout):

    IMAGE_WIDTH = 2160
    IMAGE_HEIGHT = 1920

    def __init__(self, manager, game_data, buildings_manager, update_all_callback=None, popup_manager=None, network_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.game_data = game_data
        self.buildings_manager = buildings_manager
        self.popup_manager = popup_manager
        self.update_all_callback = update_all_callback
        self.network_manager = network_manager

        self.city_scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale=1.0,
            scale_min=0.3,
            scale_max=3,
            size_hint=(None, None),
            size=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT),
            pos=(0, 0)
        )

        self.drag_surface = Widget(size_hint=(None, None), size=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT), pos=(0, 0))
        self.city_scatter.add_widget(self.drag_surface)

        self.city_content = FloatLayout(size_hint=(None, None), size=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
        self.background_image = Image(
            source="assets/city/default_city.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(None, None),
            size=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT),
            pos=(0, 0)
        )
        self.city_content.add_widget(self.background_image)

        self.interactive_layout = RelativeLayout(size_hint=(None, None), size=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT), pos=(0, 0))
        self.city_content.add_widget(self.interactive_layout)

        self.city_scatter.add_widget(self.city_content)
        self.add_widget(self.city_scatter)

        self.background_image.bind(texture=self.on_background_loaded)
        Window.bind(on_mouse_scroll=self.on_mouse_scroll)
        self.bind(size=self.init_scatter_position)

        self.city_scatter.bind(pos=self.limit_scatter_position)
        self.city_scatter.bind(scale=self.limit_scatter_position)
        self.bind(size=self.limit_scatter_position)

    def calc_min_scale(self):
        win_w, win_h = self.size
        iw, ih = self.background_image.size
        if iw == 0 or ih == 0 or win_w == 0 or win_h == 0:
            return 1.0
        scale_x = win_w / iw
        scale_y = win_h / ih
        return max(scale_x, scale_y)

    def on_background_loaded(self, *args):
        iw, ih = self.IMAGE_WIDTH, self.IMAGE_HEIGHT
        self.background_image.size = (iw, ih)
        self.city_content.size = (iw, ih)
        self.interactive_layout.size = (iw, ih)
        self.drag_surface.size = (iw, ih)
        self.city_scatter.size = (iw, ih)
        self.init_scatter_position()
        self.limit_scatter_position()

    def init_scatter_position(self, *args):
        min_scale = self.calc_min_scale()
        scatter = self.city_scatter
        scatter.scale_min = min_scale
        scatter.scale = min_scale
        win_w, win_h = self.size
        img_w, img_h = self.background_image.size
        scaled_w, scaled_h = img_w * scatter.scale, img_h * scatter.scale
        scatter.pos = (
            (win_w - scaled_w) / 2,
            (win_h - scaled_h) / 2,
        )
        self.limit_scatter_position()

    def limit_scatter_position(self, *args):
        scatter = self.city_scatter
        win_w, win_h = self.size
        img_w = self.background_image.size[0] * scatter.scale
        img_h = self.background_image.size[1] * scatter.scale

        if img_w <= win_w:
            min_x = max_x = (win_w - img_w) / 2
        else:
            min_x = win_w - img_w
            max_x = 0

        if img_h <= win_h:
            min_y = max_y = (win_h - img_h) / 2
        else:
            min_y = win_h - img_h
            max_y = 0

        new_x = min(max(scatter.x, min_x), max_x)
        new_y = min(max(scatter.y, min_y), max_y)
        scatter.pos = (new_x, new_y)

    def on_mouse_scroll(self, window, x, y, scroll_x, scroll_y):
        scatter = self.city_scatter
        min_scale = scatter.scale_min
        max_scale = scatter.scale_max
        if scroll_y != 0:
            anchor = scatter.to_widget(x, y)
            scale_factor = 1.1 if scroll_y > 0 else 0.9
            new_scale = scatter.scale * scale_factor
            new_scale = max(min_scale, min(max_scale, new_scale))
            if new_scale != scatter.scale:
                scale_factor = new_scale / scatter.scale
                scatter.apply_transform(
                    scatter.get_scale_matrix(
                        scale_factor, scale_factor, scale_factor,
                        anchor=anchor
                    )
                )
                self.limit_scatter_position()
            return True
        return False

    def get_city_data(self):
        return self.game_data.get_active_city()

    def sync_and_update_city(self):
        def sync_task():
            if self.network_manager is not None:
                self.network_manager.sync_game_data(self.game_data)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.update_city())
        import threading
        threading.Thread(target=sync_task, daemon=True).start()

    def _display_slots(self, city_data, disabled=False):
        self.interactive_layout.clear_widgets()
        layout = self.get_city_layout(city_data)
        if not layout:
            return
        slots = layout.get("slots", [])
        buildings = city_data.get_buildings() if hasattr(city_data, "get_buildings") else [None] * len(slots)
        for i, slot in enumerate(slots):
            building = buildings[i] if i < len(buildings) else None
            slot_widget = SlotWidget(
                building=building,
                slot_index=i,
                disabled=disabled or slot.get("locked", False),
                category=slot.get("type", ""),
                city_data=city_data,
                buildings_manager=self.buildings_manager,
                popup_manager=self.popup_manager,
                network_manager=self.network_manager,
                update_all_callback=self.update_all_callback,
                size_hint=(0.07, 0.07),
                pos_hint={"x": slot["x"], "y": slot["y"]},
                timer_font_size="28sp",
                timer_banner_width_hint=1.27,
                timer_height=61,
                timer_label_pos_hint={"center_x": 0.5, "top": 2.24},
            )
            self.interactive_layout.add_widget(slot_widget)

    def update_city(self, city_data=None):
        self.readonly_mode = False
        city_data = self.get_city_data()
        if not city_data:
            self.interactive_layout.clear_widgets()
            return
        layout = self.get_city_layout(city_data)
        if layout:
            self.background_image.source = layout.get("background", "assets/city/default_city.png")
        else:
            self.background_image.source = "assets/city/default_city.png"
        self._display_slots(city_data, disabled=False)

    def view_city(self, city_data):
        self.readonly_mode = True
        self._display_slots(city_data, disabled=True)

    def safe_show_building_popup(self, building, slot_index, instance=None):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.show_building_popup(building, slot_index))

    def show_building_popup(self, building, slot_index, instance=None):
        building_name = getattr(building, 'name', None)
        if not building_name:
            return
        building_data_full = {k: v for k, v in buildings_database.get(building_name, {}).items()
                              if isinstance(v, (str, int, float, list, dict, type(None)))}
        for k, v in building.__dict__.items():
            if k not in ("levels", "description") and isinstance(v, (str, int, float, list, dict, type(None))):
                building_data_full[k] = v
        building_data_full["slot_index"] = slot_index
        for key in list(building_data_full.keys()):
            if not isinstance(building_data_full[key], (str, int, float, list, dict, type(None))):
                del building_data_full[key]

        if self.popup_manager:
            self.popup_manager.show_popup(
                building_name,
                building_data_full,
                self.update_all_callback,
                self.get_city_data(),
                self,
            )

    def open_building_popup(self, slot_index, category, instance=None):
        if self.buildings_manager is None:
            return
        from kivy.uix.popup import Popup
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button

        popup = Popup(title=f"Choisir un bâtiment ({category})", size_hint=(0.8, 0.8))

        scrollview = ScrollView(size_hint=(1, 1))
        popup_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        popup_layout.bind(minimum_height=popup_layout.setter('height'))

        city_buildings = self.buildings_manager.get_city_building_data(self.get_city_data())
        for building_name, building_data in city_buildings.items():
            if buildings_database[building_name].get("category", "").strip().lower() != category.strip().lower():
                continue
            levels = building_data.get("levels", [])
            if not levels:
                continue
            details = (
                f"[b]{building_name}[/b]\n"
                f"{buildings_database[building_name].get('description', 'Description indisponible')}\n"
                f"Coût : {', '.join(f'{k}: {v}' for k, v in levels[0]['cost'].items())}\n"
                f"Temps : {levels[0]['construction_time']}s"
            )
            button = Button(
                text=details,
                markup=True,
                size_hint_y=None,
                height=100,
                background_normal='',
                background_color=(0, 0, 0, 0.3)
            )
            from functools import partial
            button.bind(on_press=partial(self.start_building, slot_index, building_name, popup))
            popup_layout.add_widget(button)

        scrollview.add_widget(popup_layout)
        popup.content = scrollview
        popup.open()

    def start_building(self, slot_index, building_name, popup, instance):
        city = self.get_city_data()
        try:
            if self.network_manager is None:
                raise Exception("NetworkManager requis pour la construction REST.")
            resp = self.network_manager.build_batiment(
                username=self.manager.username,
                city_id=getattr(city, "id", None),
                building_name=building_name,
                slot_index=slot_index,
                player_id=self.manager.player_id,
            )
            if resp and resp.get("success") is True:
                building_resp = resp.get("building")
                if building_resp and hasattr(popup, "update_building_data"):
                    popup.update_building_data(building_resp)
                city_update = resp.get("city")
                if city_update:
                    city_manager = getattr(self.game_data, "city_manager", None)
                    if city_manager is not None:
                        city_manager.update_city_from_dict(city_update)
                        city_id = city_update.get("id")
                        city_manager.set_active_city(city_manager.get_city_by_id(city_id))
                    else:
                        from models.city import City
                        if hasattr(city, "set_buildings"):
                            city.set_buildings(city_update.get("buildings", []))
                        else:
                            city.buildings = City.deserialize_buildings(city_update.get("buildings", []), city=city)
                self.sync_and_update_city()
            else:
                error_msg = ""
                if resp and resp.get("error"):
                    error_msg = str(resp.get("error"))
                elif resp and resp.get("status"):
                    error_msg = str(resp.get("status"))
                elif resp:
                    error_msg = "Erreur inconnue"
                else:
                    error_msg = "Pas de réponse du serveur"
                lower_msg = error_msg.lower()
                if "ressource" in lower_msg and "insuffisant" in lower_msg:
                    error_msg = "Ressources insuffisantes pour la construction."
                elif "resource" in lower_msg and "not enough" in lower_msg:
                    error_msg = "Not enough resources for construction."
                self.show_error_popup("Erreur construction : " + error_msg)
        except Exception:
            self.show_error_popup("Erreur lors de la tentative de construction (voir console).")
            popup.dismiss()
            return

        popup.dismiss()
        if self.update_all_callback:
            self.update_all_callback()

    def show_error_popup(self, message):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        popup = Popup(title="Erreur", size_hint=(0.7, 0.3))
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(Button(text=message, size_hint_y=0.7))
        close_btn = Button(text="Fermer", size_hint_y=0.3)
        close_btn.bind(on_press=popup.dismiss)
        layout.add_widget(close_btn)
        popup.content = layout
        popup.open()

    def get_city_layout(self, city_data):
        island_coords = getattr(city_data, "island_coords", None)
        island = self.game_data.get_island_by_coords(island_coords)
        if not island:
            return None
        layout_key = island.get("city_layout")
        if not layout_key:
            return None
        layout = self.game_data.city_layouts.get(layout_key)
        return layout