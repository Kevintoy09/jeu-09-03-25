from datetime import datetime, timezone
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty, DictProperty, ObjectProperty
)

class Building(EventDispatcher):
    """
    Représente un bâtiment dans la ville.
    Toute conversion dict→instance doit passer par ensure_instance().
    Le niveau à afficher doit être obtenu via get_display_level().
    """

    name = StringProperty()
    level = NumericProperty(0)
    status = StringProperty("En construction")
    effect = DictProperty({})
    previous_effect = DictProperty({})
    started_at = StringProperty(None, allownone=True)
    build_duration = NumericProperty(0)
    slot_index = NumericProperty(None, allownone=True)
    city = ObjectProperty(None, allownone=True)

    def __init__(
        self,
        name: str,
        level: int = 0,
        status: str = "En construction",
        effect: dict = None,
        previous_effect: dict = None,
        started_at: str = None,
        build_duration: int = 0,
        slot_index: int = None,
        city=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        if not name:
            raise ValueError("Building 'name' must not be None or empty.")
        self.name = name
        self.level = max(0, level)
        self.status = status
        self.effect = effect.copy() if effect else {}
        self.previous_effect = previous_effect.copy() if previous_effect else {}
        self.started_at = started_at
        self.build_duration = build_duration
        self.slot_index = slot_index
        self.city = city

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "status": self.status,
            "timer": self.get_remaining_time(),
            "effect": self.effect,
            "previous_effect": self.previous_effect,
            "started_at": self.started_at,
            "build_duration": self.build_duration,
            "slot_index": self.slot_index,
            # city n'est pas sérialisé (référence circulaire)
        }

    @classmethod
    def from_dict(cls, data: dict, city=None):
        """
        Crée une instance Building à partir d'un dict, ou retourne l'instance si déjà un Building.
        Si l'effet est absent ou vide, il est récupéré depuis la base de données selon le nom et le niveau.
        """
        if isinstance(data, cls):
            if city is not None:
                data.city = city
            return data
        name = data.get("name")
        if not name:
            raise ValueError(f"Cannot create Building: missing or empty 'name'. Data: {data!r}")
        level = data.get("level", 0)
        effect = data.get("effect")
        # Correction : si effect absent ou vide, on va le chercher dans la base de données
        if not effect:
            try:
                from data.buildings_database import buildings_database
                building_data = buildings_database.get(name, {})
                levels = building_data.get("levels", [])
                if 0 < level <= len(levels):
                    effect = levels[level-1].get("effect", {})
                else:
                    effect = {}
            except Exception as e:
                effect = {}
        return cls(
            name=name,
            level=level,
            status=data.get("status", "En construction"),
            effect=effect,
            previous_effect=data.get("previous_effect"),
            started_at=data.get("started_at"),
            build_duration=data.get("build_duration", 0),
            slot_index=data.get("slot_index", None),
            city=city,
        )

    @staticmethod
    def ensure_instance(building, city=None):
        """
        Convertit un dict ou instance en instance Building.
        Utiliser partout (managers, City, UI).
        """
        if isinstance(building, Building):
            if city is not None:
                building.city = city
            return building
        if isinstance(building, dict):
            return Building.from_dict(building, city=city)
        return None

    def get_display_level(self) -> int:
        """
        Retourne le niveau à afficher (niveau réel sauf en construction, alors level-1 sauf pour 1er niveau).
        """
        if self.status == "En construction" and self.get_remaining_time() > 0:
            return max(0, self.level - 1)
        return self.level

    def get_name(self) -> str:
        return self.name

    def get_status(self) -> str:
        return self.status

    def get_level(self) -> int:
        return self.level

    def get_remaining_time(self) -> int:
        """Calcule dynamiquement le temps restant à partir du début + durée."""
        if not self.started_at or not self.build_duration or self.status != "En construction":
            return 0
        try:
            dt_start = datetime.fromisoformat(self.started_at)
            if dt_start.tzinfo is None:
                dt_start = dt_start.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            elapsed = (now - dt_start).total_seconds()
            remaining = int(self.build_duration - elapsed)
            return max(0, remaining)
        except Exception:
            return 0

    def update_status_from_time(self):
        """Passe le statut à 'Terminé' si le timer est fini (utilisé côté serveur)."""
        if self.status == "En construction" and self.get_remaining_time() == 0:
            self.status = "Terminé"

    @staticmethod
    def get_building_effect(building_name, level, effect_key):
        from data.buildings_database import buildings_database
        if level < 1:
            return 0
        building_data = buildings_database.get(building_name, {})
        levels = building_data.get("levels", [])
        if 0 <= (level - 1) < len(levels):
            return levels[level - 1].get("effect", {}).get(effect_key, 0)
        return 0