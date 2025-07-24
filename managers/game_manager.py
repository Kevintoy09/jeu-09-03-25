"""
GameManager : supervise la logique globale du jeu et les transitions d'état.

Responsabilités :
- Gérer les vues et états du jeu.
- Coordonner les actions entre ResourceManager, BuildingsManager, etc.
- Gérer les actions et événements globaux du jeu.
"""

from data.buildings_database import buildings_database
from models.city import City  # Pour identification des villes dans elements

class GameManager:
    def __init__(self, resource_manager, buildings_manager):
        self.resource_manager = resource_manager
        self.buildings_manager = buildings_manager

    # --- Gestion des ressources ---
    def get_resource_data(self, city_data, resource_name):
        """Retourne les données dynamiques pour une ressource spécifique."""
        return self.resource_manager.get_resource_data(city_data, resource_name)

    # --- Gestion des bâtiments ---
    def start_construction(self, island_coords, city_id, city_data, building_name, slot_index, player_id, update_header_callback=None, update_slots_callback=None):
        """
        Démarre la construction d'un bâtiment via BuildingsManager.
        Vérifie la validité et les ressources avant de lancer la construction.
        """
        level = 1  # Toujours niveau 1 pour une nouvelle construction

        # Obtenir les détails du bâtiment dans la base de données
        details = buildings_database.get(building_name, {}).get("levels", [])[level - 1]
        if not details or not self.buildings_manager.can_afford_building(city_data.resources, building_name, level):
            print("[ERREUR] Construction impossible. Fonds insuffisants ou données manquantes.")
            return False

        # Appel à BuildingsManager pour démarrer la construction
        success = self.buildings_manager.start_construction(
            island_coords=island_coords,
            city_name=city_id,  # city_id est gardé ici, sauf si city_name est explicitement requis
            city_data=city_data,
            building_name=building_name,
            slot_index=slot_index,
            player_id=player_id
        )

        # Appel des callbacks si succès
        if success:
            if update_header_callback:
                update_header_callback()
            if update_slots_callback:
                update_slots_callback(city_data)  # Correction : passer city_data si nécessaire

        return success

    # --- Recherche de ville par ID ---
    def get_city_by_id(self, city_id):
        """Récupère une ville par son identifiant."""
        for island in self.resource_manager.game_data.islands:
            for elem in island.get("elements", []):
                if isinstance(elem, City) and hasattr(elem, "id") and elem.id == city_id:
                    return elem
        raise ValueError(f"[ERROR] Ville avec id '{city_id}' introuvable.")

    # --- Mise à jour globale de toutes les villes ---
    def update_all_cities(self, dt: float):
        """Met à jour toutes les villes du jeu."""
        for island in self.resource_manager.game_data.islands:
            for elem in island.get("elements", []):
                if isinstance(elem, City) and elem.owner is not None:
                    self.update_city(elem, dt)

    # --- Mise à jour individuelle d'une ville ---
    def update_city(self, city, dt: float):
        """
        Met à jour une ville spécifique.
        À compléter : ici, on pourrait par exemple appeler resource_manager.update pour cette ville.
        """
        pass