from models.transport import Transport
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
import math
import functools

from widgets.numpad import NumpadPopup

RESOURCES = [
    {"name": "wood", "label": "Wood"},
    {"name": "stone", "label": "Stone"},
    {"name": "cereal", "label": "cereal"},
    {"name": "iron", "label": "Iron"},
    {"name": "papyrus", "label": "Glass"},
]

CAPACITE_BATEAU = 500

class TransportPopup(Popup):
    """
    Popup de création d'un transport (local ou réseau).
    """
    def __init__(
        self,
        ville_source,
        joueur_source,
        ville_dest,
        joueur_dest,
        ships_dispo,
        ships_total,
        stock_ressources,
        vitesse_chargement,
        distance,
        ville_source_obj=None,
        ville_dest_obj=None,
        vitesse_transport=12.2,
        transport_manager=None,
        network_manager=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = "Goods Transport"
        self.size_hint = (0.85, 0.85)
        self.auto_dismiss = True

        self.ville_source_obj = ville_source_obj or ville_source
        self.ville_dest_obj = ville_dest_obj or ville_dest
        self.ville_source = ville_source
        self.joueur_source = joueur_source
        self.ville_dest = ville_dest
        self.joueur_dest = joueur_dest
        self.ships_dispo = ships_dispo
        self.ships_total = ships_total
        self.vitesse_chargement = vitesse_chargement
        self.distance = distance
        self.vitesse_transport = vitesse_transport
        self.transport_manager = transport_manager
        self.network_manager = network_manager

        fr_to_en = {"bois": "wood", "pierre": "stone", "cereale": "cereal", "fer": "iron", "verre": "papyrus"}
        self.stock_ressources = {fr_to_en.get(k, k): v for k, v in stock_ressources.items()}

        self.selected_ressources = {r["name"]: 0 for r in RESOURCES}

        self.main_layout = BoxLayout(orientation='vertical', spacing=8, padding=12)
        self._build_top()
        self.error_label = Label(text="", size_hint_y=None, height=26, color=(1, 0, 0, 1), bold=True)
        self.main_layout.add_widget(self.error_label)
        self._build_resources()
        self._build_totals()
        self._build_calculs()
        self._build_actions()
        self.add_widget(self.main_layout)

        self.update_totals_and_calculs()
        self.update_sliders_max()

    def _get_object_name(self, obj):
        if hasattr(obj, "id"):
            coords = getattr(obj, "coords", None)
            if coords:
                return f"{obj.id} ({coords[0]},{coords[1]})"
            elif hasattr(obj, "x") and hasattr(obj, "y"):
                return f"{obj.id} ({obj.x},{obj.y})"
            else:
                return obj.id
        elif hasattr(obj, "name"):
            coords = getattr(obj, "coords", None)
            if coords:
                return f"{obj.name} ({coords[0]},{coords[1]})"
            elif hasattr(obj, "x") and hasattr(obj, "y"):
                return f"{obj.name} ({obj.x},{obj.y})"
            else:
                return obj.name
        elif hasattr(obj, "username"):
            return obj.username
        else:
            return str(obj)

    def _build_top(self):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=160, spacing=0)
        vs = self._get_object_name(self.ville_source)
        js = self._get_object_name(self.joueur_source)
        vd = self._get_object_name(self.ville_dest)
        jd = self._get_object_name(self.joueur_dest)
        titre = f"Transport from {vs} ({js}) to {vd} ({jd})"
        layout.add_widget(Label(text=titre, size_hint_y=None, height=28, bold=True))
        layout.add_widget(Label(
            text=f"Ships available/total: {self.ships_dispo}/{self.ships_total}",
            size_hint_y=None, height=22, halign="left", valign="middle"
        ))
        layout.add_widget(Label(text="", size_hint_y=None, height=8))
        layout.add_widget(Label(
            text=f"Capacity per ship: {CAPACITE_BATEAU}",
            size_hint_y=None, height=22, halign="left", valign="middle"
        ))
        layout.add_widget(Label(text="", size_hint_y=None, height=8))
        layout.add_widget(Label(
            text=f"Speed: {self.vitesse_transport:.1f} u/s",
            size_hint_y=None, height=22, halign="left", valign="middle"
        ))
        layout.add_widget(Label(text="", size_hint_y=None, height=8))
        self.main_layout.add_widget(layout)

    def _build_resources(self):
        self.ressource_rows = {}
        for res in RESOURCES:
            h = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=8)
            h.add_widget(Label(text=res["label"], size_hint_x=0.21))
            slider = Slider(
                min=0,
                max=self._get_slider_max(res["name"]),
                value=0,
                step=1,
                size_hint_x=0.5,
            )
            textbox = TextInput(
                text="0",
                multiline=False,
                size_hint_x=0.18,
                input_filter="int"
            )
            slider.bind(value=functools.partial(self.on_slider_change, res["name"]))
            textbox.bind(text=functools.partial(self.on_text_change, res["name"]))
            textbox.bind(focus=functools.partial(self.on_textbox_focus, res["name"], textbox))
            h.add_widget(slider)
            h.add_widget(textbox)
            self.main_layout.add_widget(h)
            self.ressource_rows[res["name"]] = {
                "slider": slider,
                "textbox": textbox,
                "row": h,
            }

    def _get_slider_max(self, res_name):
        stock = self.stock_ressources.get(res_name, 0)
        capacite_max = self.ships_dispo * CAPACITE_BATEAU
        autres = sum(v for k, v in self.selected_ressources.items() if k != res_name)
        return min(stock, max(0, capacite_max - autres))

    def update_sliders_max(self):
        for res in RESOURCES:
            name = res["name"]
            slider = self.ressource_rows[name]["slider"]
            new_max = self._get_slider_max(name)
            slider.max = new_max
            if slider.value > new_max:
                slider.value = new_max
            textbox = self.ressource_rows[name]["textbox"]
            try:
                value = int(float(textbox.text or "0"))
            except ValueError:
                value = 0
            if value > new_max:
                textbox.text = str(int(new_max))

    def _build_totals(self):
        self.totals_label = Label(text="Total: 0", size_hint_y=None, height=28, bold=True)
        self.main_layout.add_widget(self.totals_label)

    def _build_calculs(self):
        self.calculs_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=3)
        self.nb_bateaux_label = Label(text="Ships to send = 0")
        self.duree_chargement_label = Label(text="Loading time = 0")
        self.duree_transport_label = Label(text="Transport time = 0")
        self.calculs_layout.add_widget(self.nb_bateaux_label)
        self.calculs_layout.add_widget(self.duree_chargement_label)
        self.calculs_layout.add_widget(self.duree_transport_label)
        self.main_layout.add_widget(self.calculs_layout)

    def _build_actions(self):
        boutons = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=8)
        valider = Button(text="Validate", size_hint_x=0.5)
        valider.bind(on_press=self.on_valider)
        annuler = Button(text="Cancel", size_hint_x=0.5)
        annuler.bind(on_press=lambda instance: self.dismiss())
        boutons.add_widget(valider)
        boutons.add_widget(annuler)
        self.main_layout.add_widget(boutons)

    def on_slider_change(self, res_name, instance, value):
        v = int(value)
        self.selected_ressources[res_name] = v
        row = self.ressource_rows[res_name]
        if row["textbox"].text != str(v):
            row["textbox"].text = str(v)
        self.update_sliders_max()
        self.update_totals_and_calculs()

    def on_text_change(self, res_name, instance, value):
        try:
            v = int(value)
        except Exception:
            v = 0
        v = max(0, min(self.stock_ressources.get(res_name, 0), v))
        capacite_max = self.ships_dispo * CAPACITE_BATEAU
        autres = sum(vv for k, vv in self.selected_ressources.items() if k != res_name)
        v = min(v, max(0, capacite_max - autres))
        self.selected_ressources[res_name] = v
        row = self.ressource_rows[res_name]
        if int(row["slider"].value) != v:
            row["slider"].value = v
        self.update_sliders_max()
        self.update_totals_and_calculs()

    def on_textbox_focus(self, res_name, textbox, instance, value):
        if value:  # focus gained
            def validate(new_value):
                try:
                    v = int(new_value)
                except Exception:
                    v = 0
                v = max(0, min(self.stock_ressources.get(res_name, 0), v))
                capacite_max = self.ships_dispo * CAPACITE_BATEAU
                autres = sum(vv for k, vv in self.selected_ressources.items() if k != res_name)
                v = min(v, max(0, capacite_max - autres))
                textbox.text = str(v)
                self.selected_ressources[res_name] = v
                row = self.ressource_rows[res_name]
                if int(row["slider"].value) != v:
                    row["slider"].value = v
                self.update_sliders_max()
                self.update_totals_and_calculs()
                textbox.focus = False
            popup = NumpadPopup(initial_value=textbox.text, on_validate=validate)
            popup.open()

    def update_totals_and_calculs(self):
        total = sum(self.selected_ressources.values())
        self.totals_label.text = f"Total: {total}"

        nb_bateaux = math.ceil(total / CAPACITE_BATEAU) if total > 0 else 0
        nb_bateaux = min(nb_bateaux, self.ships_dispo)
        self.nb_bateaux_label.text = f"Ships to send = {nb_bateaux}"

        duree_chargement = total / self.vitesse_chargement if self.vitesse_chargement > 0 else 0
        self.duree_chargement_label.text = f"Loading time = {duree_chargement:.1f} sec"

        duree_transport = self.distance / self.vitesse_transport if self.vitesse_transport > 0 else 0
        self.duree_transport_label.text = f"Transport time = {duree_transport:.1f} sec"
        
    def on_valider(self, instance):
        total = sum(self.selected_ressources.values())
        if self.ships_dispo <= 0:
            self.error_label.text = "No ship available for this transport."
            return
        self.error_label.text = ""
        if total == 0:
            return
        nb_bateaux = math.ceil(total / CAPACITE_BATEAU) if total > 0 else 0

        transport = Transport(
            ville_source=self.ville_source_obj,
            ville_dest=self.ville_dest_obj,
            ressources=self.selected_ressources.copy(),
            nb_bateaux=nb_bateaux,
            joueur_source=self.joueur_source,
            joueur_dest=self.joueur_dest,
            duree_chargement=total / self.vitesse_chargement if self.vitesse_chargement > 0 else 0,
            duree_transport=self.distance / self.vitesse_transport if self.vitesse_transport > 0 else 0,
        )

        if self.network_manager:
            payload = transport.to_dict()
            self.network_manager.add_transport(payload)
        elif self.transport_manager:
            self.transport_manager.ajouter_transport(transport)

        self.dismiss()