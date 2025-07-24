from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.clock import Clock
import os

from views.city_popup import CityPopup

RESOURCE_LABELS = {
    "quarry": "Quarry",
    "iron_mine": "Iron Mine",
    "papyrus_pond": "Papyrus_pond",
    "horse_ranch": "Horse Ranch",
    "grain_field": "Grain_field",
    "marble_mine": "Marble Mine",
    "glassworks": "Glassworks",
    "pasture": "Pasture",
    "coal_mine": "Coal Mine",
    "gunpowder_lab": "Gunpowder Lab",
    "spice_garden": "Spice Garden",
    "cotton_field": "Cotton Field",
    "forest": "Forest"
}

RESOURCE_TYPE_MAP = {
    "forest": "wood",
    "quarry": "stone",
    "iron_mine": "iron",
    "papyrus_pond": "papyrus",
    "grain_field": "cereal",
    "horse_ranch": "horse",
    "marble_mine": "marble",
    "glassworks": "glass",
    "pasture": "meat",
    "coal_mine": "coal",
    "gunpowder_lab": "gunpowder",
    "spice_garden": "spices",
    "cotton_field": "cotton"
}

class BoundedScatter(Scatter):
    """
    Scatter qui bloque le drag pour empêcher de sortir de l'image.
    """
    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        self.parent._clamp_scatter()
        return True

class IslandView(RelativeLayout):
    """
    Vue principale d'une île, gère l'affichage du fond, des boutons villes/ressources,
    le drag/zoom, et la navigation.
    """
    def __init__(self, manager, game_data, network_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.game_data = game_data
        self.network_manager = network_manager
        self.city_popup = None
        self.selected_city = None
        self.popup = None
        self.island = None
        self.elements = []
        self.city_buttons = {}

        self.scatter = BoundedScatter(do_rotation=False, do_translation=True, do_scale=True, size_hint=(None, None))
        self.add_widget(self.scatter)
        self.background_image = Image(allow_stretch=True, keep_ratio=False)
        self.scatter.add_widget(self.background_image)

        self.title_label = Label(text="Island View", size_hint=(1, None), height=50, pos_hint={"top": 1})
        self.add_widget(self.title_label)
        self.back_button = Button(text="Back", size_hint=(0.2, 0.1), pos_hint={"x": 0, "y": 0.9})
        self.back_button.bind(on_press=self.back_to_island_selection)
        self.add_widget(self.back_button)

        self._scatter_initialized = False  # Flag pour le centrage initial

    def update_island(self, island):
        """
        Charge une nouvelle île et met à jour l'affichage.
        """
        self.island = island
        self.elements = island.get("elements", [])
        
        self.clear_widgets()
        self.add_widget(self.scatter)
        self.add_widget(self.title_label)
        self.add_widget(self.back_button)
        bg = island.get("background")
        if not bg or not isinstance(bg, str) or not bg.strip():
            bg = "assets/island/default_island.png"
        if not os.path.isfile(bg):
            bg = "assets/island/default_island.png"
        self.background_image.source = bg

        self._update_layout()
        # Centrage/zoom initial une seule fois ici
        Clock.schedule_once(self._center_and_zoom, 0)
        self.place_elements()

    def _center_and_zoom(self, *args):
        """
        Centre et ajuste le zoom du scatter pour que l'île remplisse la vue.
        """
        iw, ih = self.background_image.size
        sw, sh = self.size
        if iw == 0 or ih == 0 or sw == 0 or sh == 0:
            return
        min_scale = max(sw / iw, sh / ih)
        self.scatter.scale = min_scale
        self.scatter.scale_min = min_scale
        self.scatter.scale_max = 2.0
        self.scatter.pos = ((sw - iw * self.scatter.scale) / 2, (sh - ih * self.scatter.scale) / 2)
        self._scatter_initialized = True
        self._clamp_scatter()

    def on_size(self, *_):
        """
        Réagit au redimensionnement de la vue.
        """
        if self.island and self.elements:
            self.place_elements()
        # Ne pas rappeler self._center_and_zoom ici !

    def place_elements(self):
        """
        Place les éléments (villes, ressources, etc.) sur l'île selon les données.
        Unifie la gestion dict/objet, factorise la création des boutons, et gère les erreurs.
        """
        # Nettoyer tous les widgets de self.scatter sauf le background_image
        widgets_to_keep = {self.background_image}
        for child in list(self.scatter.children):
            if child not in widgets_to_keep:
                self.scatter.remove_widget(child)
        self.city_buttons = {}

        def extract_info(elem):
            """Retourne (typ, name, owner, coords, level) pour dict ou objet."""
            if isinstance(elem, dict):
                typ = elem.get("type")
                name = elem.get("name", "City")
                owner = elem.get("owner")
                coords = elem.get("city_coords")
                level = elem.get("level", 1)
            else:
                typ = "city"
                name = getattr(elem, "name", "City")
                owner = getattr(elem, "owner", None)
                coords = getattr(elem, "city_coords", None)
                level = getattr(elem, "level", 1)
            return typ, name, owner, coords, level

        def make_city_button(name, owner, coords, elem):
            """Crée et place un bouton ville."""
            x, y = coords
            size = (140, 50)
            city_text = f"{name}"
            if owner == self.game_data.current_player_id:
                city_text += " [YOU]"
                background_color = (1, 0.93, 0.5, 1)
            elif owner:
                background_color = (0.8, 0.8, 0.8, 1)
            else:
                background_color = (1, 1, 1, 0.7)
            btn = Button(
                text=city_text,
                size_hint=(None, None),
                size=size,
                pos=(x, y),
                background_color=background_color,
                color=(0, 0, 0, 1),
                font_size='16sp',
                bold=True
            )
            btn.bind(on_press=lambda instance, city=elem: self.confirm_city_selection(city))
            self.scatter.add_widget(btn)
            key = f"{self.island['name']}_{name}_{int(x)}_{int(y)}"
            self.city_buttons[key] = btn

        def make_resource_button(typ, level, coords):
            """Crée et place un bouton ressource."""
            x, y = coords
            label = f"{RESOURCE_LABELS[typ]} ({level})"
            size = (120, 40)
            btn = Button(
                text=label,
                size_hint=(None, None),
                size=size,
                pos=(x, y)
            )
            btn.bind(on_press=lambda instance, site_type=RESOURCE_TYPE_MAP[typ]: self.open_resource_view(site_type))
            self.scatter.add_widget(btn)

        def make_simple_button(label, coords):
            """Crée et place un bouton simple (village, forum, etc.)."""
            x, y = coords
            size = (120, 40)
            btn = Button(
                text=label,
                size_hint=(None, None),
                size=size,
                pos=(x, y)
            )
            self.scatter.add_widget(btn)

        # Mapping type → fonction de création
        type_map = {
            "city": make_city_button,
            "wild_village": lambda n, o, c, e: make_simple_button("Wild Village", c),
            "forum": lambda n, o, c, e: make_simple_button("Forum", c),
        }

        for elem in self.elements:
            typ, name, owner, coords, level = extract_info(elem)
            if not (isinstance(coords, (list, tuple)) and len(coords) == 2):
                continue
            if typ == "city":
                type_map["city"](name, owner, coords, elem)
            elif typ in RESOURCE_LABELS:
                make_resource_button(typ, level, coords)
            elif typ in type_map:
                type_map[typ](name, owner, coords, elem)
            # On ne log plus les types inconnus pour alléger la sortie
        print("---- DEBUG elements ----")
        for e in self.elements:
            print(e)
        print("---- FIN DEBUG ----")

    def open_resource_view(self, site_type):
        """
        Ouvre la vue de gestion de ressource pour la ville du joueur courant.
        """
        current_player_id = self.game_data.current_player_id
        selected_city = None
        for elem in self.elements:
            if isinstance(elem, dict):
                if elem.get("type") == "city" and elem.get("owner") == current_player_id:
                    selected_city = elem
                    break
            else:
                if hasattr(elem, "name") and hasattr(elem, "owner"):
                    if getattr(elem, "owner", None) == current_player_id:
                        selected_city = elem
                        break
        if not selected_city:
            self.show_error_popup("You must own a city on the island to manage its resources.")
            return
        self.manager.switch_view(
            "resource_view",
            site_type=site_type,
            city_data=selected_city,
            island_coords=self.island["coords"]
        )

    def confirm_city_selection(self, city):
        """
        Ouvre la popup de gestion de la ville sélectionnée.
        """
        self.city_popup = CityPopup(self.game_data, self.manager, network_manager=self.network_manager)
        self.city_popup.open_city_popup(city)

    def back_to_island_selection(self, instance):
        """
        Retour à la sélection d'île.
        """
        self.manager.switch_view("island_selection_screen")

    def show_error_popup(self, message):
        """
        Affiche une popup d'erreur.
        """
        popup = Popup(title='Error', size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical')
        msg_label = Label(text=message)
        content.add_widget(msg_label)
        close_button = Button(text='Close', size_hint_y=None, height='40dp')
        close_button.bind(on_press=popup.dismiss)
        content.add_widget(close_button)
        popup.content = content
        popup.open()

    def show_info_popup(self, message):
        """
        Affiche une popup d'information.
        """
        popup = Popup(title='Info', size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical')
        msg_label = Label(text=message)
        content.add_widget(msg_label)
        close_button = Button(text='OK', size_hint_y=None, height='40dp')
        close_button.bind(on_press=popup.dismiss)
        content.add_widget(close_button)
        popup.content = content
        popup.open()

    def _update_layout(self, *args):
        """
        Met à jour la taille et la position du fond et du scatter.
        """
        w = self.width if self.width > 0 else 1
        h = self.height if self.height > 0 else 1
        self.background_image.size = self.background_image.texture_size
        self.background_image.pos = (0, 0)
        self.scatter.size = self.background_image.size
        print(f"[DEBUG] background_image.size={self.background_image.size} scatter.size={self.scatter.size}")
        self._clamp_scatter()

    def _clamp_scatter(self, *args):
        """
        Empêche le scatter de sortir du cadre visible.
        """
        sw, sh = self.size
        iw, ih = self.background_image.size
        scale = self.scatter.scale
        min_x = min(0, sw - iw * scale)
        max_x = 0
        min_y = min(0, sh - ih * scale)
        max_y = 0
        x, y = self.scatter.pos
        nx = min(max(x, min_x), max_x)
        ny = min(max(y, min_y), max_y)
        if (nx, ny) != (x, y):
            self.scatter.pos = (nx, ny)
        if iw and ih and sw and sh:
            min_scale = max(sw / iw, sh / ih)
            if self.scatter.scale < min_scale:
                self.scatter.scale = min_scale
            if self.scatter.scale > 2.0:
                self.scatter.scale = 2.0