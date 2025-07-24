from models.city import City
from models.building import Building
from managers.population_manager import PopulationManager

class CityManager:
    """
    Gère la liste des villes du jeu, la ville active, la synchronisation avec les joueurs et la désérialisation.
    Toute logique métier liée à la construction, bonus, timers, etc. doit être déléguée à BuildingsManager.
    Toute désérialisation de ville doit passer par City.from_dict (jamais de dict brut ni de patch local).
    """

    def __init__(self, game_data):
        self.game_data = game_data
        self._cities = []
        self._active_city = None
        # Cache pour maintenir la consistance des instances de villes
        self._city_instance_cache = {}

    def create_new_city(self, player, city_name, base_city=None):
        owner_id = self.game_data.current_player_id or getattr(player, "id_player", None) or getattr(player, "username", None)
        if base_city is not None:
            real_city = self.get_city_by_id(getattr(base_city, "id", None))
            if not real_city:
                real_city = base_city
                self.add_city(real_city)
                for island in self.game_data.islands:
                    if real_city.coords == island.get("coords"):
                        island["elements"].append(real_city)
                        break
            real_city.name = city_name
            real_city.owner = str(owner_id)
            self.add_city(real_city)
            self.build_city_index(self.game_data.islands, self.game_data.player_manager.players)
            print(f"[DEBUG] Ville colonisée (base_city) : {real_city.name} | owner = {real_city.owner} ({type(real_city.owner)}) | attendu = {owner_id} ({type(owner_id)})")
            return real_city
        else:
            target_island = self.game_data.islands[0]
            new_city = City(
                name=city_name,
                owner=owner_id,
                coords=target_island["coords"],
                city_type="player",
                base_resource=target_island["base_resource"],
                game_data=self.game_data,
                id=None
            )
            new_city.owner = player.id_player
            print(f"[DEBUG] Nouvelle ville créée : {new_city.name} | owner = {new_city.owner} | attendu = {player.id_player}")
            self.add_city(new_city)
            target_island["elements"].append(new_city)
            return new_city

    def add_city(self, city):
        if city not in self._cities:
            self._cities.append(city)
            # Ajoute au cache
            city_id = getattr(city, 'id', None)
            if city_id:
                self._city_instance_cache[city_id] = city
        for island in self.game_data.islands:
            if city.coords == island["coords"] and city not in island["elements"]:
                island["elements"].append(city)

    def get_all_cities(self):
        return self._cities

    def get_cities_for_player(self, player_id):
        return [city for city in self._cities if getattr(city, "owner", '') == player_id]

    def find_unowned_city(self, island_coords: tuple, base_resource: str):
        island = self.game_data.get_island_by_coords(island_coords)
        if not island:
            return None
        for elem in island["elements"]:
            if isinstance(elem, City) and elem.base_resource == base_resource and not getattr(elem, "owner", ""):
                return elem
        return None

    def player_has_city(self, player_id: str) -> bool:
        return any(getattr(city, "owner", "") == player_id for city in self._cities)

    def update_active_city(self, city):
        self.set_active_city(city)
        if city:
            self.game_data.population_manager = PopulationManager(self.game_data)

    def set_active_city(self, city):
        if city is not None:
            # Toujours s'assurer que c'est l'instance centrale
            real_city = self.get_city_by_id(getattr(city, "id", None)) if city else None
            if real_city:
                self._active_city = real_city
            else:
                self._active_city = city

    def get_active_city(self):
        return self._active_city

    def get_or_create_city_from_dict(self, city_dict, game_data, coords=None):
        """
        Récupère ou crée une ville à partir d'un dict, toujours via le cache pour garantir l’unicité.
        """
        city_id = city_dict.get("id")
        if city_id:
            if city_id in self._city_instance_cache:
                city = self._city_instance_cache[city_id]
                city.from_dict_instance(city_dict)
                return city
        # Création si aucune instance trouvée
        new_city = City.from_dict(city_dict, game_data, coords)
        self._city_instance_cache[city_id] = new_city
        self.add_city(new_city)
        return new_city

    def get_city_by_id(self, city_id):
        """
        Retourne l’instance unique de la ville par son id, toujours via le cache.
        """
        return self._city_instance_cache.get(city_id)

    def update_city_from_dict(self, city_dict):
        """
        Met à jour une ville existante à partir d'un dictionnaire (venant du serveur).
        Utilise get_or_create_city_from_dict pour éviter les instances multiples.
        """
        city_id = city_dict.get("id")
        
        # Utilise la nouvelle méthode qui gère le cache automatiquement
        city = self.get_or_create_city_from_dict(city_dict, self.game_data)
        
        # Met à jour la ville active si nécessaire
        if getattr(self._active_city, "id", None) == city_id:
            self._active_city = city

    def build_city_index(self, islands, players):
        """
        Reconstruit la liste des villes à partir des îles, en garantissant l’unicité via le cache.
        """
        self._cities = []
        for island in islands:
            for elem in island["elements"]:
                if isinstance(elem, City):
                    city_id = getattr(elem, "id", None)
                    if city_id:
                        # Remplace l’élément par l’instance du cache si elle existe
                        if city_id in self._city_instance_cache:
                            cached_city = self._city_instance_cache[city_id]
                            if cached_city not in self._cities:
                                self._cities.append(cached_city)
                            # Remplace dans l’île
                            idx = island["elements"].index(elem)
                            island["elements"][idx] = cached_city
                        else:
                            self._city_instance_cache[city_id] = elem
                            if elem not in self._cities:
                                self._cities.append(elem)
                    else:
                        if elem not in self._cities:
                            self._cities.append(elem)

    def from_dict(self, cities_data, game_data):
        """
        Désérialise la liste des villes à partir de leur représentation dict.
        Garantit l’unicité des instances et nettoie le cache.
        """
        new_city_ids = {city_dict.get("id") for city_dict in cities_data}
        # Nettoie le cache pour les villes supprimées
        to_remove = [city_id for city_id in self._city_instance_cache.keys() if city_id not in new_city_ids]
        for city_id in to_remove:
            del self._city_instance_cache[city_id]
        # Met à jour ou crée les villes
        self._cities = []
        for city_dict in cities_data:
            city = self.get_or_create_city_from_dict(city_dict, game_data)
            if city not in self._cities:
                self._cities.append(city)