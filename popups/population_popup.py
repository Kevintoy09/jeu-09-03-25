from popups.base_popup import BasePopup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class PopulationPopup(BasePopup):
    def __init__(self, title, building_data, city, **kwargs):
        super().__init__(title, building_data, **kwargs)
        self.city = city
        self.title = f"Gestion de la population - {city.get_name()}"

        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=8, padding=8)

        # Récupération des données
        pop_max = city.get_population_limit()
        pop_actuelle = city.get_resources().get("population_total", 0)

        # Récupérer l'île de la ville
        island = None
        if city.game_data and hasattr(city.game_data, "get_island_by_coords"):
            island = city.game_data.get_island_by_coords(city.island_coords)
        # Sécurisation de l'accès aux clés
        nom_site_base = island["base_resource"] if island and isinstance(island, dict) and "base_resource" in island else "site_base"
        nom_site_avance = island["advanced_resource"] if island and isinstance(island, dict) and "advanced_resource" in island else "site_avance"
        nom_foret = "wood"
        if island and isinstance(island, dict) and "elements" in island:
            for elem in island["elements"]:
                if isinstance(elem, dict) and elem.get("type") == "forest":
                    # Si tu veux afficher le nom, garde elem["type"], mais pour le nombre, utilise "wood"
                    break

        # Population affectée
        pop_affectee = sum(city.get_workers_assigned(res) for res in city.workers_assigned.keys())
        pop_libre = pop_actuelle - pop_affectee

        # Ajout des labels
        layout.add_widget(Label(text=f"Capacité de population : {pop_max}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"Population actuelle : {int(pop_actuelle)}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"Population libre : {int(pop_libre)}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"Population affectée : {pop_affectee}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"  - Affectée académie : {city.get_workers_assigned('academy')}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"  - Affectée forêt : {city.get_workers_assigned('wood')}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"  - Affectée {nom_site_base} : {city.get_workers_assigned(nom_site_base)}", size_hint_y=None, height=30))
        layout.add_widget(Label(text=f"  - Affectée {nom_site_avance} : {city.get_workers_assigned(nom_site_avance)}", size_hint_y=None, height=30))

        # Bouton de fermeture
        close_btn = Button(text="Fermer", size_hint_y=None, height=40)
        close_btn.bind(on_press=self.dismiss)
        layout.add_widget(close_btn)

        # Ajout du layout comme unique contenu
        self.content = layout