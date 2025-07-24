from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty, ListProperty
from models.constants import STARTING_DIAMONDS  # Ajoute cet import en haut du fichier

class Player(EventDispatcher):
    """
    Représente un joueur du jeu, ses recherches, points et progression.
    L'accès aux villes possédées se fait via CityManager.get_cities_for_player(player.id_player)
    """
    id_player = StringProperty()
    username = StringProperty()
    password = StringProperty()
    unlocked_research = ListProperty([])
    points = NumericProperty(0)
    military_points = NumericProperty(0)
    ships = NumericProperty(1)
    ships_available = NumericProperty(1)
    research_points = NumericProperty(0)
    diamonds = NumericProperty(0)  # Ajout des diamants

    def __init__(self, id_player: str, username: str, password: str, **kwargs):
        super().__init__(**kwargs)
        self.id_player = id_player
        self.username = username
        self.password = password
        self.unlocked_research = []
        self.points = 0
        self.military_points = 0
        self.ships = 1
        self.ships_available = 1
        self.research_points = 0  # Points de recherche globaux du joueur
        self.diamonds = STARTING_DIAMONDS  # Attribue 100 diamants au départ

    def to_dict(self) -> dict:
        """
        Convertit les données du joueur en dictionnaire pour la sauvegarde.
        La liste des IDs de villes est obtenue via CityManager au besoin.
        """
        return {
            "id_player": self.id_player,
            "username": self.username,
            "password": self.password,
            "unlocked_research": self.unlocked_research,
            "points": self.points,
            "military_points": self.military_points,
            "ships": self.ships,
            "ships_available": self.ships_available,
            "research_points": self.research_points,
            "diamonds": self.diamonds,  # Ajout des diamants
        }

    @classmethod
    def from_dict(cls, data: dict, game_data):
        """Crée une instance de Player à partir d'un dictionnaire."""
        if not isinstance(data, dict):
            raise TypeError("Expected a dictionary for player data")
        
        id_player = data.get("id_player")
        username = data.get("username")
        password = data.get("password")
        player = cls(id_player, username, password)
        
        player.unlocked_research = data.get("unlocked_research", [])
        player.points = data.get("points", 0)
        player.military_points = data.get("military_points", 0)
        player.ships = data.get("ships", 1)
        player.ships_available = data.get("ships_available", player.ships)
        player.research_points = data.get("research_points", 0)
        player.diamonds = data.get("diamonds", STARTING_DIAMONDS)
        return player

    def get_points(self) -> int:
        """Retourne le nombre de points du joueur."""
        return self.points

    def get_military_points(self) -> int:
        """Retourne le nombre de points militaires du joueur."""
        return self.military_points

    def has_city(self, city_manager) -> bool:
        """
        Vérifie si le joueur possède au moins une ville.
        city_manager : instance de CityManager
        """
        return len(city_manager.get_cities_for_player(self.id_player)) > 0

    def apply_research_effects_to_cities(self, research_effects: dict, city_manager):
        """Applique les effets de recherche à toutes les villes du joueur."""
        for city in city_manager.get_cities_for_player(self.id_player):
            if hasattr(city, "apply_research_effects"):
                city.apply_research_effects(research_effects)

    def add_diamonds(self, amount):
        self.diamonds += amount

    # Pour compatibilité, propriété d'accès dépréciée (à retirer à terme)
    @property
    def cities(self):
        """
        Propriété dépréciée : utiliser CityManager.get_cities_for_player(player.id_player)
        """
        import warnings
        warnings.warn(
            "Accès direct à player.cities déprécié. Utilisez CityManager.get_cities_for_player(player.id_player)",
            DeprecationWarning,
            stacklevel=2
        )
        return []