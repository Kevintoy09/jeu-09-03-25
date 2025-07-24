from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from config.style import apply_button_style, apply_label_style
from managers.player_manager import PlayerManager

class CreateAccountScreen(BoxLayout):
    def __init__(self, switch_view_callback, game_data, **kwargs):
        super(CreateAccountScreen, self).__init__(**kwargs)
        self.switch_view_callback = switch_view_callback
        self.game_data = game_data
        self.player_manager = PlayerManager(self.game_data)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = [20, 50, 20, 50]

        self.title = Label(text='Créer un Compte', font_size='40sp', size_hint=(1, 0.3))
        apply_label_style(self.title)
        self.add_widget(self.title)

        self.add_widget(Label(text='Nom d\'utilisateur', size_hint=(1, 0.1)))
        self.username_input = TextInput(multiline=False, height=40, size_hint_y=None)
        apply_label_style(self.username_input)
        self.add_widget(self.username_input)

        self.add_widget(Label(text='Mot de Passe', size_hint=(1, 0.1)))
        self.password_input = TextInput(password=True, multiline=False, height=40, size_hint_y=None)
        apply_label_style(self.password_input)
        self.add_widget(self.password_input)

        self.add_widget(Label(text='Confirmer Mot de Passe', size_hint=(1, 0.1)))
        self.confirm_password_input = TextInput(password=True, multiline=False, height=40, size_hint_y=None)
        apply_label_style(self.confirm_password_input)
        self.add_widget(self.confirm_password_input)

        self.create_account_button = Button(text='Créer un Compte', size_hint=(1, 0.2))
        apply_button_style(self.create_account_button)
        self.create_account_button.bind(on_press=self.create_account)
        self.add_widget(self.create_account_button)

        self.back_to_login_button = Button(text='Retour à la Connexion', size_hint=(1, 0.2))
        apply_button_style(self.back_to_login_button)
        self.back_to_login_button.bind(on_press=self.back_to_login)
        self.add_widget(self.back_to_login_button)

    def create_account(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        confirm_password = self.confirm_password_input.text

        if password != confirm_password:
            print("Les mots de passe ne correspondent pas.")
            return

        self.player_manager.create_account(username, password)
        self.switch_view_callback('login_screen')

    def back_to_login(self, instance):
        self.switch_view_callback('login_screen')