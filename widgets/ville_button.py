from kivy.uix.button import Button
import threading
import requests
from kivy.clock import Clock

class VilleButton(Button):
    def __init__(self, joueur_id=None, **kwargs):
        super().__init__(**kwargs)
        self.joueur_id = joueur_id
        self.text = "VILLE"
        self.markup = True

    def fetch_unread_ville_count(self):
        if self.joueur_id is None:
            return 0
        try:
            url = "http://localhost:5000/get_notifications"
            response = requests.post(url, json={"joueur_id": self.joueur_id}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                # Filtrer uniquement les notifications de type "ville"
                count = sum(
                    1 for n in notifications
                    if not n.get("lu", False) and n.get("type", "").lower() == "ville"
                )
                return count
        except Exception:
            pass
        return 0

    def update_badge(self):
        def run():
            count = self.fetch_unread_ville_count()
            Clock.schedule_once(lambda dt: self._set_text(count))
        threading.Thread(target=run, daemon=True).start()

    def _set_text(self, count):
        if count > 0:
            self.text = f"VILLE [b][color=ff0000]({count})[/color][/b]"
        else:
            self.text = "VILLE"