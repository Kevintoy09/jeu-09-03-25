from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from widgets.timer_widget import TimerWidget
from kivy.clock import Clock
from models.building import Building
from widgets.ui_helpers import make_adaptive_label, show_alert_popup, show_confirmation_popup

class BasePopup(Popup):
    """
    Popup de base pour l'affichage et la gestion d'un bâtiment.
    Toute la logique métier (coût, bonus, timer, effets) est côté serveur.
    L'UI ne fait qu'afficher, déclencher les actions, attendre la réponse, synchroniser et afficher.
    """

    def __init__(
        self,
        title,
        building_data,
        update_all_callback=None,
        buildings_manager=None,
        custom_content_callback=None,
        network_manager=None,
        city_view=None,
        city_id=None,
        game_data=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.building_data = building_data
        self.update_all_callback = update_all_callback
        self.buildings_manager = buildings_manager
        self.network_manager = network_manager
        self.city_view = city_view
        self.city_id = city_id
        self.game_data = game_data
        self.size_hint = (0.8, 0.8)
        self.need_refresh_after_close = False
        self._refresh_event = None

        self.scrollview = ScrollView(size_hint=(1, 1))
        self.main_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        self.main_layout.bind(minimum_height=self.main_layout.setter('height'))
        self.scrollview.add_widget(self.main_layout)
        self.content = self.scrollview

        try:
            self.construction_key = self.get_construction_key()
        except Exception as e:
            self._show_error(f"Erreur clé construction : {e}")
            return

        try:
            self.building = Building.ensure_instance(
                building_data.get("building") if isinstance(building_data, dict) and "building" in building_data else building_data
            )
        except Exception as e:
            self._show_error(f"Erreur building instance : {e}")
            return

        try:
            self._create_dynamic_info_widgets(building_data)
        except Exception as e:
            self._show_error(f"Erreur dynamic_info : {e}")
            return

        try:
            self.main_layout.add_widget(self.common_info_layout)
            self.main_layout.add_widget(self.cost_info_layout)
            self.main_layout.add_widget(self._create_action_buttons(building_data))
        except Exception as e:
            self._show_error(f"Erreur widgets principaux : {e}")
            return

        specific_layout = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None))
        specific_layout.bind(minimum_height=specific_layout.setter('height'))
        specific_layout.height = 10

        if custom_content_callback:
            try:
                custom_content_callback(specific_layout)
            except Exception as e:
                specific_layout.add_widget(make_adaptive_label(
                    f"[color=ff0000][b]Erreur partie spécifique[/b][/color]\n{e}"
                ))

        self.main_layout.add_widget(specific_layout)
        self.bind(on_dismiss=self._on_popup_dismiss)
        self._start_refresh_complete_button()

    def _resolve_city_slot_player(self, building_data=None):
        data = building_data if building_data is not None else self.building_data
        slot_index = data.get("slot_index") if isinstance(data, dict) else None
        city = None
        if self.city_view and getattr(self.city_view, "city_data", None):
            city = self.city_view.city_data
        elif self.city_id and self.game_data and hasattr(self.game_data, "city_manager"):
            city = self.game_data.city_manager.get_city_by_id(self.city_id)
        player_id = getattr(city, "owner", None) if city else None
        return city, slot_index, player_id

    def _start_refresh_complete_button(self):
        if self._refresh_event is None:
            self._refresh_event = Clock.schedule_interval(lambda dt: self.refresh_common_info_labels(), 0.5)

    def _stop_refresh_complete_button(self):
        if self._refresh_event is not None:
            self._refresh_event.cancel()
            self._refresh_event = None

    def _on_popup_dismiss(self, *args):
        self._stop_refresh_complete_button()
        if self.need_refresh_after_close and self.city_view:
            self.city_view.update_city()
            if self.update_all_callback:
                self.update_all_callback()

    def _show_error(self, message):
        self.main_layout.clear_widgets()
        err_box = BoxLayout(orientation="vertical")
        err_box.add_widget(make_adaptive_label(
            f"[color=ff0000][b]Erreur ouverture popup[/b][/color]\n{message}"
        ))
        btn = Button(text="Fermer", size_hint=(1, None), height=40)
        btn.bind(on_release=lambda instance: self.dismiss())
        err_box.add_widget(btn)
        self.main_layout.add_widget(err_box)

    def get_construction_key(self):
        city = None
        slot_index = self.building_data.get("slot_index")
        if self.city_view and getattr(self.city_view, "city_data", None):
            city = self.city_view.city_data
        elif self.city_id and self.game_data and hasattr(self.game_data, "city_manager"):
            city = self.game_data.city_manager.get_city_by_id(self.city_id)
        if not city:
            raise ValueError("Impossible de résoudre la ville centrale !")
        island_coords = getattr(city, "coords", None)
        city_name = getattr(city, "name", None)
        if island_coords is None or city_name is None or slot_index is None:
            raise ValueError("Paramètre manquant pour construction_key")
        return (island_coords, city_name, slot_index)

    def _create_dynamic_info_widgets(self, building_data):
        self.common_info_layout = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None))
        self.common_info_layout.bind(minimum_height=self.common_info_layout.setter('height'))

        self.title_label = make_adaptive_label(f"[b]{self.title}[/b]", height=40, halign="center", valign="middle")
        self.common_info_layout.add_widget(self.title_label)

        description = building_data.get("description", "Aucune description disponible.")
        self.description_label = make_adaptive_label(str(description), height=60)
        self.common_info_layout.add_widget(self.description_label)

        self.niveau_label = make_adaptive_label("", height=30)
        self.common_info_layout.add_widget(self.niveau_label)
        self.effets_actuels_label = make_adaptive_label("", height=60)
        self.common_info_layout.add_widget(self.effets_actuels_label)
        self.effets_suivants_label = make_adaptive_label("", height=60)
        self.common_info_layout.add_widget(self.effets_suivants_label)

        self.cost_info_layout = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=10)
        self.cost_info_layout.bind(minimum_height=self.cost_info_layout.setter('height'))
        self.cost_label = make_adaptive_label("", height=30)
        self.cost_info_layout.add_widget(self.cost_label)

        self.refresh_common_info_labels()

    def refresh_common_info_labels(self):
        city, slot_index, _ = self._resolve_city_slot_player()
        if city and slot_index is not None:
            self.building = city.get_buildings()[slot_index]

        building_name = self.building_data.get("name")
        display_level = self.building.get_display_level() if self.building else 1
        current_level = display_level - 1
        if current_level < 0:
            current_level = 0

        self.niveau_label.text = f"[b]Niveau actuel : {display_level}[/b]"

        effets_actuels = "Non disponible."
        effets_suivants = "Non disponible."
        if self.buildings_manager:
            details_current = self.buildings_manager.get_building_details(building_name, display_level, city)
            details_next = self.buildings_manager.get_building_details(building_name, display_level + 1, city)
            if details_current and "effect" in details_current:
                effets_actuels = "\n".join(f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in details_current["effect"].items()) or "Aucun."
            if details_next and "effect" in details_next:
                effets_suivants = "\n".join(f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in details_next["effect"].items()) or "Aucun."
            elif not details_next:
                effets_suivants = "[b]Niveau maximum atteint.[/b]"
        self.effets_actuels_label.text = f"[b]Effets actuels :[/b]\n{effets_actuels}"
        self.effets_suivants_label.text = f"[b]Effets du niveau suivant :[/b]\n{effets_suivants}"

        if not self.buildings_manager or not hasattr(self.buildings_manager, "get_building_details"):
            self.cost_label.text = "Données du manager absentes."
        else:
            next_level = current_level + 2
            details = self.buildings_manager.get_building_details(building_name, next_level, city) if city else None
            if not details:
                self.cost_label.text = "Niveau maximum atteint ou données manquantes."
            else:
                cost = details.get("cost", {})
                construction_time = details.get("construction_time", "Indéfini")
                cost_items = [f"{res.capitalize()}: {amount}" for res, amount in cost.items()]
                cost_items.append(f"Temps: {construction_time}s")

                # Ajout du bonus architecte si présent
                architecte_bonus = ""
                if self.buildings_manager and hasattr(self.buildings_manager, "apply_architect_reductions"):
                    city = self.city_view.city_data if self.city_view and hasattr(self.city_view, "city_data") else None
                    if city:
                        custom_data = self.buildings_manager.get_city_building_data(city)
                        for b in city.get_buildings():
                            if b and getattr(b, "name", "").lower().replace(" ", "") in ["atelierd'architecte", "atelierdarchitecte"]:
                                if getattr(b, "status", None) == "Terminé":
                                    effect = getattr(b, "effect", {})
                                    cost_red = effect.get("construction_cost_reduction", 0)
                                    time_red = effect.get("construction_time_reduction", 0)
                                    if cost_red or time_red:
                                        architecte_bonus = f"(Architecte : -{cost_red}% coût, -{time_red}% temps)"
                                break
                if architecte_bonus:
                    cost_items.append(architecte_bonus)

                self.cost_label.text = " | ".join(cost_items)

        try:
            if hasattr(self, "finish_button") and self.finish_button is not None:
                self.update_finish_button_state()
        except Exception:
            pass

    def _create_action_buttons(self, building_data):
        layout = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))

        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        develop_button = Button(text="Développer", size_hint=(0.3, 1))
        destroy_button = Button(text="Détruire", size_hint=(0.3, 1))
        close_button = Button(text="Fermer", size_hint=(0.3, 1))

        display_level = self.building.get_display_level() if self.building else 1
        details_next = self.buildings_manager.get_building_details(
            self.building_data.get("name"),
            display_level + 1,
            self.city_view.city_data if self.city_view else None
        )
        if not details_next or (self.building and self.building.status == "En construction" and self.building.get_remaining_time() > 0):
            develop_button.disabled = True

        develop_button.bind(on_press=lambda instance: self._on_develop_pressed())
        destroy_button.bind(on_press=lambda instance: self.destroy_building(building_data))
        close_button.bind(on_press=lambda instance: self.dismiss())

        button_layout.add_widget(develop_button)
        button_layout.add_widget(destroy_button)
        button_layout.add_widget(close_button)
        layout.add_widget(button_layout)

        timer_initial = 0
        if self.building is not None and hasattr(self.building, "get_remaining_time"):
            timer_initial = self.building.get_remaining_time()

        # --- TIMER SPÉCIFIQUE AU POPUP ---
        # Personnalisation du timer pour le popup (différent du slot dans CityView)
        self.timer_widget = TimerWidget(
            initial_time=timer_initial,
            on_timer_finished=self.on_timer_finished_popup,
            size_hint=(1, None),
            height=32,  # Plus petit que sur le slot
            font_size="14sp",  # Police plus petite
            font_color=(0, 0, 0, 1),  # Texte noir
            banner_color=(1, 1, 1, 0.95),  # Fond blanc légèrement transparent
            border_color=(0.5, 0.5, 0.5, 0.7),  # Bordure grise
            label_pos_hint={"center_x": 0.5, "top": 1}  # Position différente (légèrement plus bas)
        )
        layout.add_widget(self.timer_widget)
        # --- FIN TIMER POPUP SPÉCIFIQUE ---

        self.finish_button = Button(text="Terminer instantanément", size_hint=(1, None), height=40)
        self.finish_button.disabled = not getattr(self, 'can_finish_instantly', False)
        self.finish_button.bind(on_press=lambda instance: self._on_finish_instantly_pressed())
        layout.add_widget(self.finish_button)

        return layout

    def update_finish_button_state(self):
        building_name = self.building_data.get("name")
        level = self.building.get_display_level()
        city_id = getattr(self.city_view.city_data, "id", None) if self.city_view and hasattr(self.city_view, "city_data") else None
        player_id = getattr(self.city_view.city_data, "owner", None) if self.city_view and hasattr(self.city_view, "city_data") else None

        details = self.network_manager.get_building_details(building_name, level, city_id, player_id)
        self.can_finish_instantly = details.get("can_finish_instantly", False)
        self.finish_button.disabled = not self.can_finish_instantly

    def _on_develop_pressed(self):
        city, slot_index, player_id = self._resolve_city_slot_player()
        building_name = self.building_data.get("name")
        if self.network_manager is not None:
            resp = self.network_manager.build_batiment(
                username=getattr(player_id, "username", None),
                player_id=player_id,
                city_id=getattr(city, "id", None),
                building_name=building_name,
                slot_index=slot_index
            )
            self.on_build_response(resp)
        else:
            resp = self.buildings_manager.build_or_upgrade_building(city, slot_index, building_name, player_id=player_id)
            self.on_build_response(resp)

    def on_timer_finished_popup(self, *args):
        self.need_refresh_after_close = True
        self._sync_and_refresh()

    def destroy_building(self, building_data):
        def do_destroy(instance):
            city, slot_index, player_id = self._resolve_city_slot_player(building_data)
            city_id = getattr(city, "id", None) if city else None
            if self.network_manager is not None:
                self.network_manager.destroy_building(
                    player_id=player_id,
                    city_id=city_id,
                    slot_index=slot_index
                )
            elif self.buildings_manager is not None:
                self.buildings_manager.destroy_building(city, slot_index, player_id=player_id)
            self.need_refresh_after_close = True
            self._sync_and_refresh()
            self.dismiss()

        show_confirmation_popup(
            message="Voulez-vous vraiment détruire ce bâtiment ?\n(Cela enlèvera 1 niveau, ou supprimera le bâtiment si niveau 1)",
            on_confirm=do_destroy,
            title="Confirmer la destruction"
        )

    def _sync_and_refresh(self):
        if self.city_view and hasattr(self.city_view, "manager") and hasattr(self.city_view.manager, "sync_from_server"):
            def sync_and_update(dt):
                self.city_view.manager.sync_from_server(
                    on_done=lambda: Clock.schedule_once(lambda ddt: self.city_view.update_city(), 0.01)
                )
                Clock.schedule_once(lambda ddt: self.refresh_common_info_labels(), 0.2)
            Clock.schedule_once(sync_and_update, 0.05)
        elif self.city_view:
            Clock.schedule_once(lambda dt: self.city_view.update_city(), 0.1)
            Clock.schedule_once(lambda dt: self.refresh_common_info_labels(), 0.2)
        else:
            self.refresh_common_info_labels()

    def _on_finish_instantly_pressed(self):
        city, slot_index, player_id = self._resolve_city_slot_player()
        building_name = self.building_data.get("name")
        if self.network_manager is not None:
            resp = self.network_manager.complete_instantly(
                player_id=player_id,
                city_id=getattr(city, "id", None),
                slot_index=slot_index,
                building_name=building_name
            )
            self.on_build_response(resp)
        else:
            resp = self.buildings_manager.complete_instantly(city, slot_index, building_name=building_name)
            self.on_build_response(resp)
        self.update_finish_button_state()

    def on_build_response(self, response):
        if not response or not response.get("success", False):
            message = response.get("message", "Erreur lors de la construction ou du développement.") if response else "Erreur inconnue."
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            popup = Popup(title="Erreur", content=Label(text=message), size_hint=(0.7, 0.3))
            popup.open()
        else:
            self._sync_and_refresh()
            # Met à jour le timer APRÈS le rafraîchissement
            def update_timer(dt):
                if hasattr(self, "timer_widget") and hasattr(self, "building") and hasattr(self.building, "get_remaining_time"):
                    self.timer_widget.set_time(self.building.get_remaining_time())
            Clock.schedule_once(update_timer, 0.3)