from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import sp
from config.style import apply_button_style, apply_label_style
from data.research_data import RESEARCH_TREE
from models.game_data import GameData

# On ne définit plus SERVER_URL ici, il vient du NetworkManager

class ResearchView(BoxLayout):
    def __init__(self, open_research_tree_callback, go_back_callback, open_research_table_callback, game_data, network_manager, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        if not isinstance(game_data, GameData):
            raise ValueError("game_data doit être une instance valide de GameData.")

        self.game_data = game_data
        self.network_manager = network_manager
        self.open_research_tree_callback = open_research_tree_callback
        self.go_back_callback = go_back_callback
        self.open_research_table_callback = open_research_table_callback

        self.spacing = 20
        self.padding = 20

        # Ajout des catégories avec labels et boutons
        categories = [("ÉCONOMIE", "economy"), ("SCIENCE", "science"), ("GUERRE", "warfare"), ("MARINE", "marine")]
        for label, category in categories:
            category_label = Label(text=label, size_hint_y=None, height=40, font_size=sp(16))
            apply_label_style(category_label)
            self.add_widget(category_label)

            open_tree_button = Button(text=f"Voir l'arbre {label.lower()}", size_hint_y=None, height=50)
            apply_button_style(open_tree_button)
            open_tree_button.bind(on_press=lambda instance, cat=category: self.open_research_tree(cat))
            self.add_widget(open_tree_button)

        # Boutons pour afficher les tableaux individuels
        table_buttons = [
            ("Tableau ÉCONOMIE", "economy"),
            ("Tableau SCIENCE", "science"),
            ("Tableau GUERRE", "warfare"),
            ("Tableau MARINE", "marine"),
        ]

        for text, category in table_buttons:
            specific_table_button = Button(text=text, size_hint=(1, None), height=50)
            apply_button_style(specific_table_button)
            specific_table_button.bind(on_press=lambda instance, cat=category: self.open_specific_table(cat))
            self.add_widget(specific_table_button)

        # Bouton Retour
        return_button = Button(text="Retour", size_hint=(1, None), height=50)
        apply_button_style(return_button)
        return_button.bind(on_press=lambda instance: go_back_callback())
        self.add_widget(return_button)

    def open_research_tree(self, category):
        """Ouvre une popup pour afficher l'arbre de recherche de la catégorie."""
        if category not in RESEARCH_TREE:
            print(f"[ERREUR] Catégorie inconnue : {category}")
            return

        research_popup = ResearchTreePopup(category, RESEARCH_TREE[category], self.game_data, self.network_manager)
        research_popup.open()

    def open_specific_table(self, category):
        """Ouvre un tableau spécifique de recherche sous forme de popup."""
        if category not in RESEARCH_TREE:
            print(f"[ERREUR] Catégorie inconnue : {category}")
            return

        research_table_popup = ResearchTablePopup(category, RESEARCH_TREE[category])
        research_table_popup.open()

class ResearchTreePopup(Popup):
    def __init__(self, category, research_data, game_data, network_manager, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Arbre de recherche : {category.capitalize()}"
        self.size_hint = (0.9, 0.9)
        self.game_data = game_data  # Référence à GameData pour gérer les recherches
        self.network_manager = network_manager

        main_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Ajouter un ScrollView pour afficher les recherches
        scroll_view = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))

        self.research_data = research_data
        self.populate_research_grid()

        scroll_view.add_widget(self.grid)
        main_layout.add_widget(scroll_view)

        # Bouton Fermer
        close_button = Button(text="Fermer", size_hint=(1, None), height=50)
        apply_button_style(close_button)
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout

    def populate_research_grid(self):
        self.grid.clear_widgets()
        current_player_id = self.game_data.current_player_id
        if current_player_id is None:
            print("[ERROR] Aucun joueur authentifié.")
            return

        for research in self.research_data:
            is_unlocked = all(
                prereq in self.game_data.player_manager.get_player(current_player_id).unlocked_research for prereq in research['prerequisites']
            )

            button_text = (
                f"{research['name']}\n"
                f"Points: {research['cost'].get('research_points', 0)}\n"
                f"Coût: {', '.join([f'{k}: {v}' for k, v in research['cost'].items() if k != 'research_points'])}"
            )

            research_button = Button(text=button_text, size_hint_y=None, height=100, disabled=not is_unlocked)
            apply_button_style(research_button)
            research_button.bind(on_press=lambda instance, res=research: self.open_research_details(res))
            self.grid.add_widget(research_button)

    def open_research_details(self, research):
        """Ouvre la fenêtre de détails pour une recherche spécifique."""
        details_popup = ResearchDetailsPopup(
            research, self.game_data, self.network_manager
        )
        details_popup.bind(on_dismiss=self.refresh_research_tree)  # Refresh the research tree on dismiss
        details_popup.open()

    def refresh_research_tree(self, instance):
        """Refresh the research tree after a research is unlocked."""
        self.populate_research_grid()

class ResearchDetailsPopup(Popup):
    def __init__(self, research, game_data, network_manager, **kwargs):
        super().__init__(**kwargs)
        self.game_data = game_data  # Référence à GameData
        self.network_manager = network_manager
        self.title = research["name"]
        self.size_hint = (0.8, 0.8)
        self.research = research

        main_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Description
        description_label = Label(
            text=f"[b]Description :[/b]\n{research['description']}",
            markup=True,
            size_hint_y=None,
            height=120,
        )
        apply_label_style(description_label)
        main_layout.add_widget(description_label)

        # Coût
        cost_text = ", ".join([f"{k}: {v}" for k, v in research["cost"].items()])
        cost_label = Label(
            text=f"[b]Coût :[/b]\n{cost_text}",
            markup=True,
            size_hint_y=None,
            height=80,
        )
        apply_label_style(cost_label)
        main_layout.add_widget(cost_label)

        # Points de recherche disponibles
        current_player_id = self.game_data.current_player_id
        if current_player_id is None:
            print("[ERROR] Aucun joueur authentifié.")
            self.dismiss()
            return

        player = self.game_data.player_manager.get_player(current_player_id)
        city_manager = self.game_data.city_manager
        owned_cities = city_manager.get_cities_for_player(player.id_player)
        if not player or not owned_cities:
            print("[ERROR] Aucun joueur ou aucune ville trouvée.")
            self.dismiss()
            return
        city = owned_cities[0]
        available_points = player.research_points
        self.available_points_label = Label(
            text=f"Points de recherche disponibles : {available_points}",
            size_hint_y=None,
            height=40,
        )
        apply_label_style(self.available_points_label)
        main_layout.add_widget(self.available_points_label)

        # Bouton Débloquer
        self.unlock_button = Button(text="Débloquer", size_hint=(1, None), height=50)
        apply_button_style(self.unlock_button)
        self.unlock_button.bind(on_press=lambda instance: self.unlock_research(research=self.research))
        
        # Désactiver le bouton si les points de recherche sont insuffisants
        if available_points < research["cost"].get("research_points", 0):
            self.unlock_button.disabled = True

        main_layout.add_widget(self.unlock_button)

        # Bouton Fermer
        close_button = Button(text="Fermer", size_hint=(1, None), height=50)
        apply_button_style(close_button)
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout

    def unlock_research(self, research):
        current_player_id = self.game_data.current_player_id
        if current_player_id is None:
            print("[ERROR] Aucun joueur authentifié.")
            return

        # Appel centralisé via NetworkManager
        result = self.network_manager.unlock_research(current_player_id, research["name"])
        if result.get("success"):
            available_points = result.get("available_points", 0)
            self.available_points_label.text = f"Points de recherche disponibles : {available_points}"
            self.unlock_button.disabled = True
            # MAJ locale (optionnel, si tu veux maintenir la cohérence en RAM)
            player = self.game_data.player_manager.get_player(current_player_id)
            player.unlocked_research = result.get("unlocked_research", player.unlocked_research)
            # Optionnel : recharger la ville/ressources
            city_manager = self.game_data.city_manager
            owned_cities = city_manager.get_cities_for_player(player.id_player)
            if owned_cities:
                player.research_points = available_points
        else:
            print("Erreur serveur : ", result.get("error"))

        self.dismiss()

class ResearchTablePopup(Popup):
    def __init__(self, category, research_data, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Tableau des recherches : {category.capitalize()}"
        self.size_hint = (0.9, 0.9)

        main_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Ajouter un ScrollView pour afficher le tableau
        scroll_view = ScrollView()
        grid = GridLayout(cols=4, spacing=5, size_hint_y=None)  # 4 colonnes pour les données
        grid.bind(minimum_height=grid.setter('height'))

        # En-têtes du tableau
        headers = ["Nom", "Âge", "Description", "Coût"]
        header_widths = [80, 40, 120, 100]  # Largeur maximale des colonnes
        for header, width in zip(headers, header_widths):
            header_label = Label(
                text=f"[b]{header}[/b]",
                markup=True,
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
            )
            header_label.text_size = (width, None)  # Limite la largeur pour forcer les sauts de ligne
            apply_label_style(header_label)
            grid.add_widget(header_label)

        # Ajouter les données de recherche
        for research in research_data:
            # Nom
            name_label = Label(
                text=research["name"],
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
            )
            name_label.text_size = (header_widths[0], None)  # Largeur fixe avec ajustement automatique
            apply_label_style(name_label)
            grid.add_widget(name_label)

            # Âge
            age_label = Label(
                text=research["age"],
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
            )
            age_label.text_size = (header_widths[1], None)
            apply_label_style(age_label)
            grid.add_widget(age_label)

            # Description
            description_label = Label(
                text=research["description"],
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
            )
            description_label.text_size = (header_widths[2], None)  # Largeur fixe pour la description
            apply_label_style(description_label)
            grid.add_widget(description_label)

            # Coût
            cost_text = ", ".join([f"{k}: {v}" for k, v in research["cost"].items()])
            cost_label = Label(
                text=cost_text,
                size_hint_y=None,
                height=50,
                halign="center",
                valign="middle",
            )
            cost_label.text_size = (header_widths[3], None)  # Largeur fixe pour les coûts
            apply_label_style(cost_label)
            grid.add_widget(cost_label)

        # Ajouter la grille au ScrollView
        scroll_view.add_widget(grid)
        main_layout.add_widget(scroll_view)

        # Bouton Fermer
        close_button = Button(text="Fermer", size_hint=(1, None), height=50)
        apply_button_style(close_button)
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout