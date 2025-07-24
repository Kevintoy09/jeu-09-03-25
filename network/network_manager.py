import requests
import logging

class NetworkManager:
    """
    Gère la communication réseau avec le serveur.
    Responsable uniquement des requêtes HTTP et du retour des données/réponses.
    Ne modifie jamais le modèle en local : toute modification passe par validation serveur.
    Toutes les actions retournent l’état à jour (ville, bâtiment, etc.) pour synchronisation UI.
    """

    def __init__(self, server_url):
        self.server_url = server_url
        print(f"NetworkManager initialisé avec server_url = {self.server_url}")  # Ajout debug
        self.logger = logging.getLogger("NetworkManager")

    def get_state(self):
        """Récupère l'état complet du serveur (GET /get_state)."""
        try:
            r = requests.get(f"{self.server_url}/get_state")
            if r.status_code == 200:
                return r.json()
            else:
                self.logger.warning(f"get_state: HTTP {r.status_code} - {r.text}")
            return None
        except Exception as e:
            self.logger.error(f"get_state failed: {e}")
            return None

    def sync_game_data(self, game_data):
        """Récupère l'état complet du serveur et met à jour game_data."""
        state = self.get_state()
        if state:
            game_data.from_dict(state)
        else:
            self.logger.error("sync_game_data: Impossible de récupérer l'état serveur")

    def build_batiment(self, username=None, player_id=None, city_id=None, building_name=None, slot_index=0):
        """Envoie une requête pour construire ou améliorer un bâtiment."""
        return self._post(
            "/build",
            {
                "username": username,
                "player_id": player_id,
                "city_id": city_id,
                "building_name": building_name,
                "slot_index": slot_index
            }
        )

    def destroy_building(self, player_id=None, city_id=None, slot_index=None):
        """Envoie une requête pour détruire un niveau de bâtiment (POST /destroy_building)."""
        return self._post(
            "/destroy_building",
            {
                "player_id": player_id,
                "city_id": city_id,
                "slot_index": slot_index
            }
        )

    def complete_instantly(self, player_id=None, city_id=None, slot_index=None, building_name=None):
        """Termine instantanément la construction d'un bâtiment (POST /complete_instantly)."""
        return self._post(
            "/complete_instantly",
            {
                "player_id": player_id,
                "city_id": city_id,
                "slot_index": slot_index,
                "building_name": building_name
            }
        )

    def select_city(self, username, city_id):
        """Sélectionne une ville côté serveur (POST /select_city)."""
        return self._post(
            "/select_city",
            {
                "username": username,
                "city_id": city_id
            }
        )

    def unlock_research(self, player_id, research_name):
        """Débloque une recherche côté serveur (POST /unlock_research)."""
        return self._post(
            "/unlock_research",
            {
                "player_id": player_id,
                "research_name": research_name
            }
        )

    def assign_workers(self, city_id, resource, workers, player_id):
        """Affecte des ouvriers à une ressource dans une ville côté serveur (POST /assign_workers)."""
        data = {
            "city_id": city_id,
            "resource": resource,
            "workers": workers,
            "player_id": player_id,
        }
        return self._post("/assign_workers", data)

    def get_resource_site_info(self, site_type, player_id, island_coords=None):
        """Récupère les informations sur un site de ressource."""
        payload = {"site_type": site_type, "player_id": player_id}
        if island_coords:
            payload["island_coords"] = island_coords
        resp = self._post("/resource_site_info", payload)
        return resp

    def donate_to_resource_site(self, site_type, amount, player_id, resource_type, island_coords=None, city_id=None):
        payload = {
            "site_type": site_type,
            "amount": amount,
            "player_id": player_id,
            "resource_type": resource_type
        }
        if island_coords is not None:
            payload["island_coords"] = island_coords
        if city_id is not None:
            payload["city_id"] = city_id
        resp = self._post("/donate_to_resource_site", payload)
        return resp if resp else None

    # === TRANSPORTS (endpoints) ===
    def add_transport(self, payload):
        """Ajoute un transport (POST /add_transport)."""
        if not isinstance(payload, dict):
            raise TypeError(f"add_transport: payload must be a dict, got {type(payload)}")
        return self._post("/add_transport", payload)

    def cancel_transport(self, payload_or_id):
        """Annule un transport."""
        payload = payload_or_id if isinstance(payload_or_id, dict) else {"transport_id": payload_or_id}
        return self._post("/cancel_transport", payload)

    def get_transports_for_player(self, joueur_id):
        """Retourne la liste à jour des transports du joueur (POST /get_transports_for_player)."""
        return self._post("/get_transports_for_player", {"joueur_id": joueur_id})

    def buy_ship(self, joueur_id, ville_id):
        """Achète un bateau pour une ville donnée (POST /buy_ship)."""
        payload = {"joueur_id": joueur_id, "ville_id": ville_id}
        return self._post("/buy_ship", payload)

    def get_building_details(self, building_name, level, city_id, player_id):
        """Récupère les détails d'un bâtiment (coût, effets, can_finish_instantly, etc.) depuis le serveur."""
        url = self.server_url + "/building/details"
        payload = {
            "building_name": building_name,
            "level": level,
            "city_id": city_id,
            "player_id": player_id
        }
        try:
            resp = requests.post(url, json=payload, timeout=2)
            if resp.status_code == 200:
                return resp.json()
            else:
                self.logger.warning(f"get_building_details: HTTP {resp.status_code} - {resp.text}")
                return {}
        except Exception as e:
            self.logger.error(f"get_building_details Exception: {e}")
            return {}

    def set_game_data(self, game_data):
        """Définit les données du jeu."""
        self.game_data = game_data

    def update_city(self, city):
        """Met à jour les informations d'une ville."""
        data = city.to_dict()
        return self._post(
            "/update_city",
            data
        )

    def rename_city(self, city_id, new_name):
        """
        Envoie une requête au serveur pour renommer une ville.
        Retourne la réponse du serveur (dict).
        """
        print(f"Envoi requête renommage ville : {city_id} -> {new_name}")  # Ajout pour debug
        try:
            response = self._post(
                "/rename_city",
                {"city_id": city_id, "new_name": new_name}
            )
            return response
        except Exception as e:
            print(f"Erreur lors du renommage de la ville : {e}")
            return {"success": False, "error": str(e)}

    # --- Méthode interne ---
    def _post(self, endpoint, payload):
        """
        POST générique, retourne la réponse JSON du serveur ou un dict d'erreur explicite.
        Toujours utiliser ce point d’entrée pour toute action réseau.
        Toutes les réponses doivent inclure l’état à jour (ville, bâtiment, etc.) pour synchronisation UI.
        """
        print(f"POST {endpoint} avec {payload}")  # Ajout pour debug
        try:
            url = f"{self.server_url}{endpoint}"
            r = requests.post(url, json=payload)
            try:
                resp = r.json()
                if "success" not in resp:
                    self.logger.warning(f"_post {endpoint}: réponse sans 'success': {resp}")
                return resp
            except Exception:
                self.logger.warning(f"_post {endpoint}: réponse non JSON: {r.text}")
                return {"error": r.text}
        except Exception as e:
            self.logger.error(f"_post {endpoint} failed: {e}")
            return {"error": str(e)}