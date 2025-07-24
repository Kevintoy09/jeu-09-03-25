SITE_TO_RESOURCE = {
    "forest": "wood",
    "quarry": "stone",
    "grain_field": "cereal",
    "iron_mine": "iron",
    "papyrus_pond": "papyrus",
    "horse_ranch": "horse",
    "marble_mine": "marble",
    "glassworks": "glass",
    "pasture": "meat",
    "coal_mine": "coal",
    "gunpowder_lab": "gunpowder",
    "spice_garden": "spices",
    "cotton_field": "cotton"
}

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.clock import Clock
from config.message_info import (
    ERROR_INVALID_DONATION,
    ERROR_NO_ACTIVE_CITY,
    ERROR_SERVER,
    ERROR_LOADING_SITE,
    not_enough_resource,
    show_error_popup
)

class ResourceView(Screen):
    """
    Vue du site de ressource partagé façon Ikariam.
    - Affiche le niveau du site, la capacité max d'ouvriers par joueur.
    - Affiche la liste des villes de l'île, ouvriers affectés/max, dons.
    - Permet d'améliorer le site (bouton don).
    - Affiche le temps nécessaire pour upgrade et un timer.
    """
    def __init__(self, manager, site_type, city_data=None, island_coords=None, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.site_type = site_type
        self.city_data = city_data
        self.island_coords = island_coords
        # Initialisation robuste de resource_key
        if not site_type:
            print("[ERREUR] ResourceView.__init__ appelé sans site_type !")
        self.resource_key = SITE_TO_RESOURCE.get(site_type, site_type)
        print(f"[DEBUG] ResourceView.__init__ site_type={site_type}, island_coords={island_coords}, city_data={city_data}")

        self.layout = BoxLayout(orientation="vertical", size_hint_y=1)
        # Supprime l'espace en haut en ajoutant un widget invisible de 0px ou en vérifiant qu'aucun Widget vide n'est ajouté avant le titre
        self.add_widget(self.layout)
        self.upgrade_timer_seconds = 0
        self.upgrade_timer_event = None

        # Titre et niveau du site
        self.title_label = Label(
            text=f"[b]{self.site_type.capitalize()}[/b]",
            size_hint_y=None, height=40, color=(0,0,0,1),
            halign="center", markup=True
        )
        self.title_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.layout.add_widget(self.title_label)
        self.level_label = Label(text="Niveau du site : ?", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.level_label)
        self.base_yield_label = Label(text="Récolte de base : ?", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.base_yield_label)
        self.max_workers_label = Label(text="Ouvriers max par ville : ?", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.max_workers_label)

        # Description de la ressource
        desc = f"Permet de générer du {self.site_type.capitalize()}"
        self.desc_label = Label(
            text=desc, size_hint_y=None, height=30, color=(0,0,0,1),
            halign="center"
        )
        self.desc_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.layout.add_widget(self.desc_label)

        # Champ et bouton pour affecter des ouvriers globalement
        worker_line = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        self.worker_input = TextInput(text="0", size_hint=(0.5, 1))
        self.assign_btn = Button(text="Affecter", size_hint=(0.5, 1), color=(0,0,0,1))
        self.assign_btn.bind(on_press=lambda inst: self.assign_workers_active_city())
        worker_line.add_widget(self.worker_input)
        worker_line.add_widget(self.assign_btn)
        self.layout.add_widget(worker_line)

        # Slider pour affecter les ouvriers
        self.worker_slider = Slider(min=0, max=1, value=0, step=1, size_hint_y=None, height=40)
        self.worker_slider.bind(value=self.on_slider_value)
        self.layout.add_widget(self.worker_slider)

        self.ouvriers_label = Label(
            text="Ouvriers affectés par votre ville : 0",
            size_hint_y=None, height=30, color=(0,0,0,1)
        )
        self.layout.add_widget(self.ouvriers_label)
        # Suppression du champ Production per hour
        # Ajout d'un champ Timer pour l'upgrade
        self.upgrade_time_label = Label(
            text="Temps nécessaire pour upgrade : ?",
            size_hint_y=None, height=30, color=(0.6,0.2,0.2,1)
        )
        self.upgrade_timer_label = Label(
            text="Timer : --:--",
            size_hint_y=None, height=30, color=(0.7,0.1,0.1,1)
        )
        self.layout.add_widget(self.upgrade_time_label)
        self.layout.add_widget(self.upgrade_timer_label)

        # ----------- ESPACE 20px ENTRE LES PARTIES -----------
    
        # ------------- FIN ESPACE ---------------

        # --- NOUVELLE SECTION : Développer le site de production ---
        self.layout.add_widget(Widget(size_hint_y=None, height=10))
        self.upgrade_title_label = Label(
            text="[b]Développer le site de production[/b]",
            size_hint_y=None, height=35, color=(0.15,0.3,0.5,1), markup=True, halign="center"
        )
        self.upgrade_title_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.layout.add_widget(self.upgrade_title_label)

        self.site_next_bonus_label = Label(
            text="Bonus du site au prochain niveau : ?",
            size_hint_y=None, height=30, color=(0.1,0.6,0.1,1)
        )
        self.site_next_bonus_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.layout.add_widget(self.site_next_bonus_label)

        self.site_upgrade_cost_label = Label(
            text="Ressources nécessaires pour évoluer : ?",
            size_hint_y=None, height=30, color=(0.35,0.3,0.0,1)
        )
        self.site_upgrade_cost_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.layout.add_widget(self.site_upgrade_cost_label)
        # --- FIN NOUVELLE SECTION ---

        # Label pour les ressources restantes à donner
        self.remaining_label = Label(text="", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.remaining_label)

        # Don (input + bouton + spinner)
        self.donation_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
        self.donation_input = TextInput(text="0", size_hint=(0.5, 1))
        self.donation_button = Button(text="Donner", size_hint=(0.5, 1), color=(0,0,0,1))
        self.donation_button.bind(on_press=self.make_donation)
        self.donation_box.add_widget(self.donation_input)
        self.donation_box.add_widget(self.donation_button)
        self.resource_spinner = Spinner(
            text="",
            values=[],
            size_hint=(0.5, 1)
        )
        self.donation_box.add_widget(self.resource_spinner)
        self.layout.add_widget(self.donation_box)

        # Ajoute un espace avant le tableau pour le descendre
        self.layout.add_widget(Widget(size_hint_y=None, height=20))
        # Section villes de l'île (juste après le don)
        self.player_cities_box = BoxLayout(orientation="vertical", size_hint_y=1)
        self.player_cities_box.add_widget(Label(text="Villes et joueurs sur l'île :", size_hint_y=None, height=30, color=(0,0,0,1)))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        header.add_widget(Label(text="Ville", size_hint=(0.25, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Joueur", size_hint=(0.25, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Ouvriers", size_hint=(0.2, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Dons", size_hint=(0.3, 1), color=(0,0,0,1)))
        self.player_cities_box.add_widget(header)
        self.layout.add_widget(self.player_cities_box)

        # Coût de l'amélioration et bonus (placés après le tableau)
        self.upgrade_cost_label = Label(text="", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.upgrade_cost_label)
        self.next_level_benefits_label = Label(text="", size_hint_y=None, height=30, color=(0,0,0,1))
        self.layout.add_widget(self.next_level_benefits_label)

        # Bouton retour
        back_button = Button(text="Retour à l'Île", size_hint=(1, None), height=50, color=(0,0,0,1))
        back_button.bind(on_press=lambda instance: self.manager.switch_view("island_view"))
        self.layout.add_widget(back_button)

        # Rafraîchit la vue au chargement
        self.refresh_view()

        self.layout.padding = [15, 120, 15, 5]  # 150px en haut, pas de marge ailleurs
        self.layout.spacing = 0.2  # Espacement minimal entre les éléments

    def on_timer_update(self, dt):
        if self.upgrade_timer_seconds > 0:
            self.upgrade_timer_seconds -= 1
            mins = self.upgrade_timer_seconds // 60
            secs = self.upgrade_timer_seconds % 60
            self.upgrade_timer_label.text = f"Timer : {mins:02d}:{secs:02d}"
        else:
            self.upgrade_timer_label.text = "Timer : 00:00"
            if self.upgrade_timer_event:
                self.upgrade_timer_event.cancel()
                self.upgrade_timer_event = None

    def start_upgrade_timer(self, seconds):
        if seconds is None:
            seconds = 0
        seconds = int(seconds)
        if seconds > 0:
            self.upgrade_timer_seconds = seconds
            if self.upgrade_timer_event:
                self.upgrade_timer_event.cancel()
            if seconds > 0:
                self.upgrade_timer_label.text = f"Timer : {seconds // 60:02d}:{seconds % 60:02d}"
                self.upgrade_timer_event = Clock.schedule_interval(self.on_timer_update, 1)
            else:
                self.upgrade_timer_label.text = "Timer : 00:00"
        else:
            self.upgrade_timer_label.text = "Timer : 00:00"

    def refresh_view(self):
        player_id = self.manager.game_data.current_player_id
        if not player_id:
            # Aucun joueur connecté, la vue ressource attend une connexion pour s’afficher.
            self.level_label.text = "Niveau du site : ?"
            self.max_workers_label.text = "Ouvriers max par joueur : ?"
            self.player_cities_box.clear_widgets()
            return
        # --- PATCH : transmettre l'id de l'île ---
        island_coords = None
        if hasattr(self, 'city_data') and self.city_data and hasattr(self.city_data, 'island_coords'):
            island_coords = self.city_data.island_coords
        elif hasattr(self.manager, 'get_active_city') and self.manager.get_active_city():
            island_coords = getattr(self.manager.get_active_city(), 'island_coords', None)
        data = self.manager.network_manager.get_resource_site_info(
            self.site_type, player_id, island_coords=island_coords
        )
        print("[DEBUG] Données reçues pour ResourceView :", data)

        if not data or data.get("error"):
            self.level_label.text = "Niveau du site : ?"
            self.max_workers_label.text = "Ouvriers max par joueur : ?"
            self.player_cities_box.clear_widgets()
            error_msg = data.get("error", ERROR_LOADING_SITE)
            self.desc_label.text = f"[color=ff0000]{error_msg}[/color]"
            self.site_next_bonus_label.text = "Bonus du site au prochain niveau : ?"
            self.site_upgrade_cost_label.text = "Ressources nécessaires pour évoluer : ?"
            self.upgrade_time_label.text = "Temps nécessaire pour upgrade : ?"
            self.start_upgrade_timer(0)
            return

        self.level_label.text = f"Niveau du site : {data.get('level', '?')}"
        max_workers = data.get('max_workers_per_city')
        if max_workers is None:
            max_workers = data.get('max_workers_per_player', 0)
        self.max_workers_label.text = f"Ouvriers max par ville : {max_workers}"

        # Mettre à jour le max du slider selon la capacité du site
        self.worker_slider.max = max_workers if max_workers is not None else 1

        # Affichage de toutes les villes de l'île
        self.player_cities_box.clear_widgets()
        # Réaffiche le label et le header à chaque refresh
        self.player_cities_box.add_widget(Label(text="Villes et joueurs sur l'île :", size_hint_y=None, height=30, color=(0,0,0,1)))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        header.add_widget(Label(text="Ville", size_hint=(0.25, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Joueur", size_hint=(0.25, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Ouvriers", size_hint=(0.2, 1), color=(0,0,0,1)))
        header.add_widget(Label(text="Dons", size_hint=(0.3, 1), color=(0,0,0,1)))
        self.player_cities_box.add_widget(header)
        all_cities = data.get("all_cities", [])
        all_donations = data.get("donations_history", {}) or data.get("donations", {})
        for city in all_cities:
            hbox = BoxLayout(orientation="horizontal", size_hint_y=None, height=22)
            hbox.add_widget(Label(text=city.get("city_name", "?"), size_hint=(0.25, 1), color=(0,0,0,1)))
            hbox.add_widget(Label(text=city.get("player", "?"), size_hint=(0.25, 1), color=(0,0,0,1)))
            hbox.add_widget(Label(text=str(city.get("workers", 0)), size_hint=(0.2, 1), color=(0,0,0,1)))
            city_don = all_donations.get(city.get("city_id"), {})
            don_str = " + ".join(f"{v} {k}" for k, v in city_don.items()) if city_don else "0"
            hbox.add_widget(Label(text=don_str, size_hint=(0.3, 1), color=(0,0,0,1)))
            self.player_cities_box.add_widget(hbox)

        # Affichage de la récolte de base sous le niveau du site
        base_yield = data.get("base_yield", 1)
        self.base_yield_label.text = f"Récolte de base : {base_yield} unité / ouvrier / seconde"

        # Affichage ouvriers
        ouvriers_ville = 0
        free_pop = None
        player_cities = data.get("player_cities", [])
        if player_cities:
            ouvriers_ville = player_cities[0].get("workers", 0)
            # Synchronise la population libre dans la ville active si possible
            active_city = self.manager.get_active_city() if hasattr(self.manager, "get_active_city") else None
            if active_city:
                # On suppose que la population libre est stockée dans player_cities[0]['free_population'] si dispo
                free_pop = player_cities[0].get("free_population", None)
                setattr(active_city, "free_population", free_pop)
        self.ouvriers_label.text = f"Ouvriers affectés par votre ville : {ouvriers_ville}"

        # -------- AFFICHAGE UPGRADE TIME/COST DU NIVEAU ACTUEL (PAS SUIVANT) --------
        level = data.get('level', 1)
        resource_type = self.resource_key
        try:
            from data.resource_sites_database import RESOURCE_SITE_LEVELS
            level_config = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(level, {})
            upgrade_time = level_config.get("upgrade_time", None)
            upgrade_cost = level_config.get("upgrade_cost", {})
        except Exception:
            upgrade_time = None
            upgrade_cost = {}

        if upgrade_time is not None:
            self.upgrade_time_label.text = f"Temps nécessaire pour upgrade : {upgrade_time} sec"
        else:
            self.upgrade_time_label.text = "Temps nécessaire pour upgrade : ?"

        # Affichage du timer d'upgrade si en cours
        if data.get("upgrade_in_progress"):
            self.start_upgrade_timer(data.get("upgrade_remaining_time", 0))
        else:
            self.start_upgrade_timer(0)

        if upgrade_cost:
            cost_str = ", ".join(f"{v} {k}" for k, v in upgrade_cost.items())
            self.site_upgrade_cost_label.text = f"Ressources nécessaires pour évoluer : {cost_str}"
        else:
            self.site_upgrade_cost_label.text = "Ressources nécessaires pour évoluer : ?"

        # Synchroniser la valeur du slider et du champ texte
        self.worker_slider.value = ouvriers_ville
        self.worker_input.text = str(ouvriers_ville)

        # --- NOUVELLE SECTION : "Développer le site de production" ---
        next_level_benefits = data.get("next_level_benefits", {})
        if not next_level_benefits or "max_workers_per_city" not in next_level_benefits:
            self.site_next_bonus_label.text = "Bonus du site au prochain niveau : ?"
        else:
            self.site_next_bonus_label.text = f"Bonus du site au prochain niveau : max_workers_per_city = {next_level_benefits['max_workers_per_city']}"

        donations = data.get("donations", {})
        remaining = {res: max(0, upgrade_cost.get(res, 0) - sum(donations.get(city_id, {}).get(res, 0) for city_id in donations)) for res in upgrade_cost}
        remaining_str = ", ".join(f"{v} {k} restants" for k, v in remaining.items())
        self.remaining_label.text = remaining_str
        self.resource_spinner.text = list(upgrade_cost.keys())[0] if upgrade_cost else ""
        self.resource_spinner.values = list(upgrade_cost.keys())

    def on_slider_value(self, instance, value):
        """Synchronise le champ texte avec la valeur du slider, n'affecte les ouvriers que si l'utilisateur interagit."""
        self.worker_input.text = str(int(value))
        # N'affecte les ouvriers que si le slider est manipulé par l'utilisateur (touch event)
        if hasattr(instance, 'touch_control') and instance.touch_control:
            self.assign_workers_active_city()

    def assign_workers(self, city_id, workers_text):
        try:
            workers = int(float(workers_text))
        except Exception:
            print("Entrée invalide")
            return
        player_id = self.manager.game_data.current_player_id
        resp = self.manager.network_manager.assign_workers(city_id, self.resource_key, workers, player_id)
        if resp and resp.get("status") == "ok":
            self.refresh_view()
        else:
            print("Erreur serveur:", resp.get("error") if resp else "Aucune réponse serveur.")

    def make_donation(self, *args):
        try:
            amount = int(float(self.donation_input.text))
        except Exception:
            show_error_popup(ERROR_INVALID_DONATION)
            return
        player_id = self.manager.game_data.current_player_id
        resource_type = self.resource_spinner.text
        # Récupérer la ville active (celle du header bar)
        active_city = self.manager.get_active_city() if hasattr(self.manager, "get_active_city") else None
        city_id = getattr(active_city, "id", None) if active_city else None
        if not active_city or not city_id:
            show_error_popup(ERROR_NO_ACTIVE_CITY)
            return
        # Calculer la bonne coordonnée d’île
        island_coords = None
        if hasattr(self, 'city_data') and self.city_data and hasattr(self.city_data, 'island_coords'):
            island_coords = self.city_data.island_coords
        elif hasattr(self.manager, 'get_active_city') and self.manager.get_active_city():
            island_coords = getattr(self.manager.get_active_city(), 'island_coords', None)
        resp = self.manager.network_manager.donate_to_resource_site(
            self.site_type, amount, player_id, resource_type,
            island_coords=island_coords, city_id=city_id
        )
        if resp and resp.get("success"):
            self.refresh_view()
        else:
            error_msg = resp.get("error") if resp else ERROR_SERVER
            show_error_popup(error_msg)

    def assign_workers_global(self):
        """
        Affecte des ouvriers à tous les villes du joueur sur ce site, selon la valeur dans le champ.
        """
        player_id = self.manager.game_data.current_player_id
        workers_text = self.worker_input.text
        try:
            workers = int(float(workers_text))
        except Exception:
            print("Entrée invalide")
            return
        # PATCH : transmettre l'id de l'île à la requête réseau
        island_coords = None
        if hasattr(self, 'city_data') and self.city_data and hasattr(self.city_data, 'island_coords'):
            island_coords = self.city_data.island_coords
        elif hasattr(self.manager, 'get_active_city') and self.manager.get_active_city():
            island_coords = getattr(self.manager.get_active_city(), 'island_coords', None)
        data = self.manager.network_manager.get_resource_site_info(self.site_type, player_id, island_coords=island_coords)
        city_ids = [city["city_id"] for city in data.get("player_cities", [])]
        for city_id in city_ids:
            self.manager.network_manager.assign_workers(city_id, self.resource_key, workers, player_id)
        self.refresh_view()

    def assign_workers_active_city(self):
        """
        Affecte des ouvriers uniquement à la ville active (celle du header bar),
        et seulement si cette ville appartient à l'île affichée.
        """
        from config.message_info import ERROR_CITY_NOT_ON_ISLAND, ERROR_NO_ACTIVE_CITY, not_enough_resource, show_error_popup
        player_id = self.manager.game_data.current_player_id
        workers_text = self.worker_input.text
        try:
            workers = int(float(workers_text))
        except Exception:
            print("Entrée invalide")
            return
        # Récupérer la ville active (celle du header bar)
        active_city = self.manager.get_active_city() if hasattr(self.manager, "get_active_city") else None
        city_id = getattr(active_city, "id", None) if active_city else None
        if not active_city or not city_id:
            show_error_popup(ERROR_NO_ACTIVE_CITY)
            return
        # Vérifier que la ville active est bien sur l'île affichée
        city_island = getattr(active_city, "island_coords", None)
        # On recalcule la coordonnée d’île attendue pour la vue
        island_coords = None
        if hasattr(self, 'city_data') and self.city_data and hasattr(self.city_data, 'island_coords'):
            island_coords = self.city_data.island_coords
        elif hasattr(self.manager, 'get_active_city') and self.manager.get_active_city():
            island_coords = getattr(self.manager.get_active_city(), 'island_coords', None)
        if city_island != island_coords:
            show_error_popup(ERROR_CITY_NOT_ON_ISLAND)
            return
        # Vérifier la population libre
        free_pop = getattr(active_city, "free_population", None)
        if free_pop is None:
            show_error_popup("Impossible de vérifier la population libre. Veuillez réessayer plus tard ou contacter un administrateur.")
            return
        if workers > free_pop:
            show_error_popup(not_enough_resource)
            return
        resp = self.manager.network_manager.assign_workers(city_id, self.resource_key, workers, player_id)
        # Synchronise la population libre avec la valeur renvoyée par le serveur
        if resp and resp.get("success"):
            free_pop_server = resp.get("free_population", None)
            if free_pop_server is not None:
                setattr(active_city, "free_population", free_pop_server)
        self.refresh_view()

    def set_city_data(self, city_data):
        """Définit la ville sélectionnée pour la vue ressource."""
        self.city_data = city_data
        # Optionnel : rafraîchir l’UI si besoin
        # self.refresh_view()

    def upgrade_site_level(self, site, elapsed_time, save_load_manager):
        """
        Améliore le niveau du site si le temps écoulé dépasse le temps d'upgrade.
        Remarque : Cette méthode est appelée par le gestionnaire de sauvegarde/chargement
        après le chargement des données du jeu, pour appliquer les upgrades en attente.
        """
        level = site.get("level", 1)
        resource_type = self.resource_key
        try:
            from data.resource_sites_database import RESOURCE_SITE_LEVELS
            level_config = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(level, {})
            upgrade_time = level_config.get("upgrade_time", 0)
        except Exception:
            upgrade_time = 0

        # Vérifie si un upgrade est en cours et si le temps écoulé depuis le début de l'upgrade
        # est supérieur ou égal au temps requis pour l'upgrade.
        if site.get("upgrade_in_progress") and site.get("upgrade_start_time"):
            elapsed = elapsed_time - site["upgrade_start_time"]
            if elapsed >= upgrade_time:
                # Passage de niveau
                site["level"] = site.get("level", 1) + 1
                site.pop("upgrade_start_time", None)
                site.pop("upgrade_time", None)
                site["donations"] = {}  # Remise à zéro SEULEMENT donations
                # NE PAS toucher à donations_history ici !
                upgraded = True
                save_load_manager.save_game()
