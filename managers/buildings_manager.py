"""
BuildingsManager : gère la création, l'évolution et la gestion des bâtiments dans une ville.

Responsabilités :
- Centraliser toute la logique métier liée aux bâtiments (coûts, bonus, timers, effets).
- Lancer la construction, l'amélioration, la destruction.
- Appliquer tous les bonus (ex : architecte) de façon cohérente.
- Garantir que l’UI ne fait qu’afficher et déclencher des actions, jamais de calcul métier.
- Synchroniser l’état à jour après chaque action.
"""

from datetime import datetime
from data.buildings_database import buildings_database
from managers.resource_manager import ResourceManager
from models.building import Building
import unicodedata
import logging

class BuildingsManager:
    """
    Gère la création, l'évolution et la gestion des bâtiments dans une ville.
    Toute la logique métier (coût, bonus, timer, effets) est centralisée ici.
    L'UI ne fait qu'afficher, déclencher les actions, attendre la réponse, synchroniser et afficher.
    """

    def __init__(self, game_data, city_view=None, update_all_callback=None, network_manager=None, username=None):
        self.game_data = game_data
        self.city_view = city_view
        self.buildings_database = buildings_database
        self.resource_manager = ResourceManager(game_data)
        self.instant_completion_threshold = 5
        self.network_manager = network_manager
        self.username = username
        self.update_all_callback = update_all_callback

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def get_instant_completion_threshold(self, player=None):
    #     base = self.instant_completion_threshold
    #     if player is None:
    #         current_player_id = getattr(self.game_data, "current_player_id", None)
    #         player = self.game_data.player_manager.get_player(current_player_id) if current_player_id else None
    #     bonus = int(getattr(player, "instant_completion_bonus", 0)) if player and hasattr(player, "instant_completion_bonus") else 0
    #     return base + bonus

    def set_network_config(self, network_manager, username):
        self.network_manager = network_manager
        self.username = username

    def set_building_status(self, building, status, city_data=None, **kwargs):
        building = Building.ensure_instance(building)
        building.status = status
        bname = getattr(building, "name", None)
        level = getattr(building, "level", 1)
        if status == "En construction":
            building.started_at = kwargs.get("started_at", datetime.utcnow().isoformat())
            building.build_duration = kwargs.get("build_duration", 0)
            if bname and self._normalize_name(bname) == "atelier d'architecte":
                if bname in buildings_database and level > 1:
                    prev_effect = buildings_database[bname]["levels"][level-2].get("effect", {})
                else:
                    prev_effect = {}
                building.previous_effect = prev_effect
        elif status == "Terminé":
            building.started_at = None
            building.build_duration = 0
            if bname and self._normalize_name(bname) == "academy":
                effect = buildings_database["Academy"]["levels"][level-1]["effect"]
                building.effect = effect
            elif "effect" in kwargs:
                building.effect = kwargs["effect"]
            else:
                if bname in buildings_database:
                    levels = buildings_database[bname]["levels"]
                    if 0 < level <= len(levels):
                        building.effect = levels[level-1].get("effect", {})
            if bname and self._normalize_name(bname) == "atelier d'architecte":
                if hasattr(building, "previous_effect"):
                    del building.previous_effect
        elif status == "Annulé":
            building.started_at = None
            building.build_duration = 0
        if city_data:
            self.get_city_building_data(city_data)

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def check_construction_plan_research(self):
    #     current_player_id = self.game_data.current_player_id
    #     if current_player_id is None:
    #         return False
    #     player = self.game_data.player_manager.get_player(current_player_id)
    #     return "plan_de_construction" in [r.replace(" ", "_").lower() for r in getattr(player, "unlocked_research", [])]

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def get_current_player(self):
    #     current_player_id = getattr(self.game_data, "current_player_id", None)
    #     if current_player_id:
    #         return self.game_data.player_manager.get_player(current_player_id)
    #     return None

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def check_building_conditions(self, city, slot_index, building_name, player_id=None):
    #     city_owner = getattr(city, "owner", None) or getattr(city, "owner_id", None)
    #     if player_id is not None and city_owner != player_id:
    #         return False, "Vous n'êtes pas propriétaire de la ville."
    #     building_data = self.buildings_database.get(building_name)
    #     if not building_data:
    #         return False, "Bâtiment inconnu."
    #     required_research = building_data.get("required_research")
    #     player = self.game_data.player_manager.get_player(player_id) if player_id else None
    #     if required_research and (not player or required_research not in getattr(player, "unlocked_research", [])):
    #         return False, "Recherche requise non débloquée."
    #     current_building = city.get_building_by_index(slot_index)
    #     current_building = Building.ensure_instance(current_building) if current_building else None
    #     if current_building:
    #         if current_building.get_name() != building_name:
    #             return False, "Le slot est occupé par un autre bâtiment."
    #         current_level = current_building.get_level()
    #     else:
    #         current_level = 0
    #     levels = self.buildings_database[building_name]["levels"]
    #     if current_level >= len(levels):
    #         return False, "Niveau maximum déjà atteint."
    #     max_count = building_data.get("max_count")
    #     if max_count is not None:
    #         current_count = sum(
    #             1 for b in city.get_buildings() if b and Building.ensure_instance(b).get_name() == building_name
    #         )
    #         if current_count >= max_count:
    #             return False, "Nombre maximal de bâtiments atteint."
    #     target_level = current_level + 1
    #     details = self.get_building_details(building_name, target_level, city)
    #     if not details:
    #         return False, "Données du niveau cible manquantes."
    #     if not self.resource_manager.can_spend_resources(city, details["cost"]):
    #         return False, "Ressources insuffisantes."
    #     return True, None

    def build_or_upgrade_building(self, city_data, slot_index, building_name, player_id=None):
        # Vérification unique et atomique
        if not player_id:
            return {"success": False, "message": "Aucun joueur."}
        if getattr(city_data, "owner", None) is None:
            city_data.owner = player_id
        city_owner = getattr(city_data, "owner", None) or getattr(city_data, "owner_id", None)
        if city_owner != player_id:
            return {"success": False, "message": "Vous n'êtes pas propriétaire de la ville."}
        building_data = self.buildings_database.get(building_name)
        if not building_data:
            return {"success": False, "message": "Bâtiment inconnu."}
        required_research = building_data.get("required_research")
        player = self.game_data.player_manager.get_player(player_id)
        if required_research and (not player or required_research not in getattr(player, "unlocked_research", [])):
            return {"success": False, "message": "Recherche requise non débloquée."}
        current_building = city_data.get_building_by_index(slot_index)
        current_building = Building.ensure_instance(current_building) if current_building else None
        if current_building:
            if current_building.get_name() != building_name:
                return {"success": False, "message": "Le slot est occupé par un autre bâtiment."}
            current_level = current_building.get_level()
        else:
            current_level = 0
        levels = self.buildings_database[building_name]["levels"]
        if current_level >= len(levels):
            return {"success": False, "message": "Niveau maximum déjà atteint."}
        max_count = building_data.get("max_count")
        if max_count is not None:
            current_count = sum(
                1 for b in city_data.get_buildings() if b and Building.ensure_instance(b).get_name() == building_name
            )
            if current_count >= max_count:
                return {"success": False, "message": "Nombre maximal de bâtiments atteint."}
        target_level = current_level + 1
        details = self.get_building_details(building_name, target_level, city_data)
        if not details:
            return {"success": False, "message": "Données du niveau cible manquantes."}
        cost = details["cost"] if details else {}
        if not self.resource_manager.can_spend_resources(city_data, cost):
            return {"success": False, "message": "Ressources insuffisantes."}
        # Déduction et construction atomique
        if not self.resource_manager.spend_resources(city_data, cost):
            return {"success": False, "message": "Ressources insuffisantes (conflit concurrentiel)."}
        construction_time = details.get("construction_time", 10) if details else 10
        now = datetime.utcnow()
        building = Building(
            name=building_name,
            status="En construction",
            level=target_level,
            effect=current_building.effect if current_building else {},
            previous_effect=current_building.effect if current_building else {},
            started_at=now.isoformat(),
            build_duration=int(construction_time),
            slot_index=slot_index,
        )
        self.set_building_status(building, "En construction", started_at=now.isoformat(), build_duration=int(construction_time))
        city_data.set_building_by_index(slot_index, building)
        self._refresh_after_action(city_data)
        return {"success": True}

    def destroy_building(self, city_data, slot_index, player_id=None):
        current_building = city_data.get_building_by_index(slot_index)
        current_building = Building.ensure_instance(current_building) if current_building else None
        if not current_building:
            return False
        city_owner = getattr(city_data, "owner", None) or getattr(city_data, "owner_id", None)
        if player_id is not None and city_owner != player_id:
            return False
        current_level = current_building.get_level()
        if current_level > 1:
            new_level = current_level - 1
            details = self.get_building_details(current_building.get_name(), new_level, city_data)
            current_building.level = new_level
            current_building.effect = details["effect"] if details and "effect" in details else {}
            city_data.set_building_by_index(slot_index, current_building)
        else:
            city_data.set_building_by_index(slot_index, None)
        self.apply_building_bonuses(city_data)
        self._refresh_after_action(city_data)
        return True

    def apply_building_bonuses(self, city_data):
        if hasattr(city_data, "reset_building_bonuses"):
            city_data.reset_building_bonuses()
        for building in city_data.get_buildings():
            building = Building.ensure_instance(building)
            if not building:
                continue
            effect = getattr(building, "effect", {})
            # Appliquer ici l'effet du bâtiment sur la ville (adapter selon la logique métier)

    def update_all_building_statuses(self, city_data):
        for i, b in enumerate(city_data.buildings):
            b = Building.ensure_instance(b)
            if b is not None and b.status == "En construction":
                remaining = self.get_remaining_time(b)
                if remaining <= 0:
                    self.set_building_status(b, "Terminé")
            city_data.buildings[i] = b

    def complete_task(self, construction_key, city_data, slot_index, building_name=None, level=None):
        building = city_data.get_building_by_index(slot_index)
        building = Building.ensure_instance(building)
        if building and getattr(building, "status", None) == "En construction":
            details = self.get_building_details(building.get_name(), building.level, city_data)
            self.set_building_status(building, "Terminé", effect=details.get("effect", {}) if details else {})
            city_data.set_building_by_index(slot_index, building)
            notif_manager = getattr(self.game_data, "notification_manager", None)
            owner_id = getattr(city_data, "owner", None)
            msg = f"Construction du bâtiment '{building.get_name()}' terminée dans la ville '{city_data.get_name()}'."
            if notif_manager and owner_id:
                notif_manager.add_notification(owner_id, msg, "construction")
        self.apply_building_bonuses(city_data)
        self._refresh_after_action(city_data)

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    def complete_instantly(self, city, slot_index, building_name=None):
        buildings = city.get_buildings()
        if 0 <= slot_index < len(buildings):
            building = buildings[slot_index]
            if building and getattr(building, "status", None) == "En construction":
                building.status = "Terminé"
                building.remaining_time = 0
                return True
        return False

    def get_remaining_time(self, building):
        building = Building.ensure_instance(building)
        if building.status != "En construction" or not building.started_at or building.build_duration <= 0:
            return 0
        try:
            dt_started = datetime.fromisoformat(building.started_at)
        except Exception:
            try:
                dt_started = datetime.strptime(building.started_at, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                return 0
        elapsed = (datetime.utcnow() - dt_started).total_seconds()
        return max(0, int(building.build_duration - elapsed))

    def get_building_details(self, building_name, level, city_data=None):
        levels = []
        if city_data is not None:
            custom_data = self.get_city_building_data(city_data)
            levels = custom_data.get(building_name, {}).get("levels", [])
        else:
            levels = buildings_database.get(building_name, {}).get("levels", [])
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 1
        return levels[level - 1] if 0 <= level - 1 < len(levels) else None

    def get_city_building_data(self, city_data):
        city_data.custom_buildings_data = {
            building_name: {
                "levels": [
                    {
                        "cost": level["cost"].copy(),
                        "construction_time": level["construction_time"]
                    }
                    for level in building_data.get("levels", [])
                ]
            }
            for building_name, building_data in buildings_database.items()
        }
        self.apply_architect_reductions(city_data.custom_buildings_data, city_data)
        return city_data.custom_buildings_data

    def apply_architect_reductions(self, buildings_data, city_data):
        cost_reduction, time_reduction = 0, 0
        for building in getattr(city_data, "get_buildings", lambda: [])():
            building = Building.ensure_instance(building)
            if building and building.get_name() == "Atelier d'Architecte":
                if building.get_status() == "Terminé":
                    effect = building.effect
                    cost_reduction += effect.get("construction_cost_reduction", 0)
                    time_reduction += effect.get("construction_time_reduction", 0)
                elif building.get_status() == "En construction" and hasattr(building, "previous_effect"):
                    effect = building.previous_effect
                    cost_reduction += effect.get("construction_cost_reduction", 0)
                    time_reduction += effect.get("construction_time_reduction", 0)
        if cost_reduction == 0 and time_reduction == 0:
            return
        for building_data in buildings_data.values():
            for level_data in building_data.get("levels", []):
                for resource, cost in level_data["cost"].items():
                    level_data["cost"][resource] = max(1, int(cost * (1 - cost_reduction / 100)))
                level_data["construction_time"] = max(1, int(level_data["construction_time"] * (1 - time_reduction / 100)))

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def get_building_level(self, city_data, building_name: str) -> int:
    #     b = city_data.get_building_by_name(building_name)
    #     b = Building.ensure_instance(b)
    #     return b.get_level() if b else 0

    def _refresh_after_action(self, city_data):
        try:
            if self.city_view and hasattr(self.city_view, 'is_active'):
                if self.city_view.is_active:
                    self.city_view.update_city(city_data)
            elif self.city_view:
                if hasattr(self.city_view, 'parent') and self.city_view.parent:
                    self.city_view.update_city(city_data)
        except Exception:
            pass
        if self.update_all_callback:
            self.update_all_callback()

    def _normalize_name(self, name):
        return ''.join(
            c for c in unicodedata.normalize('NFD', name or "")
            if unicodedata.category(c) != 'Mn'
        ).lower()