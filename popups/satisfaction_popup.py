from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from .base_popup import BasePopup

def make_adaptive_label(text, min_height=22, **kwargs):
    return Label(text=text, markup=True, size_hint_y=None, height=min_height, **kwargs)

class SatisfactionPopup(BasePopup):
    def __init__(self, city, **kwargs):
        super().__init__("Détail de la satisfaction", {}, None, None, **kwargs)
        self.city = city

        # Créez un layout vertical pour contenir tous les widgets
        layout = BoxLayout(orientation='vertical', size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Pour que le ScrollView fonctionne

        self.add_dynamic_info(layout)
        self.content.clear_widgets()
        self.content.add_widget(layout)  # Ajoutez le layout au ScrollView

    def add_dynamic_info(self, layout):
        layout.clear_widgets()
        # Calcul dynamique de la satisfaction
        satisfaction = self.city.get_satisfaction()

        layout.add_widget(make_adaptive_label(
            f"[b]Satisfaction totale : {int(self.city.get_satisfaction())} / 100[/b]", min_height=30
        ))
        layout.add_widget(make_adaptive_label("[b]Malus :[/b]", min_height=24))
        for k, v in self.city.satisfaction_factors.get("malus", {}).items():
            layout.add_widget(make_adaptive_label(f"- {k} : -{v}", min_height=22))
        layout.add_widget(make_adaptive_label("[b]Bonus :[/b]", min_height=24))
        for k, v in self.city.satisfaction_factors.get("bonus", {}).items():
            layout.add_widget(make_adaptive_label(f"+ {k} : +{v}", min_height=22))
        layout.add_widget(make_adaptive_label(
            "\nLa satisfaction module la croissance de la population.\n"
            "Exemple : 0 = crise, 50 = neutre, 100 = boom démographique.", min_height=30
        ))
        close_btn = Button(text="Fermer", size_hint_y=None, height=40)
        close_btn.bind(on_press=lambda instance: self.dismiss())
        layout.add_widget(close_btn)