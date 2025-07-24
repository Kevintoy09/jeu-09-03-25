from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from config.style import apply_button_style, apply_label_style

SERVER_URL = "http://127.0.0.1:5000"

class LoginScreen(BoxLayout):
    def __init__(self, switch_view_callback, game_data, header, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.switch_view_callback = switch_view_callback
        self.game_data = game_data
        self.header = header
        self.spacing = 10
        self.padding = [20, 50, 20, 50]

        self.title = Label(text='Connexion', font_size='40sp', size_hint=(1, 0.3))
        apply_label_style(self.title)
        self.add_widget(self.title)

        self.add_widget(Label(text="Nom d'utilisateur", size_hint=(1, 0.1)))
        self.username_input = TextInput(multiline=False, height=40, size_hint_y=None)
        apply_label_style(self.username_input)
        self.add_widget(self.username_input)

        self.add_widget(Label(text='Mot de Passe', size_hint=(1, 0.1)))
        self.password_input = TextInput(password=True, multiline=False, height=40, size_hint_y=None)
        apply_label_style(self.password_input)
        self.add_widget(self.password_input)

        self.login_button = Button(text='Connexion', size_hint=(1, 0.2))
        apply_button_style(self.login_button)
        self.login_button.bind(on_press=self.login)
        self.add_widget(self.login_button)

        self.create_account_button = Button(text='Créer un Compte', size_hint=(1, 0.2))
        apply_button_style(self.create_account_button)
        self.create_account_button.bind(on_press=self.create_account)
        self.add_widget(self.create_account_button)

        self.error_label = Label(text='', color=(1, 0, 0, 1), size_hint=(1, 0.1))
        self.add_widget(self.error_label)

    def login(self, instance):
        login = self.username_input.text.strip()
        password = self.password_input.text

        if not login:
            self.error_label.text = "Nom d'utilisateur requis."
            return
        try:
            mainwidget = self.get_mainwidget()
            network_manager = getattr(mainwidget, "network_manager", None) if mainwidget else None
            if not network_manager:
                self.error_label.text = "Erreur: gestionnaire réseau absent."
                return
            response = network_manager._post("/join", {"username": login})
            # Pour une meilleure robustesse, idéalement créer une méthode network_manager.join()
            if response and response.get("player_id"):
                player_id = response.get("player_id")
                mainwidget.username = login
                mainwidget.player_id = player_id
                mainwidget.view_manager.username = login
                mainwidget.view_manager.player_id = player_id
                mainwidget.game_data.current_player_id = player_id
                mainwidget.game_data.current_player_username = login
                mainwidget.game_data.current_player_password = password

                # PATCH – ajoute le joueur si pas déjà présent
                if not mainwidget.game_data.player_manager.get_player_by_username(login):
                    from models.player import Player
                    player = Player(player_id, login, password)
                    mainwidget.game_data.player_manager.add_player(player)

                mainwidget.sync_userview()
                if hasattr(mainwidget, "buildings_manager"):
                    mainwidget.buildings_manager.set_network_config(getattr(mainwidget, "network_manager", None), login)

                # SYNC D'ABORD !
                mainwidget.sync_from_server()

                # Vérifie la liste des villes APRÈS sync
                player = mainwidget.game_data.player_manager.get_player_by_username(login)
                city_manager = mainwidget.game_data.city_manager
                owned_cities = city_manager.get_cities_for_player(player.id_player) if player else []
                if owned_cities and len(owned_cities) > 0:
                    self.switch_view_callback("world_view")
                else:
                    self.switch_view_callback("island_selection_screen")
                self.username_input.text = ""
                self.password_input.text = ""
                self.error_label.text = ""
            else:
                self.error_label.text = "Nom d'utilisateur incorrect ou indisponible."
        except Exception as e:
            import traceback
            print("[DEBUG] Exception lors de la connexion réseau :", e)
            traceback.print_exc()
            self.error_label.text = "Erreur réseau lors de la connexion."

    def get_mainwidget(self):
        parent = self.parent
        while parent is not None:
            if hasattr(parent, "sync_userview"):
                return parent
            parent = parent.parent
        return None

    def create_account(self, instance):
        self.switch_view_callback("create_account_screen")