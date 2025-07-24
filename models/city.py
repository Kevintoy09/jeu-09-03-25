import copy
import logging
logging.basicConfig(level=logging.INFO)
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty, ObjectProperty, ListProperty, DictProperty, BooleanProperty
)
from data.buildings_database import buildings_database
from data.resources_database import RESOURCES
from models.constants import DEFAULT_RESOURCES, DEFAULT_STORAGE_CAPACITY
from models.building import Building

def safe_int(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0

class City(EventDispatcher):
    """
    Représente une ville dans le jeu.
    Gère les bâtiments, la production, la désérialisation/sérialisation, et les accès aux ressources.
    La logique métier (bonus, productivité, etc.) est externalisée.
    Toute conversion dict→Building passe par Building.ensure_instance(building, city=self).
    """

    name = StringProperty()
    owner = StringProperty('', allownone=True)
    coords = ObjectProperty()
    city_coords = ObjectProperty()
    island_coords = ObjectProperty(allownone=True)
    x = NumericProperty(0)
    y = NumericProperty(0)
    city_type = StringProperty("player")
    base_resource = StringProperty("")
    resources = DictProperty({})
    storage_capacity = DictProperty({})
    buildings = ListProperty([])
    categories = ListProperty([])
    research_points_per_tick = NumericProperty(0)
    unlocked_buildings = ListProperty([])
    game_data = ObjectProperty(allownone=True)
    workers_assigned = DictProperty({})
    controlable = BooleanProperty(True)
    id = StringProperty()
    satisfaction = NumericProperty(100)  # Valeur initiale à 100 (satisfait)
    satisfaction_factors = DictProperty()
    windmill_cereal_multiplier = NumericProperty(1)  # Multiplicateur de consommation de céréales via le moulin

    def __init__(
        self,
        name: str,
        owner: str,
        coords: tuple,
        island_coords: tuple = None,
        city_type: str = "player",
        base_resource: str = "",
        game_data=None,
        controlable=True,
        id: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.owner = owner if owner is not None else ''
        self.coords = tuple(coords)
        self.city_coords = list(coords)
        self.island_coords = island_coords
        self.x = coords[0]
        self.y = coords[1]
        self.city_type = city_type
        self.base_resource = base_resource
        self.resources = copy.deepcopy(DEFAULT_RESOURCES)
        self.storage_capacity = copy.deepcopy(DEFAULT_STORAGE_CAPACITY)
        self.buildings = []
        self.categories = ["defensive"] * 2 + ["marine"] * 2 + ["general"] * 6
        self.research_points_per_tick = 0
        self.unlocked_buildings = []
        self.game_data = game_data
        self.workers_assigned = {k: 0 for k in RESOURCES.keys()}
        self.controlable = controlable
        self.id = id if id is not None else f"{self.name}|{self.island_coords}|{self.owner}"
        self.satisfaction = 100
        self.satisfaction_factors = {"bonus": {}, "malus": {}}
        self.has_plague = False

    # --- Accès bâtiments ---
    def get_building_by_index(self, idx) -> Building:
        if 0 <= idx < len(self.buildings):
            return Building.ensure_instance(self.buildings[idx], city=self)
        return None

    def set_building_by_index(self, idx, building):
        while len(self.buildings) <= idx:
            self.buildings.append(None)
        self.buildings[idx] = Building.ensure_instance(building, city=self)

    def get_building_by_name(self, building_name: str):
        for building in self.get_buildings():
            if building and building.get_name() == building_name:
                return building
        return None

    def add_building(self, building: Building, idx: int = None):
        if idx is not None and 0 <= idx < len(self.buildings):
            self.buildings[idx] = Building.ensure_instance(building, city=self)
        else:
            for i, b in enumerate(self.buildings):
                if b is None:
                    self.buildings[i] = Building.ensure_instance(building, city=self)
                    return
            self.buildings.append(Building.ensure_instance(building, city=self))

    def get_buildings(self):
        return [Building.ensure_instance(building, city=self) for building in self.buildings]

    @staticmethod
    def deserialize_buildings(buildings_data, city=None):
        return [Building.ensure_instance(b, city=city) for b in buildings_data]

    # --- Méthode utilitaire pour UI ---
    def get_display_level_for_slot(self, idx):
        b = self.get_building_by_index(idx)
        return b.get_display_level() if b else 0

    # --- Encapsulation ressources et workers ---
    def get_resources(self) -> dict:
        return self.resources

    def get_workers_assigned(self, resource_name: str) -> int:
        return safe_int(self.workers_assigned.get(resource_name, 0))

    def get_name(self) -> str:
        return self.name

    def get_owner(self) -> str:
        return self.owner

    def rename(self, new_name):
        self.name = new_name

    # --- Population ---
    def get_population_limit(self) -> int:
        if self.game_data and hasattr(self.game_data, "population_manager"):
            return self.game_data.population_manager.calculate_population_limit(self)
        return 0

    def get_building_level(self, building_name: str) -> int:
        b = self.get_building_by_name(building_name)
        return b.get_level() if b else 0

    def can_build(self, building_name: str, player_id=None) -> bool:
        building_data = buildings_database.get(building_name)
        if not building_data:
            return False
        if player_id is not None and self.owner != player_id:
            return False
        required_research = building_data.get("required_research")
        player = self.game_data.player_manager.get_player(player_id) if player_id is not None else None
        if required_research and (not player or required_research not in getattr(player, "unlocked_research", [])):
            return False
        return True

    # --- Désérialisation et serialization ---
    def to_dict(self) -> dict:
        buildings_list = [
            b.to_dict() if hasattr(b, "to_dict") else None for b in self.get_buildings()
        ]
        data = {
            "type": "city",
            "name": self.name,
            "owner": self.owner if self.owner is not None else '',
            "island_coords": self.island_coords,
            "city_type": self.city_type,
            "base_resource": self.base_resource,
            "resources": self.resources,
            "storage_capacity": self.storage_capacity,
            "buildings": buildings_list,
            "categories": self.categories,
            "research_points_per_tick": self.research_points_per_tick,
            "unlocked_buildings": self.unlocked_buildings,
            "workers_assigned": {k: safe_int(v) for k, v in self.workers_assigned.items()},
            "controlable": self.controlable,
            "id": self.id,
            "satisfaction": self.satisfaction,
            "satisfaction_factors": self.satisfaction_factors.copy(),
            "gold_rate": self.gold_rate,
            "windmill_cereal_multiplier": getattr(self, "windmill_cereal_multiplier", 1),
            "has_plague": self.has_plague
        }
        return data

    @classmethod
    def from_dict(cls, data, game_data, coords=None):
        if coords is None:
            coords = (0, 0)
        city = cls(
            name=data.get("name"),
            owner=data.get("owner"),
            coords=tuple(coords),
            island_coords=tuple(data.get("island_coords")) if data.get("island_coords") else None,
            city_type=data.get("type", "player"),
            base_resource=data.get("base_resource"),
            game_data=game_data,
            controlable=data.get("controlable", True),
            id=data.get("id")
        )
        city.city_coords = list(coords)
        saved_resources = data.get("resources", {})
        city.resources = copy.deepcopy(DEFAULT_RESOURCES)
        city.resources.update(saved_resources)
        city.storage_capacity = data.get("storage_capacity", copy.deepcopy(DEFAULT_STORAGE_CAPACITY))
        city.buildings = cls.deserialize_buildings(data.get("buildings", []), city=city)
        layout_key = None
        if city.game_data and hasattr(city.game_data, "get_city_layout_for_city"):
            layout_key = city.game_data.get_city_layout_for_city(city)
        elif city.island_coords and city.game_data and hasattr(city.game_data, "get_island_by_coords"):
            island = city.game_data.get_island_by_coords(city.island_coords)
            if island and "city_layout" in island:
                layout_key = island["city_layout"]
        layout = None
        if layout_key and city.game_data and hasattr(city.game_data, "city_layouts"):
            layout = city.game_data.city_layouts.get(layout_key)
        if layout and "slots" in layout:
            nb_slots = len(layout["slots"])
            while len(city.buildings) < nb_slots:
                city.buildings.append(None)
            if len(city.buildings) > nb_slots:
                city.buildings = city.buildings[:nb_slots]
        city.categories = data.get("categories", ["defensive"] * 2 + ["marine"] * 2 + ["general"] * 6)
        city.research_points_per_tick = data.get("research_points_per_tick", 0)
        city.unlocked_buildings = data.get("unlocked_buildings", [])
        city.workers_assigned = {k: safe_int(v) for k, v in data.get("workers_assigned", {}).items()}
        city.satisfaction_factors = data.get("satisfaction_factors", {"bonus": {}, "malus": {}})
        city.gold_rate = data.get("gold_rate", 1)
        city.windmill_cereal_multiplier = data.get("windmill_cereal_multiplier", 1)
        return city

    def from_dict_instance(self, data: dict):
        self.name = data.get("name", self.name)
        self.owner = data.get("owner") if data.get("owner") is not None else ''
        coords = data.get("city_coords", data.get("coords"))
        self.coords = tuple(coords) if coords is not None else (0, 0)
        self.island_coords = tuple(data.get("island_coords")) if data.get("island_coords") else None
        self.city_type = data.get("city_type", "player")
        self.base_resource = data.get("base_resource", "")
        saved_resources = data.get("resources", {})
        self.resources = copy.deepcopy(DEFAULT_RESOURCES)
        self.resources.update(saved_resources)
        self.storage_capacity = data.get("storage_capacity", copy.deepcopy(DEFAULT_STORAGE_CAPACITY))
        self.buildings = self.deserialize_buildings(data.get("buildings", []), city=self)
        layout_key = None
        if self.game_data and hasattr(self.game_data, "get_city_layout_for_city"):
            layout_key = self.game_data.get_city_layout_for_city(self)
        elif self.island_coords and self.game_data and hasattr(self.game_data, "get_island_by_coords"):
            island = self.game_data.get_island_by_coords(self.island_coords)
            if island and "city_layout" in island:
                layout_key = island["city_layout"]
        layout = None
        if layout_key and self.game_data and hasattr(self.game_data, "city_layouts"):
            layout = self.game_data.city_layouts.get(layout_key)
        if layout and "slots" in layout:
            nb_slots = len(layout["slots"])
            while len(self.buildings) < nb_slots:
                self.buildings.append(None)
            if len(self.buildings) > nb_slots:
                self.buildings = self.buildings[:nb_slots]
        self.categories = data.get("categories", ["defensive"] * 2 + ["marine"] * 2 + ["general"] * 6)
        self.research_points_per_tick = data.get("research_points_per_tick", 0)
        self.unlocked_buildings = data.get("unlocked_buildings", [])
        self.workers_assigned = {k: safe_int(v) for k, v in data.get("workers_assigned", {}).items()}
        self.satisfaction = data.get("satisfaction", 100)
        self.satisfaction_factors = data.get("satisfaction_factors", {"bonus": {}, "malus": {}})
        self.windmill_cereal_multiplier = data.get("windmill_cereal_multiplier", 1)
        self.has_plague = data.get("has_plague", False)
        self.gold_rate = data.get("gold_rate", getattr(self, "gold_rate", 1))


    def get_satisfaction(self):
        # On suppose que le manager a une méthode calculer_satisfaction(city)
        if self.game_data and hasattr(self.game_data, "population_manager"):
            return self.game_data.population_manager.calculer_satisfaction(self)
        # Valeur de secours si le manager n’est pas disponible
        return self.satisfaction