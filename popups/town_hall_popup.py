from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from .base_popup import BasePopup
from models.constants import NORMAL_CONSUMPTION_RATE
from kivy.logger import Logger
from kivy.uix.textinput import TextInput
from popups.satisfaction_popup import SatisfactionPopup

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

class TownHallPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback=None,
        buildings_manager=None,
        custom_content_callback=None,
        city_view=None,
        city_id=None,
        population_manager=None,
        network_manager=None,
        **kwargs
    ):
        self.city_view = city_view
        self.population_manager = population_manager
        self.city_id = city_id
        self.network_manager = network_manager

        for key in [
            "city_id", "population_manager", "network_manager", "city_view"
        ]:
            kwargs.pop(key, None)

        if custom_content_callback is None:
            custom_content_callback = self.add_dynamic_info

        super().__init__(
            title,
            building_data,
            update_all_callback,
            buildings_manager,
            custom_content_callback=custom_content_callback,
            city_view=city_view,
            city_id=city_id,
            network_manager=network_manager,
            **kwargs
        )

    def get_city(self):
        if self.city_view and hasattr(self.city_view, "city_data"):
            return self.city_view.city_data
        return None

    def add_dynamic_info(self, layout):
        try:
            self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
            self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))
            label_height = 22
            rename_height = 30

            # Renommer la ville
            rename_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=rename_height)
            rename_label = make_adaptive_label("Nom de la ville :", min_height=rename_height, size_hint_x=0.45)
            city = self.get_city()
            city_name = city.name if city else ""
            self.rename_input = TextInput(
                text=city_name,
                multiline=False,
                size_hint_x=0.2,
                size_hint_y=None,
                height=rename_height
            )
            rename_btn = Button(text="Renommer", size_hint_x=0.15, size_hint_y=None, height=rename_height)
            rename_btn.bind(on_press=self.rename_city)
            rename_layout.add_widget(rename_label)
            rename_layout.add_widget(self.rename_input)
            rename_layout.add_widget(rename_btn)
            self.dynamic_info_layout.add_widget(rename_layout)

            # Labels d'infos dynamiques
            self.population_growth_label = make_adaptive_label("", min_height=label_height)
            self.current_population_label = make_adaptive_label("", min_height=label_height)
            self.max_population_label = make_adaptive_label("", min_height=label_height)
            self.nourished_population_label = make_adaptive_label("", min_height=label_height)
            self.remaining_population_label = make_adaptive_label("", min_height=label_height)
            self.cereal_consumption_label = make_adaptive_label("", min_height=label_height)
            self.per_capita_cereal_consumption_label = make_adaptive_label("", min_height=label_height)
            self.satisfaction_label = make_adaptive_label("", min_height=label_height)

            self.dynamic_info_layout.add_widget(self.population_growth_label)
            self.dynamic_info_layout.add_widget(self.current_population_label)
            self.dynamic_info_layout.add_widget(self.max_population_label)
            self.dynamic_info_layout.add_widget(self.nourished_population_label)
            self.dynamic_info_layout.add_widget(self.remaining_population_label)
            self.dynamic_info_layout.add_widget(self.cereal_consumption_label)
            self.dynamic_info_layout.add_widget(self.per_capita_cereal_consumption_label)
            self.dynamic_info_layout.add_widget(self.satisfaction_label)

            satisfaction_btn = Button(text="Détail satisfaction", size_hint_y=None, height=30)
            satisfaction_btn.bind(on_press=self.open_satisfaction_popup)
            self.dynamic_info_layout.add_widget(satisfaction_btn)

            # Bouton pour ouvrir le popup population
            population_btn = Button(text="Gestion population", size_hint_y=None, height=30)
            population_btn.bind(on_press=self.open_population_popup)
            self.dynamic_info_layout.add_widget(population_btn)

            self.add_gold_rate_selector(self.dynamic_info_layout)

            self.gold_growth_label = make_adaptive_label("", min_height=label_height+2)
            self.gold_growth_label.markup = True
            self.dynamic_info_layout.add_widget(self.gold_growth_label)

            layout.add_widget(self.dynamic_info_layout)
            self.update_town_hall_info()
            self.town_hall_info_event = Clock.schedule_interval(self.update_town_hall_info, 1)
        except Exception as e:
            Logger.error(f"TownHallPopup: Erreur add_dynamic_info : {e}")
            layout.add_widget(make_adaptive_label(
                f"[color=ff0000][b]Erreur dans la partie spécifique Hôtel de Ville[/b][/color]\n{e}", min_height=40
            ))

    def open_population_popup(self, instance):
        try:
            from popups.population_popup import PopulationPopup
            city = self.get_city()
            if city:
                popup = PopulationPopup(
                    title="Gestion de la population",
                    building_data={},  # Un dictionnaire vide ou tes vraies données
                    city=city
                )
                popup.open()
        except Exception as e:
            Logger.error(f"TownHallPopup: Erreur open_population_popup : {e}")

    def add_gold_rate_selector(self, layout):
        label_height = 22
        layout.add_widget(make_adaptive_label("[b]Taux d'impôt :[/b]", min_height=label_height))

        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=label_height+8, spacing=8)
        self.gold_rate_buttons = []
        city = self.get_city()
        gold_rate = getattr(city, "gold_rate", 1)
        for rate in [1, 2, 3]:
            btn = Button(
                text=f"{rate} or",
                size_hint_x=None,
                width=60,
                background_color=(0.7, 0.7, 0.7, 1) if gold_rate == rate else (0.3, 0.3, 0.3, 1)
            )
            btn.bind(on_press=lambda instance, r=rate: self.set_gold_rate(r))
            btn_layout.add_widget(btn)
            self.gold_rate_buttons.append(btn)
        layout.add_widget(btn_layout)
        self.gold_rate_btn_layout = btn_layout

    def apply_gold_rate(self):
        city = self.get_city()
        if city and self.network_manager:
            player_id = getattr(city, "owner", None)
            resp = self.network_manager._post(
                "/set_tax_rate",
                {
                    "city_id": city.id,
                    "player_id": player_id,
                    "tax_rate": getattr(city, "gold_rate", 1)
                }
            )
            if resp and resp.get("success") and "city" in resp:
                city.from_dict_instance(resp["city"])
            self.refresh_gold_rate_buttons()
            if hasattr(self, 'update_header_callback') and self.update_header_callback:
                self.update_header_callback()
            if hasattr(self, 'update_city_callback') and self.update_city_callback:
                self.update_city_callback(city)

    def refresh_gold_rate_buttons(self):
        city = self.get_city()
        gold_rate = getattr(city, "gold_rate", 1)
        for i, btn in enumerate(self.gold_rate_buttons):
            btn.background_color = (0.7, 0.7, 0.7, 1) if (i+1) == gold_rate else (0.3, 0.3, 0.3, 1)

    def update_town_hall_info(self, *args):
        try:
            city = self.get_city()
            if not (city and self.population_manager):
                return
            resources = city.get_resources()
            current_population = resources.get("population_total", 0)

            population_assigned = sum(
                city.get_workers_assigned(resource) for resource in getattr(city, "workers_assigned", {})
            )
            population_free = current_population - population_assigned

            max_population = self.population_manager.calculate_population_limit(city)
            # Récupération des valeurs calculées par PopulationManager
            pop_nourished_by_townhall = resources.get("pop_nourished_by_townhall", 0)
            pop_nourished_by_windmill = resources.get("pop_nourished_by_windmill", 0)
            total_nourished = pop_nourished_by_townhall + pop_nourished_by_windmill
            cereal_needed = resources.get("cereal_needed", 0)
            growth_rate = resources.get("population_growth", 0)

            self.current_population_label.text = (
                f"Population: {int(current_population)} "
                f"(libre: {int(population_free)}, affectée: {int(population_assigned)})"
            )
            self.max_population_label.text = f"Capacité max: {int(max_population)}"
            self.nourished_population_label.text = (
                f"Population nourrie : {int(total_nourished)} (Hôtel de Ville : {int(pop_nourished_by_townhall)}, Moulin : {int(pop_nourished_by_windmill)})"
            )
            self.remaining_population_label.text = f"Restant à nourrir: {int(max(0, current_population - total_nourished))}"
            self.cereal_consumption_label.text = f"Consommation de céréales : {int(cereal_needed)} /sec"
            self.population_growth_label.text = f"Croissance de la population : {growth_rate:.2f} /sec"
            multiplicateur = getattr(city, "windmill_cereal_multiplier", 1)
            self.per_capita_cereal_consumption_label.text = f"Conso. par habitant : 0.1 × {multiplicateur:.2f} = {0.1 * multiplicateur:.2f} /sec"

            satisfaction = city.get_satisfaction()
            self.satisfaction_label.text = f"Satisfaction : {int(satisfaction)} / 100"

            gold_rate = getattr(city, "gold_rate", 1)
            gold_growth = int(population_free) * gold_rate
            self.gold_growth_label.text = f"[b]Taux de croissance de l'or : {gold_growth} or/sec[/b]"
            self.refresh_gold_rate_buttons()

        except Exception as e:
            Logger.error(f"TownHallPopup: Erreur lors de la mise à jour des informations : {e}")

    def rename_city(self, instance):
        city = self.get_city()
        if city:
            new_name = self.rename_input.text.strip()
            if new_name and new_name != city.name:
                try:
                    response = self.network_manager.rename_city(city.id, new_name)
                    if response and response.get("success") and "city" in response:
                        city.from_dict_instance(response["city"])
                        self.rename_input.text = city.name
                        print("Nom de la ville après renommage :", city.name)  # <-- Ligne ajoutée
                        if hasattr(self, 'update_header_callback') and self.update_header_callback:
                            self.update_header_callback()
                        if hasattr(self, 'update_city_callback') and self.update_city_callback:
                            self.update_city_callback(city)
                    else:
                        self._show_error(response.get("error", "Erreur lors du renommage."))
                except Exception as e:
                    self._show_error(f"Erreur réseau : {e}")

    def open_satisfaction_popup(self, instance):
        city = self.get_city()
        if city:
            popup = SatisfactionPopup(city)
            popup.open()

    def close(self):
        if hasattr(self, 'town_hall_info_event'):
            self.town_hall_info_event.cancel()
        self.dismiss()

    def set_gold_rate(self, rate):
        city = self.get_city()
        if city:
            city.gold_rate = rate
            self.apply_gold_rate()