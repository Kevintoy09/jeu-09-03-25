from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from .base_popup import BasePopup

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

class WindmillPopup(BasePopup):
    def __init__(
        self,
        title,
        building_data,
        update_all_callback,
        buildings_manager,
        custom_content_callback=None,
        city_view=None,
        city_id=None,
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

        if custom_content_callback is None:
            custom_content_callback = self.add_dynamic_info

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
                return game_data.city_manager.get_city_by_id(self.city_id)
        return None

    def add_dynamic_info(self, layout):
        self.dynamic_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=300, padding=30, spacing=30)
        self.dynamic_info_layout.bind(minimum_height=self.dynamic_info_layout.setter('height'))

        # Titre
        title_label = make_adaptive_label("Réglage du Moulin", min_height=40, bold=True)
        self.dynamic_info_layout.add_widget(title_label)

        # Capacité max du moulin et multiplicateur max
        city = self.get_city()
        windmill_capacity = 0
        cereal_multiplier_max = 1
        if city:
            for b in city.get_buildings():
                if b and b.get_name() == "Windmill" and b.get_status() == "Terminé":
                    level = b.get_level()
                    effect = b.effect if hasattr(b, "effect") else {}
                    windmill_capacity = effect.get("food_supply", 0)
                    cereal_multiplier_max = effect.get("cereal_consumption_multiplier", 1)
                    break

        self.capacity_label = make_adaptive_label(f"Capacité max du moulin : {windmill_capacity}", min_height=30)
        self.dynamic_info_layout.add_widget(self.capacity_label)

        self.multiplier_max_label = make_adaptive_label(
            f"Multiplicateur max : x{cereal_multiplier_max}", min_height=30
        )
        self.dynamic_info_layout.add_widget(self.multiplier_max_label)

        # Sécurise la valeur initiale pour qu'elle soit dans les bornes
        slider_min = 10
        slider_max = int(cereal_multiplier_max * 10)
        initial_value = int(round(getattr(city, "windmill_cereal_multiplier", 1) * 10))
        if initial_value < slider_min:
            initial_value = slider_min
        if initial_value > slider_max:
            initial_value = slider_max

        self.slider = Slider(
            min=slider_min,
            max=slider_max,
            value=initial_value,
            step=1,
            disabled=False,
            size_hint_y=None,
            height=60
        )
        self.slider.bind(value=self.on_slider_value_change)
        self.dynamic_info_layout.add_widget(self.slider)

        # Affichage du multiplicateur choisi (1 décimale)
        self.value_label = make_adaptive_label(
            f"Multiplicateur de consommation : x{self.slider.value/10:.1f}", min_height=30
        )
        self.dynamic_info_layout.add_widget(self.value_label)

        # Labels dynamiques pour les infos moulin
        self.label_cereal_per_hab = make_adaptive_label("Consommation de céréale/hab : ...", min_height=30)
        self.label_pop_restante = make_adaptive_label("Population restante à nourrir : ...", min_height=30)
        self.label_cereal_total = make_adaptive_label("Consommation totale de céréales : ...", min_height=30)
        self.label_bonus_satisfaction = make_adaptive_label("Bonus satisfaction du moulin : ...", min_height=30)
        self.label_population_growth = make_adaptive_label("Croissance de la population : ...", min_height=30)
        self.label_famine = make_adaptive_label("", min_height=30, color=(1,0,0,1))  # texte rouge

        self.dynamic_info_layout.add_widget(self.label_cereal_per_hab)
        self.dynamic_info_layout.add_widget(self.label_pop_restante)
        self.dynamic_info_layout.add_widget(self.label_cereal_total)
        self.dynamic_info_layout.add_widget(self.label_bonus_satisfaction)
        self.dynamic_info_layout.add_widget(self.label_population_growth)
        self.dynamic_info_layout.add_widget(self.label_famine)

        # Initial update
        self.update_dynamic_labels(self.slider.value)

        layout.add_widget(self.dynamic_info_layout)

    def update_dynamic_labels(self, slider_value):
        city = self.get_city()
        if not city:
            return
        multiplicateur = slider_value / 10
        resources = city.get_resources() if city else {}
        # Vérifie la famine
        en_famine = False
        if "famine" in city.satisfaction_factors.get("malus", {}):
            en_famine = True
        elif resources.get("cereal", 0) < resources.get("cereal_needed", 0):
            en_famine = True

        if en_famine and abs(city.windmill_cereal_multiplier - 1) > 1e-3:
            # Force le multiplicateur à 1
            city.windmill_cereal_multiplier = 1
            self.slider.value = 10  # 1.0 * 10
            self.value_label.text = "Multiplicateur de consommation : x1.0"
            # Affiche un message d’erreur utilisateur
            try:
                from config import message_info
                message_info.show_error_popup("Impossible de modifier le multiplicateur tant que la ville est en famine.")
            except Exception as e:
                print("[Erreur popup moulin]", e)
            # Met à jour toutes les données du backend
            if self.update_all_callback:
                self.update_all_callback()
            # Recharge les ressources et labels avec la nouvelle valeur
            resources = city.get_resources() if city else {}
        
        multiplicateur = city.windmill_cereal_multiplier
        resources = city.get_resources() if city else {}
        pop_unfed = resources.get("population_unfed", 0)
        # On suppose que la consommation de base est la consommation totale divisée par le multiplicateur actuel
        base_cereal_needed = resources.get("cereal_needed", 0) / max(multiplicateur, 1e-6) if multiplicateur > 0 else 0
        cereal_per_hab = base_cereal_needed / max(1, pop_unfed) if pop_unfed > 0 else 0
        cereal_total = base_cereal_needed * multiplicateur
        bonus_satisfaction = city.satisfaction_factors.get("bonus", {}).get("windmill", 0) if city else 0
        population_growth = resources.get("population_growth", 0)

        self.label_cereal_per_hab.text = f"Consommation de céréale/hab : base 0.1 × {multiplicateur:.1f} = {0.1 * multiplicateur:.2f} céréales/hab"
        self.label_pop_restante.text = f"Population restante à nourrir : {pop_unfed:.1f}"
        self.label_cereal_total.text = f"Consommation totale de céréales : {cereal_total:.2f}"
        self.label_bonus_satisfaction.text = f"Bonus satisfaction du moulin : +{bonus_satisfaction}"
        self.label_population_growth.text = f"Croissance de la population : {population_growth:.2f}/h"
        self.label_famine.text = "⚠️ Famine : plus assez de céréales pour nourrir la population" if en_famine else ""

    def on_slider_value(self, instance, value):
        print("[DEBUG] on_slider_value appelé avec value=", value)
        self.value_label.text = f"Multiplicateur de consommation : x{int(value)}"
        city = self.get_city()
        print("[DEBUG] city récupérée :", city)
        if city:
            city.windmill_cereal_multiplier = int(value)
            
            print("[DEBUG] city.windmill_cereal_multiplier mis à jour :", city.windmill_cereal_multiplier)
            print("[SERVER DEBUG] Multiplier reçu (avant conversion) :", city.windmill_cereal_multiplier)
    
    def on_slider_value_change(self, instance, value):
        multiplicateur = value / 10
        self.value_label.text = f"Multiplicateur de consommation : x{multiplicateur:.1f}"
        city = self.get_city()
        if city:
            city.windmill_cereal_multiplier = multiplicateur
            # Met à jour dynamiquement les labels
            self.update_dynamic_labels(value)
            # --- AJOUT POUR SYNCHRO SERVEUR ---
            if hasattr(self, "buildings_manager") and hasattr(self.buildings_manager, "network_manager"):
                network = self.buildings_manager.network_manager
                if network:
                    network._post(
                        "/set_windmill_multiplier",
                        {
                            "city_id": city.id,
                            "windmill_cereal_multiplier": value / 10
                        }
                    )
            # --- FIN AJOUT ---
            if self.update_all_callback:
                self.update_all_callback()

    def close(self):
        self.dismiss()