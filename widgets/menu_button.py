from kivy.uix.button import Button
import threading
import requests
from kivy.clock import Clock

class MenuButton(Button):
    def __init__(self, **kwargs):
        # Extraire les paramètres personnalisés AVANT l'appel à super
        self.joueur_id = kwargs.pop("joueur_id", None)
        self.notification_manager = kwargs.pop("notification_manager", None)
        super().__init__(**kwargs)
        self.text = "MENU"
        self.markup = True  # Permet le BBCode pour la couleur et le gras

    def fetch_unread_count(self):
        if self.joueur_id is None:
            return 0
        try:
            url = "http://localhost:5000/get_notifications"
            response = requests.post(url, json={"joueur_id": self.joueur_id}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                # Toutes les notifications non lues
                count = sum(1 for n in notifications if not n.get("lu", False))
                return count
        except Exception:
            pass
        return 0

    def update_badge(self):
        def run():
            count = self.fetch_unread_count()
            Clock.schedule_once(lambda dt: self._set_text(count))
        threading.Thread(target=run, daemon=True).start()

    def _set_text(self, count):
        if count > 0:
            # Pastille rouge et gras
            self.text = f"MENU [b][color=ff0000]({count})[/color][/b]"
        else:
            self.text = "MENU"