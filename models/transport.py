from enum import Enum
import math
from typing import Any, Dict, Optional, Union
from kivy.event import EventDispatcher
from kivy.properties import (
    ObjectProperty, DictProperty, NumericProperty, StringProperty
)

class EtatTransport(Enum):
    """État d'un transport dans le jeu."""
    EN_ATTENTE = "Waiting"
    CHARGEMENT = "Loading"
    TRANSPORT = "Transport"
    RETOUR = "Return"
    ANNULE = "Cancelled"

class Transport(EventDispatcher):
    """
    Représente un transport de ressources entre deux villes.
    """
    ville_source = ObjectProperty(None)
    ville_dest = ObjectProperty(None)
    ressources = DictProperty({})
    nb_bateaux = NumericProperty(0)
    joueur_source = ObjectProperty(None)
    joueur_dest = ObjectProperty(None, allownone=True)
    duree_chargement = NumericProperty(0)
    duree_transport = NumericProperty(0)
    temps_restant = NumericProperty(0)
    etat = StringProperty(EtatTransport.EN_ATTENTE.value)
    id = NumericProperty(None, allownone=True)
    event = ObjectProperty(None, allownone=True)

    def __init__(
        self,
        ville_source: Any,
        ville_dest: Any,
        ressources: Dict[str, int],
        nb_bateaux: int,
        joueur_source: Any,
        joueur_dest: Any,
        duree_chargement: float,
        duree_transport: float,
        etat: Union[EtatTransport, str] = EtatTransport.EN_ATTENTE,
        temps_restant: Optional[float] = None,
        id_: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.ville_source = ville_source
        self.ville_dest = ville_dest
        self.ressources = dict(ressources)
        self.nb_bateaux = nb_bateaux
        self.joueur_source = joueur_source
        self.joueur_dest = joueur_dest
        self.duree_chargement = duree_chargement
        self.duree_transport = duree_transport
        self.temps_restant = temps_restant if temps_restant is not None else duree_chargement
        self.etat = etat.value if isinstance(etat, EtatTransport) else str(etat)
        self.id = id_
        self.event = None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'objet pour l'API ou la sauvegarde."""
        return {
            "ville_source": getattr(self.ville_source, "id", self.ville_source),
            "ville_dest": getattr(self.ville_dest, "id", self.ville_dest),
            "ressources": dict(self.ressources),
            "nb_bateaux": self.nb_bateaux,
            "joueur_source": getattr(self.joueur_source, "id_player", self.joueur_source),
            "joueur_dest": getattr(self.joueur_dest, "id_player", self.joueur_dest) if self.joueur_dest else None,
            "duree_chargement": self.duree_chargement,
            "duree_transport": self.duree_transport,
            "etat": self.etat,
            "temps_restant": self.temps_restant,
            "id": self.id,
        }

    def to_display(self) -> str:
        """Affichage court pour l'UI."""
        return (
            f"{getattr(self.ville_source, 'name', self.ville_source)} → "
            f"{getattr(self.ville_dest, 'name', self.ville_dest)} : "
            f"{self.ressources} ({self.etat}, {round(max(0, self.temps_restant))}s, {self.nb_bateaux} ships)"
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], game_data: Any = None) -> "Transport":
        """
        Reconstruit un Transport depuis un dict. Si game_data est fourni, résout les ids en objets.
        """
        ville_source = data.get("ville_source")
        ville_dest = data.get("ville_dest")
        joueur_source = data.get("joueur_source")
        joueur_dest = data.get("joueur_dest")
        if game_data:
            ville_source_obj = game_data.city_manager.get_city_by_id(ville_source) if isinstance(ville_source, (str, int)) else ville_source
            ville_dest_obj = game_data.city_manager.get_city_by_id(ville_dest) if isinstance(ville_dest, (str, int)) else ville_dest
            joueur_source_obj = game_data.player_manager.get_player(joueur_source) if isinstance(joueur_source, (str, int)) else joueur_source
            joueur_dest_obj = game_data.player_manager.get_player(joueur_dest) if isinstance(joueur_dest, (str, int)) else joueur_dest
        else:
            ville_source_obj = ville_source
            ville_dest_obj = ville_dest
            joueur_source_obj = joueur_source
            joueur_dest_obj = joueur_dest

        etat_ = data.get("etat", EtatTransport.EN_ATTENTE.value)
        if not isinstance(etat_, EtatTransport):
            try:
                etat_ = EtatTransport(etat_)
            except Exception:
                etat_ = EtatTransport.EN_ATTENTE

        return cls(
            ville_source=ville_source_obj,
            ville_dest=ville_dest_obj,
            ressources=data.get("ressources", {}),
            nb_bateaux=data.get("nb_bateaux", 0),
            joueur_source=joueur_source_obj,
            joueur_dest=joueur_dest_obj,
            duree_chargement=data.get("duree_chargement", 0),
            duree_transport=data.get("duree_transport", 0),
            etat=etat_,
            temps_restant=data.get("temps_restant"),
            id_=data.get("id"),
        )

def calculer_distance(ville1: Any, ville2: Any) -> float:
    dx = getattr(ville1, "x", 0) - getattr(ville2, "x", 0)
    dy = getattr(ville1, "y", 0) - getattr(ville2, "y", 0)
    return math.sqrt(dx * dx + dy * dy)

def open_transport_popup_generic(
    from_city,
    city_dest,
    player,
    port_data,
    transport_manager,
    network_manager=None,
    joueur_dest=None,
    parent_popup=None
):
    from popups.transport_popup import TransportPopup
    from kivy.uix.popup import Popup
    from kivy.uix.label import Label

    def has_port(city):
        for b in getattr(city, "buildings", []):
            if b and getattr(b, "name", "").lower() == "port":
                return getattr(b, "level", 1) >= 1
        return False

    if not (has_port(from_city) and has_port(city_dest)):
        Popup(
            title="Transport impossible",
            content=Label(text="Both cities must have at least 1 port to transport goods."),
            size_hint=(0.65, 0.25)
        ).open()
        return

    stock_ressources = {
        "wood": from_city.resources.get("wood", 0),
        "stone": from_city.resources.get("stone", 0),
        "cereal": from_city.resources.get("cereal", 0),
        "iron": from_city.resources.get("iron", 0),
        "papyrus": from_city.resources.get("papyrus", 0),
    }

    ships_dispo = getattr(player, "ships_available", getattr(player, "ships", 0))
    ships_total = getattr(player, "ships", 0)
    port_level = port_data.get("level", 1) if port_data else 1
    if not port_data:
        for b in getattr(from_city, "buildings", []):
            if b and getattr(b, "name", "").lower() == "port":
                port_level = getattr(b, "level", 1)
                break

    vitesse_chargement = port_level * 10
    distance = calculer_distance(from_city, city_dest)

    popup = TransportPopup(
        ville_source=from_city,
        joueur_source=player,
        ville_dest=city_dest,
        joueur_dest=joueur_dest,
        ships_dispo=ships_dispo,
        ships_total=ships_total,
        stock_ressources=stock_ressources,
        vitesse_chargement=vitesse_chargement,
        distance=distance,
        ville_source_obj=from_city,
        ville_dest_obj=city_dest,
        transport_manager=transport_manager,
        network_manager=network_manager,
    )
    popup.open()
    if parent_popup:
        parent_popup.dismiss()