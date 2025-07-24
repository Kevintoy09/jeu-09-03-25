from popups.town_hall_popup import TownHallPopup
from popups.windmill_popup import WindmillPopup
from popups.academy_popup import AcademyPopup
from popups.barracks_popup import BarracksPopup
from popups.port_popup import PortPopup
from popups.wall_popup import WallPopup
from popups.architect_workshop_popup import ArchitectWorkshopPopup
from popups.mine_popup import MinePopup
from popups.sawmill_popup import SawmillPopup
from popups.warehouse_popup import WarehousePopup
from popups.ambassade_popup import AmbassadePopup
from kivy.clock import Clock
from models.building import Building
from data.buildings_database import buildings_database
from popups.thermes_popup import ThermesPopup

class BuildingPopupManager:
    """
    Gère l’ouverture des popups spécifiques à chaque bâtiment.
    Centralise la logique d’affichage et de passage des callbacks/ressources.
    """
    def __init__(self, city_view, buildings_manager, resource_manager, population_manager, network_manager=None, transport_manager=None):
        self.city_view = city_view
        self.buildings_manager = buildings_manager
        self.resource_manager = resource_manager
        self.population_manager = population_manager
        self.network_manager = network_manager
        self.transport_manager = transport_manager

        self.building_handlers = {
            "Hôtel de Ville": self.show_town_hall_popup,
            "Windmill": self.show_windmill_popup,
            "Academy": self.show_academy_popup,
            "Caserne": self.show_barracks_popup,
            "Port": self.show_port_popup,
            "Muraille": self.show_wall_popup,
            "Atelier d'Architecte": self.show_architect_workshop_popup,
            "Mine": self.show_mine_popup,
            "Scierie": self.show_sawmill_popup,
            "Entrepôt": self.show_warehouse_popup,
            "Ambassade": self.show_ambassade_popup,
            "Thermes": self.show_thermes_popup,
        }

    def show_popup(self, building_name, building_data, update_all_callback, city_data, city_view):
        handler = self.building_handlers.get(building_name)
        if not handler:
            return

        # Inject "name" if missing (for dicts from database)
        if isinstance(building_data, dict) and "name" not in building_data:
            building_data = dict(building_data)
            building_data["name"] = building_name

        try:
            building_instance = Building.ensure_instance(building_data)
        except Exception as e:
            print(f"[DEBUG][Popup] Erreur lors de la création du building_instance : {e}")
            return

        popup_dict = building_instance.to_dict() if hasattr(building_instance, "to_dict") else dict(building_instance.__dict__)
        popup_dict.setdefault("slot_index", getattr(building_instance, "slot_index", 0))

        level = popup_dict.get("level", None)
        if level is None or level == 0:
            if building_data.get("level"):
                level = building_data.get("level")
            elif building_instance and hasattr(building_instance, "level"):
                level = getattr(building_instance, "level")
            else:
                level = 1
            if not isinstance(level, int):
                try:
                    level = int(level)
                except Exception:
                    level = 1
            if level < 1:
                level = 1
            popup_dict["level"] = level

        if "name" not in popup_dict and hasattr(building_instance, "name"):
            popup_dict["name"] = building_instance.name

        # Passe city_id ET city_view
        popup_dict["city_id"] = getattr(city_data, "id", None)
        # Ajoute city_view si besoin (pour compatibilité héritage popup)
        # (city_data = objet City, city_view = obj CityView)

        if "name" in popup_dict and popup_dict["name"] in buildings_database:
            popup_dict["levels"] = buildings_database[popup_dict["name"]].get("levels", [])
            popup_dict["description"] = buildings_database[popup_dict["name"]].get("description", "")

        if popup_dict.get("status") == "En construction":
            started_at = building_data.get("started_at") or popup_dict.get("started_at")
            build_duration = (
                building_data.get("build_duration")
                or popup_dict.get("build_duration")
                or building_data.get("construction_time")
                or popup_dict.get("construction_time")
            )
            if started_at:
                popup_dict["started_at"] = started_at
            if build_duration:
                popup_dict["build_duration"] = build_duration

        try:
            handler(popup_dict, update_all_callback, city_view)  # city_view transmis ici
        except Exception as e:
            print(f"[DEBUG][Popup] Erreur lors de l'ouverture du popup : {e}")

    def show_town_hall_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: TownHallPopup(
            "Hôtel de Ville",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            population_manager=self.population_manager,
            network_manager=self.network_manager,
        ).open())

    def show_windmill_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: WindmillPopup(
            "Windmill",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_academy_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: AcademyPopup(
            "Academy",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            resource_manager=self.resource_manager,
            network_manager=self.network_manager,
        ).open())

    def show_barracks_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: BarracksPopup(
            "Caserne",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_port_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: PortPopup(
            "Port",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            transport_manager=self.transport_manager,
            network_manager=self.network_manager,
        ).open())

    def show_wall_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: WallPopup(
            "Muraille",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_architect_workshop_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: ArchitectWorkshopPopup(
            "Atelier d'Architecte",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_mine_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: MinePopup(
            "Mine",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_sawmill_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: SawmillPopup(
            "Scierie",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_warehouse_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: WarehousePopup(
            "Entrepôt",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_ambassade_popup(self, popup_dict, update_all_callback, city_view):
        Clock.schedule_once(lambda dt: AmbassadePopup(
            "Ambassade",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            network_manager=self.network_manager,
        ).open())

    def show_thermes_popup(self, popup_dict, update_all_callback, city_view):
        # Récupère les callbacks standards
        Clock.schedule_once(lambda dt: ThermesPopup(
            "Thermes",
            popup_dict,
            update_all_callback,
            self.buildings_manager,
            custom_content_callback=None,
            city_view=city_view,
            city_id=popup_dict.get("city_id"),
            population_manager=self.population_manager,
            network_manager=self.network_manager,
        ).open())