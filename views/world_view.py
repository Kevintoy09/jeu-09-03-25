from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color, Ellipse
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
import math
import logging

logging.basicConfig(level=logging.DEBUG)

from kivy.uix.scatter import Scatter

class BoundedScatter(Scatter):
    """
    Scatter qui bloque le drag pour empêcher de sortir de l'image.
    """
    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        if self.parent and hasattr(self.parent, '_clamp_scatter'):
            self.parent._clamp_scatter()
        return True

class WorldView(RelativeLayout):
    def __init__(self, manager, game_data, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.game_data = game_data

        self.hex_size = 30

        # Taille de l'image de fond
        self.map_width = 2000
        self.map_height = 2000

        title = Label(text="Carte du Monde", size_hint=(1, None), height=50, pos_hint={"top": 1})
        self.add_widget(title)

        self.map_scatter = BoundedScatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale=1.0,
            size_hint=(None, None),
            size=(self.map_width, self.map_height),
            pos=(0, 0),
            auto_bring_to_front=False
        )
        self.add_widget(self.map_scatter)

        self.map_layout = FloatLayout(size=(self.map_width, self.map_height), size_hint=(None, None))
        self.map_scatter.add_widget(self.map_layout)

        with self.map_layout.canvas.before:
            self.background = Rectangle(source="assets/world/world_view.png", size=(self.map_width, self.map_height), pos=(0, 0))

        self.island_coords_map = {}
        self.island_buttons = {}

        self.update_island_coords_map()
        self.draw_island_buttons()
        self.refresh_island_markers()

        Window.bind(on_mouse_down=self._on_mouse_down)

        self._has_centered = False
        self.bind(size=self._center_on_first_size)

    def _clamp_scatter(self):
        scatter = self.map_scatter
        scale = scatter.scale
        win_w, win_h = Window.width, Window.height
        map_w, map_h = self.map_width * scale, self.map_height * scale

        min_scale = max(win_w / self.map_width, win_h / self.map_height, 0.1)
        max_scale = 3.0
        if scale < min_scale:
            scatter.scale = min_scale
            scale = min_scale
            map_w, map_h = self.map_width * scale, self.map_height * scale
        elif scale > max_scale:
            scatter.scale = max_scale
            scale = max_scale
            map_w, map_h = self.map_width * scale, self.map_height * scale

        min_x = min(0, win_w - map_w)
        max_x = 0
        min_y = min(0, win_h - map_h)
        max_y = 0

        if map_w <= win_w:
            scatter.x = (win_w - map_w) / 2
        else:
            scatter.x = min(max(scatter.x, min_x), max_x)

        if map_h <= win_h:
            scatter.y = (win_h - map_h) / 2
        else:
            scatter.y = min(max(scatter.y, min_y), max_y)

    def update_island_coords_map(self):
        self.island_coords_map.clear()
        for island in self.game_data.islands:
            coords = tuple(island["coords"])
            self.island_coords_map[coords] = island["name"]

    def _hex_to_pos(self, coords):
        # Si tu veux garder la logique hexagonale pour le modèle, tu peux la garder ici
        x, y = coords
        pos_x = x * self.hex_size * 1.5
        pos_y = y * self.hex_size * math.sqrt(3) / 2
        return pos_x, pos_y

    def draw_island_buttons(self):
        # Supprime tous les anciens boutons du layout
        for btn in self.island_buttons.values():
            self.map_layout.remove_widget(btn)
        self.island_buttons.clear()

        for coords, name in self.island_coords_map.items():
            btn_center = self._hex_to_pos(coords)
            btn_width = self.hex_size * 1.5
            btn_height = self.hex_size * math.sqrt(3)
            btn_pos = (
                btn_center[0] - btn_width / 2,
                btn_center[1] - btn_height / 2
            )
            btn = Button(
                text=name,
                size_hint=(None, None),
                size=(btn_width, btn_height),
                pos=btn_pos,
                background_color=(1, 1, 1, 1),
                disabled_color=(0.6, 0.6, 0.6, 1),
                opacity=1.0
            )
            btn.bind(on_press=lambda instance, c=coords[0], r=coords[1]: self.on_hex_click(c, r))
            self.map_layout.add_widget(btn)
            self.island_buttons[coords] = btn

    def on_hex_click(self, col, row):
        coords = (col, row)
        is_island = coords in self.island_coords_map
        if is_island:
            logging.info(f"Île sélectionnée: {self.island_coords_map[coords]} ({coords})")
            island = next((isl for isl in self.game_data.islands if tuple(isl["coords"]) == coords), None)
            if island:
                self.manager.switch_view("island_view", data=island)
        else:
            logging.info(f"Case mer sélectionnée: {coords}")

    def add_island_markers(self):
        current_player_id = self.game_data.current_player_id
        logging.debug("DEBUG: current_player_id = %s", current_player_id)
        owned_coords = set()
        city_manager = self.game_data.city_manager

        for player in self.game_data.player_manager.players.values():
            if getattr(player, "id_player", None) == current_player_id or getattr(player, "username", None) == current_player_id:
                player_cities = city_manager.get_cities_for_player(player.id_player)
                for city in player_cities:
                    island_coords = getattr(city, "island_coords", None)
                    if island_coords:
                        owned_coords.add(tuple(island_coords))
                logging.debug(f"Villes trouvées pour le joueur courant : {[getattr(city, 'coords', None) for city in player_cities]}")
                break

        logging.debug(f"Coordonnées des villes possédées : {owned_coords}")

        for coords, btn in self.island_buttons.items():
            if coords in owned_coords:
                self.add_marker(btn)

    def refresh_island_markers(self):
        instructions_to_remove = [instr for instr in self.map_layout.canvas.after.children if isinstance(instr, Ellipse)]
        for instr in instructions_to_remove:
            self.map_layout.canvas.after.remove(instr)
        self.add_island_markers()

    def add_marker(self, button):
        with self.map_layout.canvas.after:
            Color(1, 0, 0, 1)  # Rouge
            marker_size = 20
            marker_x = button.x + (button.width - marker_size) / 2
            marker_y = button.y + (button.height - marker_size) / 2
            Ellipse(pos=(marker_x, marker_y), size=(marker_size, marker_size))
            logging.debug(f"Added marker at position ({marker_x}, {marker_y}) for button {button.text}")

    def _on_mouse_down(self, window, x, y, button, _):
        min_scale = max(
            Window.width / self.map_width,
            Window.height / self.map_height,
            0.1
        )
        max_scale = 3.0
        old_scale = self.map_scatter.scale
        if button == 'scrolldown':
            new_scale = max(min_scale, old_scale * 0.9)
            self.map_scatter.scale = new_scale
        elif button == 'scrollup':
            new_scale = min(max_scale, old_scale * 1.1)
            self.map_scatter.scale = new_scale

    def on_touch_up(self, touch):
        super().on_touch_up(touch)

    def _center_scatter_on_coords(self, coords):
        """
        Centre le scatter sur les coordonnées hexagonales données.
        """
        pos_x, pos_y = self._hex_to_pos(coords)
        win = self.get_parent_window()
        if not win:
            return
        win_cx, win_cy = win.width / 2, win.height / 2
        scale = self.map_scatter.scale
        scatter_x = win_cx - pos_x * scale
        scatter_y = win_cy - pos_y * scale
        self.map_scatter.pos = (scatter_x, scatter_y)
        self._clamp_scatter()

    def _center_on_first_size(self, *_) :
        if not self._has_centered and self.width > 0 and self.height > 0:
            coords = self._get_first_owned_island_coords()
            if coords:
                self._center_scatter_on_coords(coords)
            self._has_centered = True

    def _get_first_owned_island_coords(self):
        """
        Retourne les coordonnées de la première île possédée par le joueur courant, ou None si aucune.
        """
        current_player_id = getattr(self.game_data, 'current_player_id', None)
        city_manager = getattr(self.game_data, 'city_manager', None)
        player_manager = getattr(self.game_data, 'player_manager', None)
        if not (current_player_id and city_manager and player_manager):
            return None
        for player in player_manager.players.values():
            if getattr(player, "id_player", None) == current_player_id or getattr(player, "username", None) == current_player_id:
                player_cities = city_manager.get_cities_for_player(player.id_player)
                for city in player_cities:
                    island_coords = getattr(city, "island_coords", None)
                    if island_coords:
                        return tuple(island_coords)
        return None

    def update_world(self, data=None):
        """
        Méthode à appeler lors du changement de vue monde.
        Si data contient 'center_coords', centre la carte sur ces coordonnées.
        """
        if data and isinstance(data, dict) and "center_coords" in data:
            coords = tuple(data["center_coords"])
            self._center_scatter_on_coords(coords)