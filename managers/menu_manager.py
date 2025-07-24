"""
MenuManager : gère l'affichage et l'interaction du menu principal du jeu.
- Affiche le menu principal et ses boutons.
- Gère les notifications liées à la ville et au transport.
- Applique le style aux boutons de menu.
"""

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from config.style import apply_button_style
import requests
import threading

class MenuManager:
    def __init__(self, switch_view_callback, game_data, menu_button=None, ville_button=None):
        self.switch_view_callback = switch_view_callback
        self.menu_popup = None
        self.game_data = game_data
        self.menu_button = menu_button
        self.ville_button = ville_button
        self.journal_button = None  # Pour mettre à jour le badge asynchrone

    def open_menu(self):
        """Ouvre le menu principal du jeu."""
        if self.menu_popup and self.menu_popup.parent:
            return

        menu_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        menu_buttons = {
            "Journal": self.show_city_notifications,
            "Armée": self.show_military_reports,
            "Recherche": self.show_research_tree,
            "Message": self.show_messages,
        }

        self.journal_button = None  # reset à chaque ouverture pour éviter des erreurs

        for button_text, callback in menu_buttons.items():
            display_text = button_text.upper()
            button = Button(
                text=display_text,
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
                markup=True
            )
            apply_button_style(button)
            button.bind(on_press=lambda instance, cb=callback: self.execute_callback(cb))
            menu_layout.add_widget(button)
            if button_text == "Journal":
                self.journal_button = button

        self.menu_popup = Popup(
            title="Menu Principal",
            content=menu_layout,
            size_hint=(0.8, 0.6)
        )
        self.menu_popup.open()

        # Mise à jour asynchrone du badge sur "Journal"
        self.update_journal_badge_async()

    def update_journal_badge_async(self):
        joueur = self.game_data.get_current_player()
        if joueur is None or self.journal_button is None:
            return

        def fetch_and_update():
            try:
                url = "http://localhost:5000/get_notifications"
                response = requests.post(url, json={"joueur_id": joueur.id_player}, timeout=5)
                count = 0
                if response.status_code == 200:
                    data = response.json()
                    notifications = data.get("notifications", [])
                    count = sum(1 for n in notifications if not n.get("lu", False))
                Clock.schedule_once(lambda dt: self._set_journal_badge(count))
            except Exception as e:
                print("[MenuManager] Erreur lors du fetch unreads (journal):", e)

        threading.Thread(target=fetch_and_update, daemon=True).start()

    def _set_journal_badge(self, count):
        if self.journal_button is not None:
            if count > 0:
                self.journal_button.text = f"JOURNAL [b][color=#D80000]({count})[/color][/b]"
            else:
                self.journal_button.text = "JOURNAL"

    def execute_callback(self, callback):
        """Exécute la fonction associée à un bouton puis ferme le menu."""
        callback()
        if self.menu_popup:
            self.menu_popup.dismiss()

    def show_city_notifications(self):
        """Affiche le journal des notifications (ville, transport, etc.)."""
        from views.ville_journal import VilleJournal
        joueur = self.game_data.get_current_player()
        popup = Popup(
            title="Journal des notifications",
            content=VilleJournal(
                notification_manager=self.game_data.notification_manager,
                joueur_id=joueur.id_player if joueur else None
            ),
            size_hint=(0.8, 0.8)
        )

        def refresh_badges_on_close(*args):
            if self.menu_button:
                self.menu_button.update_badge()
            if self.ville_button:
                self.ville_button.update_badge()

        popup.bind(on_dismiss=refresh_badges_on_close)
        popup.open()

    def show_military_reports(self):
        print("[INFO] Afficher les rapports militaires.")

    def show_research_tree(self):
        print("[INFO] Afficher l'arbre de recherche.")
        self.switch_view_callback("research_view")

    def show_messages(self):
        print("[INFO] Afficher les messages.")