"""
PopulationManager : gère la croissance, la consommation alimentaire et les limites de population dans chaque ville.

Responsabilités :
- Calculer et mettre à jour la population de chaque ville selon la nourriture disponible.
- Gérer la consommation de céréales et la décroissance en cas de pénurie.
- Fournir les limites de population et de nourriture.
- Centraliser la logique de croissance/décroissance démographique pour l’ensemble du jeu.

Remarque : Ce manager assure la cohérence entre ressources alimentaires, bâtiments et population.
"""

import time
import logging
from models.building import Building
from data.buildings_database import buildings_database
from models.constants import NORMAL_CONSUMPTION_RATE
from models.city import City  # Pour filtrer les villes dans island["elements"]

class PopulationManager:
    def ajuster_affectation_ouvriers(self, city, refresh_callback=None):
        """
        Réaffecte les ouvriers en cas de décroissance selon la priorité :
        1. Académie
        2. Forêt
        3. Ressource avancée
        4. Ressource de base
        """
        resources = city.get_resources()
        pop_totale = resources.get("population_total", 0)
        ouvriers_affectes = sum(city.get_workers_assigned(res) for res in city.workers_assigned.keys())
        ouvriers_a_retirer = ouvriers_affectes - pop_totale
        if ouvriers_a_retirer <= 0:
            return  # Rien à faire

        # Récupération des noms de ressources prioritaires
        island = None
        if city.game_data and hasattr(city.game_data, "get_island_by_coords"):
            island = city.game_data.get_island_by_coords(city.island_coords)
        nom_site_base = island["base_resource"] if island and isinstance(island, dict) and "base_resource" in island else "site_base"
        nom_site_avance = island["advanced_resource"] if island and isinstance(island, dict) and "advanced_resource" in island else "site_avance"
        nom_foret = "wood"
        # On peut raffiner la détection si besoin

        priorites = ["academy", nom_foret, nom_site_avance, nom_site_base]
        for res in priorites:
            affectes = city.get_workers_assigned(res)
            if affectes > 0:
                a_retirer = min(affectes, ouvriers_a_retirer)
                city.workers_assigned[res] -= a_retirer
                ouvriers_a_retirer -= a_retirer
                if ouvriers_a_retirer <= 0:
                    break
        # Sécurisation : pas d'affectation négative
        for res in city.workers_assigned:
            if city.workers_assigned[res] < 0:
                city.workers_assigned[res] = 0
        # Rafraîchir la vue si un callback est fourni
        if refresh_callback:
            refresh_callback()
            
    def __init__(self, game_data):
        """
        Initialise le gestionnaire de population.
        :param game_data: Accès aux données globales du jeu (villes, ressources, etc.).
        """
        self.game_data = game_data
        self.last_update_time = 0

    def get_total_population(self):
        """
        Calcule la population totale de toutes les villes.
        :return: Population totale (int).
        """
        total_population = 0
        for island in self.game_data.islands:
            for elem in island.get("elements", []):
                if isinstance(elem, City):
                    resources = elem.get_resources()
                    total_population += resources.get("population_total", 0)
        return total_population

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def update_all_cities(self, dt: float):
    #     """
    #     Met à jour la population et la consommation de nourriture pour toutes les villes.
    #     :param dt: Temps écoulé depuis la dernière mise à jour (delta time).
    #     """
    #     current_time = time.time()
    #     if current_time - self.last_update_time < 1:  # Limiter les mises à jour à une fois par seconde.
    #         return
    #     self.last_update_time = current_time
    #     for island in self.game_data.islands:
    #         for elem in island.get("elements", []):
    #             if isinstance(elem, City):
    #                 city = self.game_data.city_manager.get_city_by_id(getattr(elem, "id", None))
    #                 if city is not None:
    #                     self.update_city(city, dt)
    #                 else:
    #                     self.update_city(elem, dt)

    def update_city(self, city, dt: float):
        """
        Met à jour la population et la consommation de nourriture pour une ville donnée.
        La croissance dépend uniquement de l'Hôtel de Ville.
        """
        try:
            resources = city.get_resources()
            current_population = resources["population_total"]
            if current_population < 0 or not getattr(city, "owner", None):
                return

         
            # Capacité de base (Hôtel de Ville)
            food_limit = 0 #self.calculate_food_limit(city)
            # Capacité supplémentaire (Windmill)
            windmill_supply = self.calculate_windmill_food_supply(city)
            current_population = resources["population_total"]

            # Population nourrie par l'Hôtel de Ville
            pop_nourished_by_townhall = min(current_population, food_limit)
            # Population excédentaire à nourrir par le moulin
            pop_to_feed_with_windmill = max(0, current_population - food_limit)
            # Population réellement nourrie (par le moulin)
            pop_nourished_by_windmill = min(pop_to_feed_with_windmill, windmill_supply)
            # Population non nourrie (famine)
            pop_unfed = max(0, current_population - food_limit - windmill_supply)

            # Récupérer le multiplicateur choisi (par défaut 1)
            cereal_multiplier = getattr(city, "windmill_cereal_multiplier", 1)

            # Récupérer le multiplicateur max selon le niveau du moulin
            max_multiplier = 1
            for building in city.get_buildings():
                if building and building.get_name() == "Windmill" and building.get_status() == "Terminé":
                    level = building.get_display_level()
                    max_multiplier = max(max_multiplier, self.get_building_effect("Windmill", level, "cereal_consumption_multiplier"))

            # Forcer le multiplicateur à rester dans les bornes autorisées
            cereal_multiplier = max(1, min(cereal_multiplier, max_multiplier))

            # La population à nourrir est directement gérée par pop_unfed

            # --- NOUVELLE LOGIQUE DE CONSOMMATION DE CÉRÉALES ---
            # Calcul du besoin en céréales
            cereal_needed = cereal_multiplier * NORMAL_CONSUMPTION_RATE * pop_unfed

     
            # Calcul du bonus de satisfaction dynamique (exemple : linéaire de 0 à 20)
            if max_multiplier > 1:
                bonus = int(10 * (cereal_multiplier - 1) / (max_multiplier - 1))
            else:
                bonus = 0
            city.satisfaction_factors.setdefault("bonus", {})["windmill"] = bonus

            # Ajout du bonus des Thermes
            for building in city.get_buildings():
                if building and building.get_name() == "Thermes" and building.get_status() == "Terminé":
                    level = building.get_display_level()
                    bonus = self.get_building_effect("Thermes", level, "satisfaction_bonus")
                    city.satisfaction_factors.setdefault("bonus", {})["thermes"] = bonus

            # Calcul de l'hygiène AVANT d'utiliser hygiene_percent
            population = resources.get("population_total", 0)
            cleanliness_capacity = 0
            for building in city.get_buildings():
                if building and building.get_name() == "Thermes" and building.get_status() == "Terminé":
                    level = building.get_display_level()
                    cleanliness_capacity += self.get_building_effect("Thermes", level, "cleanliness_capacity")
            hygiene_percent = 100 if population == 0 else int(100 * cleanliness_capacity / max(1, population))
            resources["hygiene_percent"] = hygiene_percent

            # Bonus si hygiène > 100%
            if hygiene_percent > 100:
                city.satisfaction_factors.setdefault("bonus", {})["hygiene"] = 5
            else:
                city.satisfaction_factors.setdefault("bonus", {})["hygiene"] = 0

            # Gestion du risque de peste
            if hygiene_percent < 50:
                city.has_plague = True  # Déclenche la peste si pas déjà présente

            # Ne PAS remettre has_plague à False si l’hygiène remonte !
            # La peste ne part que via le bouton (voir ThermesPopup)

            if city.has_plague:
                # Appliquer les malus de peste ici (décroissance population, satisfaction, etc.)
                city.satisfaction_factors.setdefault("malus", {})["peste"] = 40
            else:
                # Retirer le malus peste s'il existe
                if "peste" in city.satisfaction_factors.get("malus", {}):
                    city.satisfaction_factors["malus"].pop("peste")
      

            # On ne sort de la famine que si le stock de céréales est strictement positif ET que le besoin est couvert
            if (resources["cereal"] > 0 and resources["cereal"] >= cereal_needed):
                resources["cereal"] -= cereal_needed
                if "famine" in city.satisfaction_factors.get("malus", {}):
                    city.satisfaction_factors["malus"].pop("famine")
            else:
                resources["cereal"] = 0
                city.satisfaction_factors.setdefault("malus", {})["famine"] = 40

            # Ajout du malus population AVANT le calcul de satisfaction
            population_malus = self.get_population_malus(city)
            city.satisfaction_factors.setdefault("malus", {})["population"] = population_malus

            # Calcul satisfaction
            satisfaction = self.calculer_satisfaction(city)
            base_growth_rate = self.get_population_growth_from_town_hall(city)
            modificateur = max(-1, min(1, (satisfaction - 50) / 50))
            croissance_reelle = base_growth_rate * modificateur


            # Appliquer la croissance (positive ou négative) dans tous les cas
            new_population = current_population + croissance_reelle * dt
            resources["population_total"] = max(0, min(new_population, self.calculate_population_limit(city)))

            # Appel de la réaffectation si la population a baissé
            # Si la ResourceView est accessible, passer le callback de rafraîchissement
            refresh_callback = getattr(city, 'refresh_resource_view', None)
            self.ajuster_affectation_ouvriers(city, refresh_callback=refresh_callback)

            # Mise à jour des ressources nécessaires
            resources["cereal_needed"] = cereal_needed
            resources["satisfaction"] = satisfaction
            resources["population_growth"] = croissance_reelle
            resources["population_unfed"] = pop_unfed
            resources["pop_nourished_by_townhall"] = pop_nourished_by_townhall
            resources["pop_nourished_by_windmill"] = pop_nourished_by_windmill
            resources["total_food_supply"] = pop_nourished_by_townhall + pop_nourished_by_windmill

        except Exception as e:
            logging.error(f"Erreur dans PopulationManager.update_city : {e}")
    
    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    # def calculate_population_limit(self, city) -> int:
    #     """
    #     Calcule la capacité maximale de population d'une ville en fonction des bâtiments.
    #     :param city: La ville pour laquelle calculer la capacité.
    #     :return: Capacité maximale de population.
    #     """
    #     population_capacity = 0
    #     for building in city.get_buildings():
    #         if building and building.get_name() == "Hôtel de Ville":
    #             level = building.get_display_level()
    #             capacity_bonus = self.get_building_effect("Hôtel de Ville", level, "population_capacity")
    #             population_capacity += capacity_bonus
    #     return population_capacity
    def calculate_population_limit(self, city) -> int:
        """
        Calcule la capacité maximale de population d'une ville en fonction des bâtiments.
        :param city: La ville pour laquelle calculer la capacité.
        :return: Capacité maximale de population.
        """
        population_capacity = 0
        for building in city.get_buildings():
            if building and building.get_name() == "Hôtel de Ville":
                level = building.get_display_level()
                capacity_bonus = self.get_building_effect("Hôtel de Ville", level, "population_capacity")
                population_capacity += capacity_bonus
        return population_capacity

    # MÉTHODE COMMENTÉE POUR TEST DE CODE MORT
    def get_population_growth_from_town_hall(self, city) -> float:
         """
         Retourne la croissance de la population définie par l'Hôtel de Ville (et uniquement celle-ci).
         """
         for building in city.get_buildings():
             if building and building.get_name() == "Hôtel de Ville":
                 level = building.get_display_level()
                 return self.get_building_effect("Hôtel de Ville", level, "population_growth")
         return 0.0 
    
    def get_building_effect(self, building_name, level, effect_key):
        """
        Récupère la valeur d'effet d'un bâtiment donné à un niveau donné.
        """
        level = max(1, level)  # S'assurer que le niveau est au moins 1
        try:
            return buildings_database[building_name]["levels"][level - 1]["effect"].get(effect_key, 0)
        except Exception:
            return 0

    def get_population_malus(self, city):
        """
        Malus = 1 par tranche de 10 habitants, plafonné à 8 jusqu'à 80 habitants,
        puis 1 par tranche de 10 au-delà.
        (Toujours positif, car il sera soustrait dans le calcul de satisfaction)
        """
        population = int(city.get_resources().get("population_total", 0))
        if population <= 80:
            return min(8, population // 10)
        else:
            return population // 10
    
    def calculate_windmill_food_supply(self, city) -> int:
        """
        Calcule la capacité totale de nourriture fournie par les moulins (windmill).
        """
        food_supply = 0
        for building in city.get_buildings():
            if building and building.get_name() == "Windmill" and building.get_status() == "Terminé":
                level = building.get_display_level()
                supply = self.get_building_effect("Windmill", level, "food_supply")
                food_supply += supply
        return food_supply

    def update_worker_assignment_display(self, city_data):
        """
        Met à jour l'affichage de l'affectation des ouvriers pour une ville donnée.
        """
        ouvriers_ville = city_data.workers_assigned.get(self.resource_key, 0)
        self.ouvriers_label.text = f"Ouvriers affectés par votre ville : {ouvriers_ville}"
        self.worker_slider.value = ouvriers_ville
        self.worker_input.text = str(ouvriers_ville)

    def calculer_satisfaction(self, city):
        total_malus = sum(city.satisfaction_factors.get("malus", {}).values())
        total_bonus = sum(city.satisfaction_factors.get("bonus", {}).values())
        # Valeur de base = 50
        satisfaction = max(0, min(100, 50 - total_malus + total_bonus))
        city.satisfaction = satisfaction
        return satisfaction