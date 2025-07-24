from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from models.transport import open_transport_popup_generic
from models.transport import calculer_distance
import requests

class CityPopup:
    def __init__(self, game_data, manager, network_manager=None):
        self.game_data = game_data
        self.manager = manager
        self.popup = None
        self.selected_city = None
        self.network_manager = network_manager  # Permet passage à open_transport_popup_generic

    def open_city_popup(self, city):
        self.selected_city = city
        self.popup = Popup(title=f"Informations de {city.id}", size_hint=(0.8, 0.8))
        content = BoxLayout(orientation='vertical')

        city_info = GridLayout(cols=2)
        city_info.add_widget(Label(text="ID de la ville:"))
        city_info.add_widget(Label(text=city.id))
        city_info.add_widget(Label(text="Nom de la ville:"))
        city_info.add_widget(Label(text=city.name))

        player_id = city.owner
        is_unoccupied = not player_id  # True si None ou ''

        if not is_unoccupied:
            try:
                player = self.game_data.player_manager.get_player(player_id) if player_id else None
                city_info.add_widget(Label(text="Nom du joueur:"))
                city_info.add_widget(Label(text=player.username))
                city_info.add_widget(Label(text="Alliance:"))
                city_info.add_widget(Label(text="Aucune"))
                city_info.add_widget(Label(text="Nombre de points:"))
                city_info.add_widget(Label(text=str(player.get_points())))
                city_info.add_widget(Label(text="Points militaires:"))
                city_info.add_widget(Label(text=str(player.get_military_points())))
            except ValueError as e:
                print(e)
                self.show_error_message(str(e))
                return

        content.add_widget(city_info)
        action_buttons = GridLayout(cols=1)

        if is_unoccupied:
            # Vérifie les conditions de colonisation AVANT d'afficher le bouton
            current_player_id = self.game_data.current_player_id
            if not current_player_id:
                action_buttons.add_widget(Label(text="Aucun joueur connecté."))
            else:
                try:
                    player = self.game_data.player_manager.get_player(current_player_id)
                except Exception:
                    action_buttons.add_widget(Label(text="Joueur introuvable."))
                    player = None
                if player:
                    city_manager = self.game_data.city_manager
                    owned_cities = city_manager.get_cities_for_player(player.id_player)

                    ambassade = None
                    for city in owned_cities:
                        for building in getattr(city, "buildings", []):
                            if building is None:
                                continue
                            if "ambassade" in getattr(building, "name", "").lower():
                                ambassade = building
                                break
                        if ambassade:
                            break

                    niveau_ambassade = getattr(ambassade, "level", 1) if ambassade else 0
                    colonies_possedees = len(owned_cities)

                    if not ambassade:
                        action_buttons.add_widget(Label(text="Construisez une Ambassade pour coloniser."))
                    elif colonies_possedees >= niveau_ambassade:
                        action_buttons.add_widget(Label(
                            text=f"Limite de colonies atteinte ({colonies_possedees}/{niveau_ambassade}). Améliorez l'Ambassade."
                        ))
                    else:
                        button = Button(text="Coloniser cette ville")
                        button.bind(on_press=self.colonize_city)
                        action_buttons.add_widget(button)
        else:
            buttons = [
                ("Entrer dans la ville", self.enter_city),
                ("Voir la ville", self.view_city),
                ("Envoyer un message", self.send_message),
                ("Transporter des marchandises", self.transport_goods),
                ("Protéger la ville", self.protect_city),
                ("Envoyer un espion", self.send_spy),
                ("Attaquer la ville", self.attack_city),
                ("Attaquer le port", self.attack_port),
                ("Conquérir la ville", self.conquer_city),
            ]
            for button_text, button_action in buttons:
                button = Button(text=button_text)
                button.bind(on_press=button_action)
                action_buttons.add_widget(button)

        content.add_widget(action_buttons)
        self.popup.content = content
        self.popup.open()

    # --- Bouton de colonisation pour villes inoccupées ---
    def colonize_city(self, instance):
        current_player_id = self.game_data.current_player_id
        player = self.game_data.player_manager.get_player(current_player_id)
        city_manager = self.game_data.city_manager

        # Log toutes les villes du joueur
        owned_cities = city_manager.get_cities_for_player(player.id_player)
        print("DEBUG colonize_city: villes du joueur =", [c.id for c in owned_cities])

        ambassade = None
        for city in owned_cities:
            for building in getattr(city, "buildings", []):
                if building is None:
                    continue
                print("DEBUG FOUND:", getattr(building, "name", "??"))
                if "ambassade" in getattr(building, "name", "").lower():
                    ambassade = building
                    break
            if ambassade:
                break
        print("DEBUG ambassade trouvée:", ambassade)

        if not ambassade:
            self.show_error_message(
                "Vous devez d'abord débloquer la recherche \"Expansion\" dans l'Academy puis construire une Ambassade dans une de vos villes pour coloniser une nouvelle ville."
            )
            return

        niveau_ambassade = getattr(ambassade, "level", 1)
        colonies_possedees = len(owned_cities)
        print("DEBUG niveau ambassade:", niveau_ambassade, "| colonies possédées:", colonies_possedees)

        if colonies_possedees >= niveau_ambassade:
            self.show_error_message(
                f"Votre Ambassade est de niveau {niveau_ambassade} : vous avez déjà atteint la limite actuelle de colonies ({colonies_possedees}/{niveau_ambassade}).\n"
                "Pour coloniser une nouvelle ville, améliorez l'Ambassade."
            )
            return

        self.show_colony_creation_popup(player)

    def show_colony_creation_popup(self, player):
        """Affiche un popup pour nommer et créer une nouvelle colonie."""
        popup = Popup(title="Coloniser la ville", size_hint=(0.7, 0.4))
        layout = BoxLayout(orientation='vertical', spacing=10, padding=16)
        layout.add_widget(Label(text="Entrez un nom pour votre nouvelle colonie :"))
        name_input = TextInput(hint_text="Nom de la colonie", multiline=False)

        layout.add_widget(name_input)
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)
        create_button = Button(text="Coloniser")
        cancel_button = Button(text="Annuler")

        def create_colony_action(instance):
            colony_name = name_input.text.strip()
            if not colony_name:
                self.show_error_message("Le nom de la colonie ne peut pas être vide.")
                return
            new_city = self.game_data.city_manager.create_new_city(player, colony_name, base_city=self.selected_city)
            if new_city:
                popup.dismiss()
                self.popup.dismiss()
                city_id = getattr(new_city, "id", None)
                city = self.game_data.city_manager.get_city_by_id(city_id)
                self.selected_city = city

                # Synchronisation côté serveur
                username = player.username  # ou adapte selon ton modèle
                payload = {"username": username, "city_id": city_id}
                try:
                    resp = requests.post("http://localhost:5000/select_city", json=payload)
                    print("[DEBUG][SYNC COLONIZATION]", resp.json())
                except Exception as e:
                    print("[ERROR][SYNC COLONIZATION]", e)

                # Recharge l'état du jeu
                response = requests.get("http://localhost:5000/get_state")
                if response.ok:
                    state = response.json()
                    self.game_data.from_dict(state)
                    self.game_data.current_player_id = player.id_player
                    print("[DEBUG] Etat du jeu rafraîchi après colonisation.")
                else:
                    print("[ERREUR] Impossible de rafraîchir l'état du jeu après colonisation.")

                self.show_success_message(
                    f"La colonie \"{colony_name}\" a été fondée avec succès !\n"
                    "Vous pouvez maintenant la gérer comme une ville normale."
                )
                self.manager.switch_view("city_view", data=city)
            else:
                self.show_error_message("Impossible de coloniser cette ville. Vérifiez les conditions.")
                
        create_button.bind(on_press=create_colony_action)
        cancel_button.bind(on_press=lambda x: popup.dismiss())

        button_layout.add_widget(create_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)
        popup.content = layout
        popup.open()

    # --- Actions classiques pour villes occupées ---
    def enter_city(self, instance):
        current_player_id = self.game_data.current_player_id
        city_manager = self.game_data.city_manager
        city = city_manager.get_city_by_id(getattr(self.selected_city, "id", None))
        if city and city.owner == current_player_id:
            self.popup.dismiss()
            self.manager.switch_view("city_view", data=city)
        else:
            self.show_error_message("Cette ville ne vous appartient pas, vous ne pouvez pas contrôler cette ville.")

    def view_city(self, instance):
        self.popup.dismiss()
        # Correction ici : passer la ville en argument nommé
        self.manager.switch_view("view_city", city_data=self.selected_city)

    def send_message(self, instance):
        self.popup.dismiss()
        self.show_message_popup()

    def show_message_popup(self):
        message_popup = Popup(title="Envoyer un message", size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical')
        message_input = TextInput(hint_text="Entrez votre message ici...")
        send_button = Button(text="Envoyer")
        send_button.bind(on_press=lambda instance: self.send_message_to_player(message_input.text, message_popup))
        content.add_widget(message_input)
        content.add_widget(send_button)
        message_popup.content = content
        message_popup.open()

    def send_message_to_player(self, message, popup):
        if message:
            print(f"Message envoyé à {self.selected_city.owner}: {message}")
            popup.dismiss()
        else:
            self.show_error_message("Le message ne peut pas être vide.")

    def transport_goods(self, instance):
        self.popup.dismiss()
        ville_dest = self.selected_city
        current_player_id = self.game_data.current_player_id
        player = self.game_data.player_manager.get_player(current_player_id)
        city_manager = self.game_data.city_manager
        # On propose comme origine uniquement les villes du joueur courant qui ont un port (comme PortPopup)
        cities = []
        for city in city_manager.get_cities_for_player(player.id_player):
            for b in getattr(city, "buildings", []):
                if b and getattr(b, "name", "").lower() == "port" and getattr(b, "level", 1) >= 1:
                    if city != ville_dest:
                        cities.append(city)
                    break

        if not cities:
            self.show_error_message("Aucune ville d'expédition disponible pour le transport.")
            return

        popup = Popup(title="Choisir la ville d'expédition", size_hint=(0.7, 0.7))
        layout = BoxLayout(orientation='vertical', spacing=8, padding=8)
        layout.add_widget(Label(text="Choisissez la ville d'expédition (origine) :"))

        city_buttons = GridLayout(cols=1, spacing=5, size_hint_y=None)
        city_buttons.bind(minimum_height=city_buttons.setter('height'))
        for city in cities:
            btn = Button(text=f"{city.id}", size_hint_y=None, height=40)
            btn.bind(on_press=lambda inst, c=city: self.open_transport_popup(c, ville_dest, popup))
            city_buttons.add_widget(btn)

        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(city_buttons)
        layout.add_widget(scroll)

        close_btn = Button(text="Annuler", size_hint_y=None, height=44)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(close_btn)
        popup.content = layout
        popup.open()

    def open_transport_popup(self, city_source, city_dest, selection_popup):
        selection_popup.dismiss()
        player = self.game_data.player_manager.get_player(city_source.owner)
        port_data = None  # Pas de port_data ici (optionnel)
        joueur_dest = self.game_data.player_manager.get_player(city_dest.owner) if city_dest.owner else None
        # Passage du network_manager dans l'appel avec log de debug
        print("[DEBUG][CityPopup.open_transport_popup] self.network_manager =", self.network_manager, "id =", id(self.network_manager))
        open_transport_popup_generic(
            from_city=city_source,
            city_dest=city_dest,
            player=player,
            port_data=port_data,
            transport_manager=self.manager.transport_manager,
            network_manager=self.network_manager,
            joueur_dest=joueur_dest,
            parent_popup=None
        )

    def protect_city(self, instance):
        self.show_error_message("Fonctionnalité à développer.")

    def send_spy(self, instance):
        self.show_error_message("Fonctionnalité à développer.")

    def attack_city(self, instance):
        self.show_error_message("Fonctionnalité à développer.")

    def attack_port(self, instance):
        self.show_error_message("Fonctionnalité à développer.")

    def conquer_city(self, instance):
        self.show_error_message("Fonctionnalité à développer.")

    def show_success_message(self, message):
        success_popup = Popup(title="Succès", size_hint=(0.6, 0.3))
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close_button = Button(text="Fermer")
        close_button.bind(on_press=lambda instance: success_popup.dismiss())
        content.add_widget(close_button)
        success_popup.content = content
        success_popup.open()

    def show_error_message(self, message):
        error_popup = Popup(title="Erreur", size_hint=(0.6, 0.3))
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close_button = Button(text="Fermer")
        close_button.bind(on_press=lambda instance: error_popup.dismiss())
        content.add_widget(close_button)
        error_popup.content = content
        error_popup.open()