import json
import logging
import copy
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, DictProperty, BooleanProperty, StringProperty

from models.city import City
from models.player import Player
from managers.resource_manager import ResourceManager
from managers.player_manager import PlayerManager
from managers.population_manager import PopulationManager
from managers.notification_manager import NotificationManager
from managers.research_manager import ResearchManager
from managers.city_manager import CityManager
from managers.save_load_manager import SaveLoadManager
from managers.transport_manager import TransportManager
from models.building import Building
from data.resources_database import RESOURCES

class GameData(EventDispatcher):
    """
    Contient toutes les données du jeu et délègue la gestion des villes à CityManager et des joueurs à PlayerManager.
    La possession des villes par joueur est gérée exclusivement via CityManager.get_cities_for_player.
    La gestion de la ville active est centralisée dans CityManager, GameData ne fait que déléguer.
    Toute désérialisation de ville/bâtiment passe par les méthodes from_dict appropriées (jamais de dict brut).
    """
    score = NumericProperty(0)
    position_x = NumericProperty(0)
    position_y = NumericProperty(0)
    islands = ListProperty([])
    resource_manager = ObjectProperty(None)
    player_manager = ObjectProperty(None)
    unlocked_buildings = ListProperty([])
    unlocked_research = ListProperty([])
    production_bonus = DictProperty({})
    city_selected = BooleanProperty(False)
    active_timers = DictProperty({})
    current_player_id = StringProperty(None, allownone=True)
    current_player_username = StringProperty(None, allownone=True)
    current_player_password = StringProperty(None, allownone=True)
    population_manager = ObjectProperty(None)
    header_bar = ObjectProperty(None)
    notification_manager = ObjectProperty(None)
    research_manager = ObjectProperty(None)
    city_manager = ObjectProperty(None)
    save_load_manager = ObjectProperty(None)
    transport_manager = ObjectProperty(None)

    def __init__(self, islands_json_path="data/islands.json", city_json_path="data/city.json", **kwargs):
        super().__init__(**kwargs)
        self.score = 0
        self.position_x = 0
        self.position_y = 0
        self.islands = []
        self.resource_manager = ResourceManager(self)
        self.player_manager = PlayerManager(self)
        self.unlocked_buildings = []
        self.unlocked_research = []
        self.resources = list(RESOURCES.keys())
        self.production_bonus = {resource: 0 for resource in self.resources}
        self.city_selected = False
        self.active_timers = {}
        self.current_player_id = None
        self.current_player_username = None
        self.current_player_password = None
        self.population_manager = PopulationManager(self)
        self.header_bar = None
        self.notification_manager = NotificationManager()
        self.research_manager = ResearchManager(self)
        self.city_manager = CityManager(self)
        self.save_load_manager = SaveLoadManager(self)
        self.transport_manager = TransportManager(self)

        self.islands_json_path = islands_json_path
        self.city_json_path = city_json_path
        self.load_islands_from_json(islands_json_path)
        self.city_layouts = self.load_city_layouts_from_json(city_json_path)

        self.player_manager.load_players_table()
        self.city_manager.build_city_index(self.islands, self.player_manager.players)

        # Synchronisation unique des instances de villes via CityManager (déjà fait dans from_dict et build_city_index)
        pass

    def set_header_bar(self, header_bar):
        self.header_bar = header_bar

    def load_islands_from_json(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                islands_data = json.load(f)
            islands_list = []
            for island_dict in islands_data:
                elements = []
                for elem in island_dict.get("elements", []):
                    if elem.get("type") == "city":
                        coords = elem.get("city_coords", elem.get("coords"))
                        if coords is None:
                            continue
                        owner = elem.get("owner") if elem.get("owner") is not None else ''
                        
                        # Crée un dictionnaire temporaire pour utiliser le système de cache
                        city_dict = {
                            "name": elem.get("name"),
                            "owner": owner,
                            "coords": coords,
                            "city_coords": coords,
                            "island_coords": island_dict.get("coords"),
                            "type": "player" if elem.get("controlable", True) else "ai",
                            "base_resource": island_dict.get("base_resource"),
                            "controlable": elem.get("controlable", True),
                            "id": elem.get("id")
                        }
                        
                        # Utilise le système de cache du city_manager
                        city = self.city_manager.get_or_create_city_from_dict(city_dict, self, coords=tuple(coords))
                        elements.append(city)
                    else:
                        # On ajoute l'élément tel quel (site de production, forum, etc.)
                        elements.append(elem)
                
                # Traitement des sites de ressources : les convertir en éléments
                resource_sites = island_dict.get("resource_sites", {})
                island_name = island_dict.get("name")
                
                # Charger les positions des boutons pour cette île
                try:
                    with open("data/island_button_positions.json", encoding="utf-8") as f:
                        button_positions = json.load(f)
                    island_positions = button_positions.get(island_name, {})
                except Exception as e:
                    logging.warning(f"Impossible de charger les positions des boutons : {e}")
                    island_positions = {}
                
                for site_name, site_data in resource_sites.items():
                    # Obtenir les coordonnées depuis le fichier de positions
                    coords = island_positions.get(site_name, [0, 0])
                    
                    # Créer un élément pour chaque site de ressource
                    site_element = {
                        "type": site_name,
                        "name": site_name,
                        "level": site_data.get("level", 1),
                        "donations": site_data.get("donations", 0),
                        "city_coords": coords
                    }
                    elements.append(site_element)
                    print(f"[DEBUG TEMP] Ajout site {site_name} -> coords {coords}")
                
                island = {
                    "name": island_dict.get("name"),
                    "coords": tuple(island_dict.get("coords")),
                    "background": island_dict.get("background"),
                    "base_resource": island_dict.get("base_resource"),
                    "advanced_resource": island_dict.get("advanced_resource"),
                    "elements": elements,
                    "city_layout": island_dict.get("city_layout")
                }
                islands_list.append(island)
            # Synchronisation unique des instances de villes via CityManager (déjà fait dans from_dict et build_city_index)
            pass
            self.islands = islands_list
        except Exception as e:
            logging.error(f"Erreur lors du chargement des îles : {e}")
            self.islands = []

    def unlock_building(self, building_name: str):
        if building_name not in self.unlocked_buildings:
            self.unlocked_buildings.append(building_name)

    def set_active_city(self, city_data):
        city_id = city_data.get("id", None) if isinstance(city_data, dict) else getattr(city_data, "id", None)
        city = self.city_manager.get_city_by_id(city_id)
        if city and city.owner == self.current_player_id:
            self.city_manager.set_active_city(city)

    def get_active_city(self):
        return self.city_manager.get_active_city()

    def get_current_player(self) -> Player:
        if self.current_player_id and self.current_player_id not in self.player_manager.players:
            username = getattr(self, "current_player_username", "???")
            password = getattr(self, "current_player_password", "???")
            self.player_manager.players[self.current_player_id] = Player(self.current_player_id, username, password)
        return self.player_manager.get_player(self.current_player_id) if self.current_player_id else None

    def get_island_by_coords(self, coords):
        for island in self.islands:
            if island["coords"] == coords:
                return island
        return None

    def to_dict(self) -> dict:
        active_city = self.get_active_city()
        return {
            "score": self.score,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "islands": [
                {
                    "name": island_data["name"],
                    "coords": island_data["coords"],
                    "background": island_data.get("background"),
                    "base_resource": island_data.get("base_resource"),
                    "advanced_resource": island_data.get("advanced_resource"),
                    "elements": [
                        elem.to_dict() if isinstance(elem, City)
                        else {k: v for k, v in elem.items() if k not in ("coords", "city_coords")}
                        for elem in island_data["elements"]
                    ],
                    "city_layout": island_data.get("city_layout")  # <-- AJOUT ICI
                }
                for island_data in self.islands
            ],
            "players": self.player_manager.to_dict(),
            "active_city": active_city.id if active_city else None,
            "transports": self.transport_manager.to_dict(),
        }

    def from_dict(self, data: dict):
        """
        Désérialise tout l'état du jeu depuis un dictionnaire.
        Toute désérialisation de ville passe par City.from_dict, tout building par Building.ensure_instance.
        """
        self.score = data.get("score", 0)
        self.position_x = data.get("position_x", 0)
        self.position_y = data.get("position_y", 0)
        islands_list = []
        cities_data = []

        # Charger la config statique pour retrouver les positions des villes
        with open("data/islands.json", encoding="utf-8") as f:
            static_islands = json.load(f)
        city_positions = {}
        for island in static_islands:
            iname = island.get("name")
            for elem in island.get("elements", []):
                if elem.get("type") == "city":
                    cname = elem.get("name")
                    coords = elem.get("city_coords", elem.get("coords", (0, 0)))
                    city_positions[(iname, cname)] = coords

        # Désérialisation des îles et villes
        for island_data in data.get("islands", []):
            elements = []
            iname = island_data["name"]
            for elem in island_data.get("elements", []):
                if isinstance(elem, dict) and elem.get("type") == "city":
                    owner = elem.get("owner") if elem.get("owner") is not None else ''
                    city_dict = {**elem, "owner": owner}
                    cname = elem.get("name")
                    coords = city_positions.get((iname, cname), (0, 0))
                    # Utilise le cache du CityManager pour garantir l’unicité
                    city = self.city_manager.get_or_create_city_from_dict(elem, self, coords=coords)
                    elements.append(city)
                    cities_data.append(city_dict)
                else:
                    typ = elem.get("type")
                    coords = None
                    static_island = next((e for e in static_islands if e.get("name") == iname), None)
                    if static_island:
                        for static_elem in static_island.get("elements", []):
                            if static_elem.get("type") == typ:
                                coords = static_elem.get("city_coords") or static_elem.get("coords")
                                break
                    if coords is not None:
                        elem = dict(elem)
                        elem["city_coords"] = list(coords)
                    if "name" not in elem and "type" in elem:
                        elem = dict(elem)
                        elem["name"] = elem["type"]
                    elements.append(elem)
            island = {
                "name": island_data["name"],
                "coords": tuple(island_data["coords"]),
                "background": island_data.get("background"),
                "base_resource": island_data.get("base_resource"),
                "advanced_resource": island_data.get("advanced_resource"),
                "elements": elements,
                "city_layout": island_data.get("city_layout")
            }
            islands_list.append(island)
        self.islands = islands_list

        # Synchronisation unique des villes et des références via CityManager
        self.city_manager.from_dict(cities_data, self)
        # Synchronisation des bâtiments et des transports (une seule fois)
        city_by_id = {city.id: city for city in self.city_manager._cities}
        for city in self.city_manager._cities:
            for b in city.buildings:
                if isinstance(b, Building):
                    b.city = city
        for t in getattr(self.transport_manager, "transports", []):
            if hasattr(t, "ville_source") and getattr(t.ville_source, "id", None) in city_by_id:
                t.ville_source = city_by_id[t.ville_source.id]
            if hasattr(t, "ville_dest") and getattr(t.ville_dest, "id", None) in city_by_id:
                t.ville_dest = city_by_id[t.ville_dest.id]
        # Correction finale des city_coords manquants (une seule fois)
        for island in self.islands:
            for elem in island["elements"]:
                if isinstance(elem, City):
                    iname = island["name"]
                    cname = getattr(elem, "name", None)
                    coords = city_positions.get((iname, cname))
                    if coords is not None:
                        elem.city_coords = list(coords)

        # Désérialisation des joueurs et de la ville active
        self.player_manager.from_dict(data.get("players", {}), self)
        ac_id = data.get("active_city")
        self.city_manager.set_active_city(self.city_manager.get_city_by_id(ac_id) if ac_id else None)
        self.transport_manager.from_dict(data.get("transports", []), self)

    def load_city_layouts_from_json(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erreur lors du chargement des layouts de ville : {e}")
            return {}