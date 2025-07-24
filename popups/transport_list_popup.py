from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from models.transport import Transport

class TransportsListPopup(Popup):
    """
    Popup affichant la liste des transports en cours pour le joueur.
    Peut fonctionner en mode local ou connecté (client/serveur).
    """
    def __init__(self, game_data, transport_manager, network_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Transports en cours (tous ports du joueur)"
        self.size_hint = (0.85, 0.85)
        self.auto_dismiss = True
        self.game_data = game_data
        self.transport_manager = transport_manager
        self.network_manager = network_manager

        main_layout = BoxLayout(orientation='vertical', spacing=16, padding=[12, 16, 12, 12])
        self.scroll = ScrollView(size_hint=(1, 1))
        self.transports_list_layout = BoxLayout(orientation='vertical', spacing=36, size_hint_y=None)
        self.transports_list_layout.bind(minimum_height=self.transports_list_layout.setter('height'))
        self.scroll.add_widget(self.transports_list_layout)
        main_layout.add_widget(self.scroll)
        btn_fermer = Button(text="Fermer", size_hint_y=None, height=42)
        btn_fermer.bind(on_press=lambda *a: self.dismiss())
        main_layout.add_widget(btn_fermer)
        self.add_widget(main_layout)

        self.update_transports_list()
        self.event = Clock.schedule_interval(lambda dt: self.update_transports_list(), 1)

    def on_dismiss(self):
        if hasattr(self, "event") and self.event:
            self.event.cancel()

    def update_transports_list(self):
        self.transports_list_layout.clear_widgets()
        self.transports_list_layout.add_widget(Label(text="", size_hint_y=None, height=40))

        joueur = self.game_data.get_current_player()
        if not joueur:
            self.transports_list_layout.add_widget(
                Label(text="Aucun joueur courant.", size_hint_y=None, height=20)
            )
            return

        transports = []

        if self.network_manager is not None:
            response = self.network_manager.get_transports_for_player(joueur.id_player)
            if response and response.get("success"):
                transports = [Transport.from_dict(t, self.game_data) for t in response.get("transports", [])]
            else:
                self.transports_list_layout.add_widget(
                    Label(text="Erreur réseau: impossible de charger les transports.", size_hint_y=None, height=20)
                )
                return
        else:
            transports = self.transport_manager.get_transports_du_joueur(joueur)

        if not transports:
            self.transports_list_layout.add_widget(Label(text="Aucun transport en cours.", size_hint_y=None, height=20))
            return

        for t in transports:
            etat = str(getattr(t, "etat", "")).lower()
            if etat.startswith("etattransport."):
                etat = etat.split(".", 1)[-1]
            infos = ""
            progress = 0.0

            # Masquer les transports annulés
            if etat in ("annule", "cancelled"):
                continue

            if hasattr(t, "duree_chargement") and hasattr(t, "duree_transport"):
                if etat in ("waiting", "en_attente"):
                    progress = 0.0
                    infos = f"En attente ({round(t.temps_restant)}s avant chargement), puis {round(t.duree_chargement)}s chargement, {t.nb_bateaux} bateaux"
                elif etat in ("chargement", "loading"):
                    total = t.duree_chargement or 1
                    ecoule = max(0, total - t.temps_restant)
                    progress = min(1.0, ecoule / float(total))
                    infos = f"Chargement, {round(t.temps_restant)}s restant, {t.nb_bateaux} bateaux"
                elif etat in ("transport", "en_transport"):
                    total = t.duree_transport or 1
                    ecoule = max(0, total - t.temps_restant)
                    progress = min(1.0, ecoule / float(total))
                    infos = f"Transport, {round(t.temps_restant)}s restant, {t.nb_bateaux} bateaux"
                elif etat in ("retour", "return"):
                    total = t.duree_transport or 1
                    ecoule = max(0, total - t.temps_restant)
                    progress = min(1.0, ecoule / float(total))
                    infos = f"Retour, {round(t.temps_restant)}s restant, {t.nb_bateaux} bateaux"
                elif etat in ("fini", "termine", "done", "terminé", "terminated"):
                    progress = 1.0
                    infos = "Transport terminé"
                else:
                    progress = 0.0
                    infos = f"État inconnu ({t.etat})"

            bar = ProgressBar(max=1.0, value=progress, size_hint_y=None, height=20)

            row = BoxLayout(orientation="vertical", size_hint_y=None, height=130, spacing=6, padding=8)
            titre = f"[b]{getattr(t.ville_source, 'name', str(t.ville_source))}  →  {getattr(t.ville_dest, 'name', str(t.ville_dest))}[/b]"
            row.add_widget(Label(text=titre, size_hint_y=None, height=24, markup=True, halign="center", valign="middle"))

            ressources_txt = ', '.join(f"{k}: {v}" for k, v in getattr(t, 'ressources', {}).items() if v)
            row.add_widget(Label(text=ressources_txt, size_hint_y=None, height=22))
            row.add_widget(Label(text="", size_hint_y=None, height=12))
            row.add_widget(Label(text=infos, size_hint_y=None, height=20))
            row.add_widget(bar)

            boutons = BoxLayout(orientation='horizontal', size_hint_y=None, height=34, spacing=8)
            btn = Button(text="Annuler", size_hint_x=0.4, font_size=13, height=32)
            if self.network_manager:
                btn.bind(on_press=lambda inst, transport_id=t.id: self.cancel_transport_server(transport_id))
            else:
                btn.bind(on_press=lambda inst, transport=t: self.confirm_cancel_transport(transport))
            boutons.add_widget(btn)
            row.add_widget(boutons)
            self.transports_list_layout.add_widget(row)

    def cancel_transport_server(self, transport_id):
        """
        Annule un transport côté serveur,
        puis rafraîchit l'état du jeu côté client pour voir les ressources à jour.
        """
        if self.network_manager:
            self.network_manager.cancel_transport(transport_id)
            # PATCH : rafraîchit l'état du jeu (important pour les ressources)
            self.network_manager.sync_game_data(self.game_data)
            self.update_transports_list()

    def confirm_cancel_transport(self, transport):
        content = BoxLayout(orientation='vertical', spacing=8, padding=8)
        content.add_widget(Label(text="Annuler ce transport ?"))
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=6)
        yes = Button(text="Oui", size_hint_x=0.5)
        no = Button(text="Non", size_hint_x=0.5)
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        confirm_popup = Popup(title="Confirmation", content=content, size_hint=(0.45, 0.25), auto_dismiss=False)
        no.bind(on_press=lambda *a: confirm_popup.dismiss())
        yes.bind(on_press=lambda *a: (confirm_popup.dismiss(), self.transport_manager.annuler_transport(transport), self.update_transports_list()))
        confirm_popup.open()

class PortTransportsManager:
    """
    Gère le bouton et popup pour l'affichage des transports dans le port.
    """
    def __init__(self, port_popup):
        self.port_popup = port_popup

    def build_transports_list_layout(self, parent_layout):
        btn = Button(text="Voir les transports en cours", size_hint_y=None, height=38)
        btn.bind(on_press=self.show_transports_popup)
        parent_layout.add_widget(btn)

    def show_transports_popup(self, *args):
        game_data = self.port_popup.resource_manager.game_data
        transport_manager = self.port_popup.transport_manager
        network_manager = getattr(self.port_popup, "network_manager", None)
        popup = TransportsListPopup(game_data, transport_manager, network_manager=network_manager)
        popup.open()