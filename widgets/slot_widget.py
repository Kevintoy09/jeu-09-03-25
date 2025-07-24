from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from widgets.timer_widget import TimerWidget
from kivy.clock import Clock
from models.building import Building
from kivy.graphics import Color, RoundedRectangle

class SlotWidget(RelativeLayout):
    """
    Widget d'emplacement de bâtiment : affiche l'état d'un slot (vide, en construction, terminé)
    et permet l'action utilisateur (ouvrir popup, lancer construction).
    Toute logique métier/affichage doit passer par le modèle (Building).
    """
    building = ObjectProperty(None, allownone=True, rebind=False)
    slot_index = NumericProperty(None, allownone=True)
    disabled = ObjectProperty(False)
    category = StringProperty("")
    city_data = ObjectProperty(None)
    buildings_manager = ObjectProperty(None)
    popup_manager = ObjectProperty(None)
    network_manager = ObjectProperty(None)
    update_all_callback = ObjectProperty(None)
    is_under_construction = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.timer_font_size = kwargs.pop('timer_font_size', "18sp")
        self.timer_banner_width_hint = kwargs.pop('timer_banner_width_hint', 0.98)
        self.timer_height = kwargs.pop('timer_height', 54)
        self.timer_label_pos_hint = kwargs.pop('timer_label_pos_hint', {"center_x": 0.5, "top": 1.1})

        self.timer_widget = None
        building = kwargs.pop('building', None) if 'building' in kwargs else None

        super().__init__(**kwargs)
        self.bg_slot = Image(
            source="assets/buildings/logo_slot.png",
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            opacity=1
        )
        self.bg_construction = Image(
            source="assets/buildings/logo_construction.png",
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            opacity=0
        )
        self.bg_end = Image(
            source="assets/buildings/logo_construction_end.png",  # sera remplacé dynamiquement
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            opacity=0
        )
        self.add_widget(self.bg_slot)
        self.add_widget(self.bg_construction)
        self.add_widget(self.bg_end)
        self.label_bg = RelativeLayout(
            size_hint=(0.92, None),
            height=54,
            pos_hint={"center_x": 0.5, "top": 1},
            opacity=0
        )
        with self.label_bg.canvas.before:
            Color(0.98, 0.93, 0.82, 0.92)
            self.label_bg_rect = RoundedRectangle(radius=[18], pos=self.label_bg.pos, size=self.label_bg.size)
        self.label_bg.bind(pos=lambda inst, val: setattr(self.label_bg_rect, 'pos', val))
        self.label_bg.bind(size=lambda inst, val: setattr(self.label_bg_rect, 'size', val))
        self.add_widget(self.label_bg)
        self.label = Label(
            text="",
            size_hint=(1.5, None),
            height=60,
            pos_hint={"center_x": 0.5, "y": -0.58},
            halign="center",
            valign="middle",
            color=(0.15, 0.08, 0, 1),
            font_size="26sp"
        )
        with self.label.canvas.before:
            Color(0.98, 0.93, 0.82, 0.92)
            self.label_rect = RoundedRectangle(radius=[18], pos=self.label.pos, size=self.label.size)
            Color(0.5, 0.4, 0.2, 0.7)
            self.label_border = RoundedRectangle(radius=[18], pos=self.label.pos, size=self.label.size, width=2)
        self.label.bind(pos=lambda inst, val: (setattr(self.label_rect, 'pos', val), setattr(self.label_border, 'pos', val)))
        self.label.bind(size=lambda inst, val: (setattr(self.label_rect, 'size', val), setattr(self.label_border, 'size', val)))
        self.label.opacity = 0
        self.add_widget(self.label)
        self.label.bind(size=self.label.setter('text_size'))
        self.button = Button(
            size_hint=(1, 1),
            color=(0, 0, 0, 1),
            background_normal="",
            background_color=(0, 0, 0, 0)
        )
        self.button.bind(on_press=self.on_button_press)
        self.add_widget(self.button)
        self.fbind('building', self.update_view)
        self.fbind('disabled', self.update_view)
        if building is not None:
            self.building = building
            self._bind_building()
        self.update_view()

    def on_button_press(self, instance):
        if self.disabled:
            return
        parent = self.parent
        building = Building.ensure_instance(self.building) if self.building else None
        if building:
            # Correction : autoriser le clic même en construction pour ouvrir le popup d'info
            while parent is not None and not hasattr(parent, "safe_show_building_popup"):
                parent = parent.parent
            if parent and hasattr(parent, "safe_show_building_popup"):
                parent.safe_show_building_popup(building, self.slot_index)
        else:
            while parent is not None and not hasattr(parent, "open_building_popup"):
                parent = parent.parent
            if parent and hasattr(parent, "open_building_popup"):
                parent.open_building_popup(self.slot_index, self.category)

    def _unbind_building(self):
        building = Building.ensure_instance(self.building) if self.building else None
        if building and hasattr(building, "unbind"):
            try:
                building.unbind(status=self.on_building_status)
            except Exception:
                pass

    def _bind_building(self):
        building = Building.ensure_instance(self.building) if self.building else None
        if building and hasattr(building, "bind"):
            building.bind(status=self.on_building_status)

    def on_building_status(self, instance, value):
        self.update_view()

    def update_view(self, *args):
        if self.timer_widget is not None:
            if self.timer_widget.parent is not None:
                self.timer_widget.parent.remove_widget(self.timer_widget)
            self.timer_widget = None

        self.is_under_construction = False
        building = Building.ensure_instance(self.building) if self.building else None

        self.bg_slot.opacity = 1
        self.bg_construction.opacity = 0
        self.bg_end.opacity = 0
        self.label.text = ""
        self.label.opacity = 0
        self.button.text = ""
        self.button.disabled = self.disabled

        if building:
            self._unbind_building()
            self._bind_building()
            if getattr(building, "status", None) == "En construction":
                self.bg_slot.opacity = 0
                self.bg_construction.opacity = 1
                self.bg_end.opacity = 0
                self.is_under_construction = True
                self.button.text = ""
                # Correction : laisser le bouton activé même en construction pour permettre l'accès au popup
                self.button.disabled = self.disabled
                initial_time = building.get_remaining_time()

                def on_timer_finished():
                    parent = self.parent
                    while parent is not None and not hasattr(parent, "sync_and_update_city"):
                        parent = parent.parent
                    if parent and hasattr(parent, "sync_and_update_city"):
                        parent.sync_and_update_city()

                self.timer_widget = TimerWidget(
                    initial_time=initial_time,
                    size_hint=(self.timer_banner_width_hint, None),
                    height=self.timer_height,
                    label_pos_hint=self.timer_label_pos_hint,
                    font_size=self.timer_font_size,
                    banner_width_hint=self.timer_banner_width_hint,
                    on_timer_finished=on_timer_finished
                )
                if self.canvas is not None:
                    self.add_widget(self.timer_widget)
                else:
                    Clock.schedule_once(lambda dt: self.add_widget(self.timer_widget), 0)
            else:
                self.bg_slot.opacity = 0
                self.bg_construction.opacity = 0
                # Affiche l'image du bâtiment construit
                image_path = None
                from data.buildings_database import buildings_database
                if building.name in buildings_database:
                    image_path = buildings_database[building.name].get("image")
                if image_path:
                    self.bg_end.source = image_path
                else:
                    self.bg_end.source = "assets/buildings/logo_construction_end.png"
                self.bg_end.opacity = 1
                display_level = building.get_display_level() if hasattr(building, "get_display_level") else building.get_level()
                self.label.text = f"{building.name} (Niveau {display_level})"
                self.label.opacity = 1
                self.button.text = ""
                self.button.disabled = self.disabled
        else:
            self.bg_slot.opacity = 1
            self.bg_construction.opacity = 0
            self.bg_end.opacity = 0
            self.label.text = ""
            self.label.opacity = 0
            self.button.text = f"Slot {self.slot_index + 1} (Vide)"
            self.button.disabled = self.disabled

    def on_building(self, instance, value):
        self.update_view()