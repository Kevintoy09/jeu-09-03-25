"""
ResourceManager : centralise la gestion des ressources, leur génération, stockage et consommation.

Responsabilités :
- Calculer la production et le stockage effectif des ressources pour chaque ville.
- Gérer la croissance de la population et la génération d'or et de points de recherche.
- Appliquer les bonus issus des bâtiments et recherches.
- Fournir des méthodes pour consommer les ressources et connaître leur état.
- Coordonner la mise à jour de toutes les ressources à chaque tick du jeu.

Remarque : Ce manager assure la cohérence et l'évolution des ressources au fil du jeu.
"""

import logging
import unicodedata
from data.buildings_database import buildings_database
from models.constants import DEFAULT_STORAGE_CAPACITY
from models.building import Building
from managers.population_manager import PopulationManager
from data.resources_database import RESOURCES  # Ajout pour centraliser la liste des ressources

logger = logging.getLogger("ResourceManager")

def normalize_name(name):
    return ''.join(
        c for c in unicodedata.normalize('NFD', name or "")
        if unicodedata.category(c) != 'Mn'
    ).lower()

class Resource:
    def __init__(self, name: str, base_rate: float):
        self.name = name
        self.base_rate = base_rate

    def calculate_productivity(self, city) -> dict:
        workers = city.get_workers_assigned(self.name)
        base_productivity = workers * self.base_rate

        building_bonus = self.calculate_bonus(city, "resource_bonus")
        research_bonus = city.resources.get("research_bonus", {}).get(self.name, 0)

        total_productivity = base_productivity * (1 + building_bonus / 100) * (1 + research_bonus / 100)

        return {
            "base_productivity": base_productivity,
            "building_bonus": building_bonus,
            "research_bonus": research_bonus,
            "total_productivity": total_productivity
        }

    def calculate_bonus(self, city, bonus_type: str) -> float:
        bonus_percentage = 0
        for building in city.get_buildings():
            if building and building.get_status() == "Terminé":
                effects = building.effect
                if bonus_type in effects and self.name in effects[bonus_type]:
                    bonus_percentage += effects[bonus_type][self.name]
        return bonus_percentage

    def calculate_effective_storage(self, city) -> dict:
        buildings = city.get_buildings()
        base_capacity = DEFAULT_STORAGE_CAPACITY.copy()

        for building in buildings:
            if building and building.get_name() == "Entrepôt" and building.get_status() == "Terminé":
                level = building.get_level()
                effects = buildings_database["Entrepôt"]["levels"][level - 1]["effect"]
                for resource, bonus in effects.get("storage", {}).items():
                    base_capacity[resource] += bonus

        return base_capacity

    def update_resource(self, city, dt: float):
        resources = city.get_resources()
        workers = city.get_workers_assigned(self.name)

        if workers > 0:
            max_capacity = self.calculate_effective_storage(city).get(self.name, float("inf"))
            current_amount = resources.get(self.name, 0)
            productivity_data = self.calculate_productivity(city)

            resource_generated = min(productivity_data["total_productivity"] * dt, max_capacity - current_amount)
            resources[self.name] += resource_generated
            self._update_storage(city)

    def _update_storage(self, city):
        resources = city.get_resources()
        max_capacity = self.calculate_effective_storage(city).get(self.name, float("inf"))
        resources[self.name] = min(resources[self.name], max_capacity)

    def get_warehouse_bonus(self, city, resource):
        bonus = 0
        for building in city.get_buildings():
            if building and building.get_name() == "Entrepôt" and building.get_status() == "Terminé":
                level = building.get_level()
                effects = buildings_database["Entrepôt"]["levels"][level - 1]["effect"]
                if "storage" in effects and resource in effects["storage"]:
                    bonus += effects["storage"][resource]
        return bonus

def update_resource(resource, city, dt: float):
    resource.update_resource(city, dt)

class Population(Resource):
    def __init__(self, game_data):
        super().__init__('population', 0)
        self.population_manager = PopulationManager(game_data)

    def update_population_growth(self, city, dt: float):
        # La croissance est gérée uniquement par PopulationManager, qui utilise la valeur de l'Hôtel de Ville
        self.population_manager.update_city(city, dt)

class Gold(Resource):
    def __init__(self):
        super().__init__('gold', 0)

    def update_gold(self, city, dt: float):
        resources = city.get_resources()
        free_population = resources.get("population_free", 0)
        gold_rate_per_person = getattr(city, "gold_rate", 1)
        max_capacity = self.calculate_effective_storage(city).get("gold", float("inf"))
        current_gold = resources.get("gold", 0)
        gold_generated = free_population * gold_rate_per_person * dt
        gold_to_add = min(gold_generated, max_capacity - current_gold)
        resources["gold"] += gold_to_add

class ResourceManager:
    """
    Centralise la gestion des ressources du jeu (production, stockage, consommation, bonus...).
    """
    def __init__(self, game_data):
        self.game_data = game_data
        self.resources = {}
        # Cas spéciaux : population et gold
        self.resources['population'] = Population(game_data)
        self.resources['gold'] = Gold()
        # Ajoute dynamiquement toutes les autres ressources de RESOURCES
        for res_name, res_data in RESOURCES.items():
            if res_name in ('population', 'gold'):
                continue  # déjà gérées
            # Si RESOURCES[res_name] est un dict, on prend base_rate, sinon 1 par défaut
            base_rate = res_data.get('base_rate', 1) if isinstance(res_data, dict) else 1
            self.resources[res_name] = Resource(res_name, base_rate)
        self.schedule_tasks()

    def schedule_tasks(self):
        # À implémenter si besoin de tâches planifiées (bonus, events, etc.)
        pass

    def update_all(self, dt: float):
        from models.city import City  # Import local pour éviter les boucles d'import

        # Génération des ressources par ville (hors research_points)
        for island in self.game_data.islands:
            for elem in island.get("elements", []):
                if isinstance(elem, City):
                    city = elem
                    for resource_name, resource in self.resources.items():
                        if resource_name == 'population':
                            resource.update_population_growth(city, dt)
                        elif resource_name == 'gold':
                            resource.update_gold(city, dt)
                        else:
                            update_resource(resource, city, dt)
        # Génération des points de recherche (globaux, par joueur)
        self.update_research_points_for_all_players(dt)

    def update_research_points_for_all_players(self, dt: float):
        """
        Génère les points de recherche pour chaque joueur, en fonction des ouvriers affectés à l'academy
        dans chacune de ses villes avec une academy terminée.
        """
        city_manager = self.game_data.city_manager
        for player in self.game_data.player_manager.players.values():
            total_points = 0
            player_cities = city_manager.get_cities_for_player(player.id_player)
            for city in player_cities:
                academy = None
                for b in getattr(city, "buildings", []):
                    if (
                        normalize_name(getattr(b, "name", "")) == "academy"
                        and normalize_name(getattr(b, "status", "")) == "termine"
                    ):
                        academy = b
                        break
                if academy is None:
                    continue
                effect = getattr(academy, "effect", {})
                workers = city.workers_assigned.get("academy", 0)
                per_worker = effect.get("research_points_per_worker", 0)
                points_generated = workers * per_worker * dt  # dt = tick en secondes
                total_points += points_generated
            player.research_points += total_points

    def get_population_data(self, city):
        population_manager = self.game_data.population_manager
        if population_manager is None:
            raise ValueError("PopulationManager n'a pas été initialisé.")

        population_capacity = population_manager.calculate_population_limit(city)
        current_population = population_manager.get_total_population()
        return {
            "current": current_population,
            "max": population_capacity
        }

    def get_resource_data(self, city, resource_name: str) -> dict:
        resource = city.get_resources().get(resource_name, 0)
        max_capacity = self.resources[resource_name].calculate_effective_storage(city).get(resource_name, float("inf"))
        productivity_data = self.resources[resource_name].calculate_productivity(city)
        return {
            "current_quantity": resource,
            "max_quantity": max_capacity,
            "base_productivity": productivity_data["base_productivity"],
            "building_bonus": productivity_data["building_bonus"],
            "research_bonus": productivity_data.get("research_bonus", 0),
            "total_productivity": productivity_data["total_productivity"]
        }

    def get_production_rate(self, resource_key: str) -> float:
        city = self.game_data.get_active_city()
        if not city or resource_key not in self.resources or resource_key not in city.workers_assigned:
            return 0
        return self.resources[resource_key].calculate_productivity(city)["total_productivity"]

    def update_population_free(self, city):
        resources = city.get_resources()
        assigned_workers = sum(city.get_workers_assigned(resource) for resource in city.workers_assigned)
        free_population = resources["population_total"] - assigned_workers
        resources["population_free"] = free_population
        city.free_population = free_population

    def spend_resources(self, city, cost: dict) -> bool:
        resources = city.get_resources()
        import sys
        print(f"[DEBUG][spend_resources] Débit demandé pour la ville {getattr(city, 'name', None)} : {cost}", file=sys.stderr, flush=True)
        print(f"[DEBUG][spend_resources] Ressources AVANT débit : {resources}", file=sys.stderr, flush=True)
        if all(resources.get(res, 0) >= amount for res, amount in cost.items()):
            for res, amount in cost.items():
                resources[res] -= amount
            print(f"[DEBUG][spend_resources] Ressources APRÈS débit : {resources}", file=sys.stderr, flush=True)
            return True
        print(f"[DEBUG][spend_resources] Débit refusé (ressources insuffisantes)", file=sys.stderr, flush=True)
        return False

    def can_spend_resources(self, city, cost: dict) -> bool:
        """
        Vérifie si la ville a assez de ressources pour payer un coût sans rien modifier.
        """
        resources = city.get_resources()
        return all(resources.get(res, 0) >= amount for res, amount in cost.items())

    def calculate_productivity(self, city, resource_name: str) -> dict:
        if resource_name in self.resources:
            return self.resources[resource_name].calculate_productivity(city)
        return {
            "base_productivity": 0,
            "building_bonus": 0,
            "total_productivity": 0
        }