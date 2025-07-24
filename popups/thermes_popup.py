from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from .base_popup import BasePopup
from kivy.uix.button import Button
from kivy.clock import Clock
import random
import requests

def make_adaptive_label(text, min_height=22, **kwargs):
    if 'halign' not in kwargs:
        kwargs['halign'] = 'left'
    if 'valign' not in kwargs:
        kwargs['valign'] = 'middle'
    lbl = Label(
        text=text,
        markup=True,
        size_hint_y=None,
        **kwargs
    )
    lbl.bind(
        width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
        texture_size=lambda instance, value: setattr(instance, 'height', max(value[1], min_height)),
    )
    return lbl

class ThermesPopup(BasePopup):
    def refresh_dynamic_info(self):
        # Utilise le layout central du BasePopup pour le contenu dynamique
        if hasattr(self, "dynamic_info_layout") and self.dynamic_info_layout is not None:
            parent = self.dynamic_info_layout.parent
            if parent:
                parent.remove_widget(self.dynamic_info_layout)
            self.dynamic_info_layout = None
        # Reconstruit l'affichage dynamique dans le layout principal
        self.add_dynamic_info(self.main_layout)
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_view=None,
        city_id=None,
        population_manager=None,
        **kwargs
    ):
        kwargs.pop("manager", None)
        kwargs.pop("city_id", None)
        kwargs.pop("city_view", None)
        kwargs.pop("custom_content_callback", None)

        self.city_id = city_id
        self.city_view = city_view
        self.building_data = building_data
        self.update_all_callback = update_all_callback
        self.buildings_manager = buildings_manager
        self.population_manager = population_manager

        if custom_content_callback is None:
            custom_content_callback = lambda layout: self.add_dynamic_info(self.main_layout)

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=custom_content_callback,
            city_id=city_id,
            city_view=city_view,
            **kwargs
        )

    def get_city(self):
        if hasattr(self, "city_id") and self.city_id is not None:
            game_data = getattr(self.buildings_manager, "game_data", None)
            if game_data and hasattr(game_data, "city_manager"):
                city = game_data.city_manager.get_city_by_id(self.city_id)
                print(f"[DEBUG][ThermesPopup] get_city : id={getattr(city, 'id', None)}, instance_id={id(city)}")
                return city
        return None

    def add_dynamic_info(self, layout):
        city = self.get_city()
        if not city:
            print(f"[DEBUG] Ville non trouvée pour le popup Thermes (city_id={self.city_id})")
            return
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=300, padding=30, spacing=30)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))
        self.dynamic_info_layout.add_widget(make_adaptive_label("Thermes de la ville", min_height=40, bold=True))
        thermes_capacity = 0
        satisfaction_bonus = 0
        level = 0
        for b in city.get_buildings():
            if b and b.get_name() == "Thermes" and b.get_status() == "Terminé":
                level = b.get_level()
                effect = b.effect if hasattr(b, "effect") else {}
                thermes_capacity = effect.get("cleanliness_capacity", 0)
                satisfaction_bonus = effect.get("satisfaction_bonus", 0)
                break
        self.dynamic_info_layout.add_widget(make_adaptive_label(f"Niveau des Thermes : {level}", min_height=30))
        self.dynamic_info_layout.add_widget(make_adaptive_label(f"Capacité de propreté : {thermes_capacity}", min_height=30))
        resources = city.get_resources()
        pop_value = int(round(resources.get('population_total', 0)))
        self.dynamic_info_layout.add_widget(make_adaptive_label(f"Population actuelle : {pop_value}", min_height=30))
        self.dynamic_info_layout.add_widget(make_adaptive_label(f"Bonus satisfaction : +{satisfaction_bonus}", min_height=30))
        satisfaction = resources.get("satisfaction", 0)
        self.dynamic_info_layout.add_widget(make_adaptive_label(f"Satisfaction totale de la ville : {satisfaction}", min_height=30))
        hygiene_percent = resources.get("hygiene_percent", 100)
        if hygiene_percent > 100:
            etat = "[color=00cc00]Excellente hygiène[/color] (+5 satisfaction)"
        elif hygiene_percent >= 70:
            etat = "[color=00cc00]Bonne hygiène[/color]"
        elif hygiene_percent >= 50:
            etat = "[color=ffaa00]Attention : hygiène insuffisante[/color]"
        else:
            etat = "[color=ff0000]Danger : risque élevé de peste ![/color]"
        self.dynamic_info_layout.add_widget(make_adaptive_label(
            f"Hygiène de la population : {hygiene_percent}%\n{etat}",
            min_height=40
        ))
        population = int(resources.get("population_total", 0))
        population_manager = getattr(self, "population_manager", None)
        if population_manager and hasattr(population_manager, "calculate_population_limit"):
            population_max = population_manager.calculate_population_limit(city)
            print(f"[DEBUG][ThermesPopup] population_max calculé via population_manager = {population_max}")
        else:
            print(f"[ERREUR][ThermesPopup] population_manager absent ou non conforme !")
            population_max = 0

        # Barre de progression personnalisée
        class PopulationBar(Widget):
            def __init__(self, population, population_max, thermes_capacity=0, **kwargs):
                super().__init__(**kwargs)
                self.population = population
                self.population_max = population_max
                self.thermes_capacity = thermes_capacity
                self.size_hint = (0.95, None)
                self.height = 28
                self.bind(pos=self.update_bar, size=self.update_bar)

            def update_bar(self, *args):
                self.canvas.clear()
                with self.canvas:
                    # Cadre gris (capacité max)
                    Color(0.7, 0.7, 0.7, 1)
                    Rectangle(pos=(self.x, self.y), size=(self.width, self.height))
                    # Barre bleue (population actuelle)
                    Color(0.2, 0.4, 1, 1)
                    fill_w = self.width * min(self.population / self.population_max, 1.0) if self.population_max > 0 else 0
                    Rectangle(pos=(self.x, self.y), size=(fill_w, self.height))
                    # Curseur capacité de propreté (vert)
                    print(f"[DEBUG][PopulationBar] thermes_capacity={self.thermes_capacity}, population_max={self.population_max}")
                    if self.population_max > 0:
                        cap_ratio = min(self.thermes_capacity / self.population_max, 1.0)
                        cap_x = self.x + self.width * cap_ratio
                        print(f"[DEBUG][PopulationBar] cap_ratio={cap_ratio}, cap_x={cap_x}, self.x={self.x}, self.width={self.width}")
                        Color(0, 1, 0, 1)
                        Rectangle(pos=(cap_x-2, self.y), size=(4, self.height))

        # Ajout du label de capacité de propreté au-dessus de la barre, aligné sur le curseur
        if population_max > 0:
            cap_ratio = min(thermes_capacity / population_max, 1.0)
            # Hauteur minimale pour coller le label à la barre
            cap_label_layout = FloatLayout(size_hint_y=None, height=2)
            pos_x = cap_ratio if cap_ratio <= 1.0 else 1.0
            lbl_cap = Label(text=str(thermes_capacity), font_size=12, size_hint=(None, None), size=(40, 12), pos_hint={"x":pos_x-0.05, "y":0})
            cap_label_layout.add_widget(lbl_cap)
            self.dynamic_info_layout.add_widget(cap_label_layout)
        # Barre de progression
        pop_bar = PopulationBar(population, population_max, thermes_capacity=thermes_capacity)
        self.dynamic_info_layout.add_widget(pop_bar)
        # Label max collé à la barre
        max_label_layout = FloatLayout(size_hint_y=None, height=2)
        lbl_max = Label(text=f"Max : {population_max}", font_size=12, size_hint=(None, None), size=(60, 12), pos_hint={"right":1, "y":0})
        max_label_layout.add_widget(lbl_max)
        self.dynamic_info_layout.add_widget(max_label_layout)

        # Ligne colorée représentant les 4 zones d'hygiène
        class HygieneZonesLine(Widget):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (0.95, None)
                self.height = 12
                self.bind(pos=self.update_line, size=self.update_line)

            def update_line(self, *args):
                self.canvas.clear()
                with self.canvas:
                    w = self.width
                    h = self.height
                    # Zone excellente hygiène (>100%)
                    Color(0, 0.7, 0, 1)
                    Rectangle(pos=(self.x, self.y), size=(w * 0.25, h))
                    # Zone bonne hygiène (70-100%)
                    Color(0, 1, 0, 1)
                    Rectangle(pos=(self.x + w * 0.25, self.y), size=(w * 0.25, h))
                    # Zone attention (50-70%)
                    Color(1, 0.7, 0, 1)
                    Rectangle(pos=(self.x + w * 0.5, self.y), size=(w * 0.2, h))
                    # Zone danger (<50%)
                    Color(1, 0, 0, 1)
                    Rectangle(pos=(self.x + w * 0.7, self.y), size=(w * 0.3, h))

        hygiene_line = HygieneZonesLine()
        self.dynamic_info_layout.add_widget(hygiene_line)
        # Ajout des labels de seuils sous la ligne
        seuils_layout = FloatLayout(size_hint_y=None, height=18)
        # Positionnement horizontal des labels
        lbl_100 = Label(text="100%", font_size=12, size_hint=(None, None), size=(40, 18), pos_hint={"x":0.23, "y":0})
        lbl_70 = Label(text="70%", font_size=12, size_hint=(None, None), size=(40, 18), pos_hint={"x":0.48, "y":0})
        lbl_50 = Label(text="50%", font_size=12, size_hint=(None, None), size=(40, 18), pos_hint={"x":0.68, "y":0})
        seuils_layout.add_widget(lbl_100)
        seuils_layout.add_widget(lbl_70)
        seuils_layout.add_widget(lbl_50)
        self.dynamic_info_layout.add_widget(seuils_layout)
        # Le label legend est supprimé pour alléger l'affichage
        self.cure_button = Button(
            text="Soigner la peste",
            size_hint_y=None,
            height=50,
            disabled=True,
        )
        gold = resources.get("gold", 0)
        has_plague = getattr(city, "has_plague", False)
        self.cure_button.bind(on_release=lambda instance: self.try_cure_plague(city, population, gold, hygiene_percent))
        self.dynamic_info_layout.add_widget(self.cure_button)
        self.cure_cooldown = False
        self.update_cure_button(has_plague, hygiene_percent, gold, population)
        # LOG DEBUG : état du parent avant manipulation
        print(f"[DEBUG][ThermesPopup] Avant ajout layout : parent={layout}, enfants={len(layout.children) if hasattr(layout, 'children') else 'N/A'}")
        if hasattr(layout, 'children'):
            for child in list(layout.children):
                print(f"[DEBUG][ThermesPopup] Enfant : {child}, type={type(child)}, is_dynamic_info_layout={getattr(child, 'is_dynamic_info_layout', False)}")
                if isinstance(child, BoxLayout) and getattr(child, 'is_dynamic_info_layout', False):
                    print(f"[DEBUG][ThermesPopup] Suppression ancien layout dynamique : {child}")
                    layout.remove_widget(child)
        # Marque le layout dynamique pour le retrouver facilement
        self.dynamic_info_layout.is_dynamic_info_layout = True
        print(f"[DEBUG][ThermesPopup] Ajout du nouveau layout dynamique : {self.dynamic_info_layout}")
        layout.add_widget(self.dynamic_info_layout)
        print(f"[DEBUG][ThermesPopup] Après ajout layout : enfants={len(layout.children) if hasattr(layout, 'children') else 'N/A'}")
        if has_plague:
            self.dynamic_info_layout.add_widget(make_adaptive_label("[color=ff0000][b]PESTE ACTIVE ![/b][/color]", min_height=30))
        else:
            self.dynamic_info_layout.add_widget(make_adaptive_label("[color=00cc00]Aucune peste dans la ville[/color]", min_height=30))
        print(f"[DEBUG] Etat de peste dans le popup Thermes pour {city.get_name()} : {city.has_plague} (id={id(city)})")

    def update_cure_button(self, has_plague, hygiene_percent, gold, population):
        can_cure = (
            has_plague
            and hygiene_percent >= 100
            and gold >= 2 * population
            and not self.cure_cooldown
        )
        self.cure_button.disabled = not can_cure
        if not has_plague:
            self.cure_button.text = "Soigner la peste (pas de peste)"
        elif hygiene_percent < 100:
            self.cure_button.text = "Soigner la peste (hygiène insuffisante)"
        elif gold < 2 * population:
            self.cure_button.text = f"Soigner la peste (or insuffisant : {2*population})"
        elif self.cure_cooldown:
            self.cure_button.text = "Nouvelle tentative dans 5s…"
        else:
            self.cure_button.text = f"Soigner la peste (coût : {2*population} or, 25 % de réussite)"
        print(f"[DEBUG] update_cure_button : has_plague={has_plague}, hygiene_percent={hygiene_percent}, gold={gold}, population={population}, cooldown={self.cure_cooldown}")

    def try_cure_plague(self, city, population, gold, hygiene_percent):
        if self.cure_cooldown:
            return
        main_city = None
        if hasattr(self.buildings_manager, "game_data") and hasattr(self.buildings_manager.game_data, "city_manager"):
            city_manager = self.buildings_manager.game_data.city_manager
            main_city = city_manager.get_city_by_id(city.id)
        if not main_city:
            print(f"[DEBUG] Impossible de trouver l'instance centrale de la ville pour la guérison (id={getattr(city, 'id', None)})")
            return
        if not main_city.has_plague or hygiene_percent < 100 or gold < 2 * population:
            print(f"[DEBUG] Conditions non réunies pour soigner la peste : has_plague={main_city.has_plague}, hygiene_percent={hygiene_percent}, gold={gold}, population={population}")
            return
        main_city.resources["gold"] -= 2 * population
        if random.random() < 0.95:
            main_city.has_plague = False
            print(f"[DEBUG] Guérison réussie : has_plague={main_city.has_plague} (id={id(main_city)})")
            self.show_result("Succès ! La peste a disparu.", color=(0,1,0,1))
            self.update_cure_button(False, hygiene_percent, main_city.resources["gold"], population)
            self.update_all_callback()
            if hasattr(self.buildings_manager, "game_data"):
                self.buildings_manager.game_data.save_load_manager.save_game()
            # Ajout : synchronisation serveur
            result = self.send_cure_plague_to_server(main_city.id)
            print(f"[DEBUG] Résultat serveur cure_plague : {result}")
            # Rafraîchit le contenu du popup sans le fermer
            self.refresh_dynamic_info()
        else:
            print(f"[DEBUG] Guérison échouée : has_plague={main_city.has_plague} (id={id(main_city)})")
            self.show_result("Échec… La peste persiste.", color=(1,0,0,1))
            self.cure_cooldown = True
            self.update_cure_button(True, hygiene_percent, main_city.resources["gold"], population)
            Clock.schedule_once(lambda dt: self.reset_cure_cooldown(main_city), 5)
        self.update_all_callback()

    def reset_cure_cooldown(self, city):
        self.cure_cooldown = False
        resources = city.get_resources()
        self.update_cure_button(
            city.has_plague,
            resources.get("hygiene_percent", 100),
            resources.get("gold", 0),
            resources.get("population_total", 0)
        )

    def show_result(self, message, color=(1,1,1,1)):
        if hasattr(self, "result_label"):
            self.dynamic_info_layout.remove_widget(self.result_label)
        self.result_label = Label(
            text=message,
            color=color,
            size_hint_y=None,
            height=30
        )
        self.dynamic_info_layout.add_widget(self.result_label)
        Clock.schedule_once(lambda dt: self.remove_result_label(), 3)

    def remove_result_label(self):
        if hasattr(self, "result_label"):
            self.dynamic_info_layout.remove_widget(self.result_label)
            del self.result_label

    def send_cure_plague_to_server(self, city_id):
        url = "http://localhost:5000/cure_plague"
        data = {"city_id": city_id}
        try:
            response = requests.post(url, json=data)
            result = response.json()
            print("[DEBUG][Serveur] Réponse cure_plague :", result)
            return result
        except Exception as e:
            print("[DEBUG][Serveur] Erreur d'appel cure_plague :", e)
            return None