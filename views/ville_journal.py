from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from datetime import datetime
import threading
import requests

class Separator(Widget):
    """Séparateur graphique horizontal (ligne grise)."""
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=1, **kwargs)
        with self.canvas:
            Color(0.7, 0.7, 0.7, 1)  # Gris clair
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

class VilleJournal(BoxLayout):
    """
    VilleJournal adapté au mode serveur :
    - Récupère les notifications depuis le serveur via l'API /get_notifications
    - Marque comme lues côté serveur via l'API /mark_notifications_read
    - Prend en compte le timestamp au format ISO (converti en datetime si besoin)
    - Utilise un thread pour ne pas bloquer l'UI lors des requêtes réseau
    """
    def __init__(self, notification_manager, joueur_id, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.notification_manager = notification_manager
        self.joueur_id = joueur_id

        # En-tête du tableau
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=32)
        header.add_widget(Label(text="Date\nHeure", bold=True, size_hint_x=None, width=60, halign="center", valign="middle", text_size=(60, 32)))
        header.add_widget(Label(text="Type", bold=True, size_hint_x=None, width=70, halign="left", valign="middle", text_size=(70, 32)))
        header.add_widget(Label(text="Informations", bold=True, size_hint_x=1, halign="left", valign="middle"))
        self.add_widget(header)

        # Scroll pour le contenu
        self.scroll = ScrollView(size_hint=(1, 1))
        # Ajout de spacing et padding pour éviter la superposition et ajouter de l'espace entre les messages
        self.log_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=12, padding=[0, 12])
        self.log_box.bind(minimum_height=self.log_box.setter('height'))
        self.scroll.add_widget(self.log_box)
        self.add_widget(self.scroll)
        self.refresh_async()

    def fetch_notifications(self):
        """Interroge le serveur pour obtenir les notifications."""
        try:
            url = "http://localhost:5000/get_notifications"
            response = requests.post(url, json={"joueur_id": self.joueur_id})
            data = response.json()
            if data.get("success"):
                return data.get("notifications", [])
        except Exception as e:
            print(f"Erreur lors du fetch des notifications: {e}")
        return []

    def mark_all_as_read(self, callback=None):
        """Demande au serveur de marquer toutes les notifications comme lues, puis appelle le callback si fourni."""
        def run():
            try:
                url = "http://localhost:5000/mark_notifications_read"
                response = requests.post(url, json={"joueur_id": self.joueur_id})
                if callback:
                    Clock.schedule_once(lambda dt: callback())
            except Exception as e:
                print(f"Erreur lors du mark_all_as_read: {e}")
                if callback:
                    Clock.schedule_once(lambda dt: callback())
        threading.Thread(target=run, daemon=True).start()

    def refresh_async(self):
        """Lance la récupération des notifications dans un thread."""
        self.log_box.clear_widgets()
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        notifications = self.fetch_notifications()
        Clock.schedule_once(lambda dt: self._update_log_box(notifications))

    def _update_log_box(self, notifications):
        self.log_box.clear_widgets()
        for i, notif in enumerate(notifications):
            # Ajout de padding dans chaque ligne pour plus d'espace
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=60, padding=[0, 10])
            dt = notif.get("timestamp")
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except Exception:
                    dt = datetime.now()
            date_line = dt.strftime("%d/%m/%y")
            hour_line = dt.strftime("%H:%M")
            date_text = f"{date_line}\n{hour_line}"
            row.add_widget(Label(
                text=date_text,
                size_hint_x=None,
                width=60,
                halign="center",
                valign="middle",
                text_size=(60, 60)
            ))
            row.add_widget(Label(
                text=notif.get("type", ""),
                size_hint_x=None,
                width=70,
                halign="left",
                valign="middle",
                text_size=(70, 60)
            ))
            desc_label = Label(
                text=notif.get("message", ""),
                size_hint_x=1,
                halign="left",
                valign="middle",
                bold=not notif.get("lu", False)
            )
            desc_label.bind(
                width=lambda instance, value: setattr(instance, 'text_size', (value, None))
            )
            row.add_widget(desc_label)
            self.log_box.add_widget(row)
            # Ajout du séparateur sauf après le dernier message
            if i < len(notifications) - 1:
                self.log_box.add_widget(Separator())

    def on_parent(self, *args):
        # Marquer toutes les notifications comme lues à l'ouverture de la popup (côté serveur),
        # puis rafraîchir la liste uniquement une fois la réponse serveur reçue
        self.mark_all_as_read(callback=self.refresh_async)