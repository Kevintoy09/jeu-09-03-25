import math
from datetime import datetime
from typing import Any, Dict, Optional, List

from models.transport import EtatTransport, Transport

class TransportManager:
    """
    Gère les transports locaux (file d'attente, progression, annulation, notifications).
    Aucun appel réseau ici : toute communication HTTP doit passer par un NetworkManager séparé.
    """

    def __init__(self, game_data):
        self.game_data = game_data
        self.transports: List[Transport] = []

    def ajouter_transport(self, transport: Transport) -> bool:
        transports_port = [
            t for t in self.transports
            if t.ville_source == transport.ville_source and t.etat in (EtatTransport.CHARGEMENT.value, EtatTransport.EN_ATTENTE.value)
        ]
        if transports_port:
            attente = sum(t.temps_restant for t in transports_port if t.etat == EtatTransport.CHARGEMENT.value)
            for t in transports_port:
                if t.etat == EtatTransport.EN_ATTENTE.value:
                    attente += t.temps_restant
            transport.etat = EtatTransport.EN_ATTENTE.value
            transport.temps_restant = attente
        else:
            transport.etat = EtatTransport.CHARGEMENT.value
            transport.temps_restant = transport.duree_chargement
            # Prélèvement immédiat si port libre
            self.prelever_ressources_et_bateaux(transport)
            transport._ressources_bateaux_preleves = True
        self.transports.append(transport)
        return True

    def create_and_add_transport(
        self,
        ville_source: Any,
        ville_dest: Any,
        ressources: Dict[str, int],
        nb_bateaux: int,
        joueur_source: Any,
        joueur_dest: Any,
        duree_chargement: float,
        duree_transport: float,
        etat: Optional[EtatTransport] = None,
        temps_restant: Optional[float] = None,
        id_: Optional[int] = None,
    ) -> Transport:
        if id_ is None:
            existing_ids = {t.id for t in self.transports if t.id is not None}
            id_ = 1
            while id_ in existing_ids:
                id_ += 1
        t = Transport(
            ville_source=ville_source,
            ville_dest=ville_dest,
            ressources=ressources,
            nb_bateaux=nb_bateaux,
            joueur_source=joueur_source,
            joueur_dest=joueur_dest,
            duree_chargement=duree_chargement,
            duree_transport=duree_transport,
            etat=etat.value if isinstance(etat, EtatTransport) else (etat if etat is not None else EtatTransport.EN_ATTENTE.value),
            temps_restant=temps_restant,
            id_=id_
        )
        self.ajouter_transport(t)
        return t

    def to_dict(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.transports]

    def from_dict(self, transport_dicts: List[Dict[str, Any]], game_data: Any):
        self.transports.clear()
        for tdict in transport_dicts:
            t = Transport.from_dict(tdict, game_data)
            self.transports.append(t)

    def get_transports_du_joueur(self, joueur: Any) -> List[Transport]:
        return [
            t for t in self.transports
            if getattr(t, "joueur_source", None) == joueur or getattr(t, "joueur_dest", None) == joueur
        ]

    def get_transports_for_player(self, joueur_id: Any) -> List[Transport]:
        def id_of(j):
            return getattr(j, "id_player", j)
        return [
            t for t in self.transports
            if id_of(t.joueur_source) == joueur_id or id_of(t.joueur_dest) == joueur_id
        ]

    def update_transports(self, dt: float = 1.0) -> None:
        for t in list(self.transports):  # Copie pour modification sûre
            if t.etat == EtatTransport.EN_ATTENTE.value:
                t.temps_restant -= dt
                if t.temps_restant <= 0:
                    t.etat = EtatTransport.CHARGEMENT.value
                    t.temps_restant = t.duree_chargement
                    self.prelever_ressources_et_bateaux(t)
                    t._ressources_bateaux_preleves = True
            elif t.etat == EtatTransport.CHARGEMENT.value:
                t.temps_restant -= dt
                if t.temps_restant <= 0:
                    t.etat = EtatTransport.TRANSPORT.value
                    t.temps_restant = t.duree_transport
            elif t.etat == EtatTransport.TRANSPORT.value:
                t.temps_restant -= dt
                if t.temps_restant <= 0:
                    self.crediter_destinataire(t)
                    # Propagation de la peste à l'arrivée
                    if getattr(t.ville_source, "has_plague", False):
                        t.ville_dest.has_plague = True
                    notif_mgr = getattr(self.game_data, "notification_manager", None)
                    try:
                        dest_name = getattr(t.ville_dest, "name", str(t.ville_dest))
                        src_name = getattr(t.ville_source, "name", str(t.ville_source))
                        ressources_str = ", ".join(
                            f"{k}: {v}" for k, v in t.ressources.items() if v > 0
                        ) or "Aucune"
                        if notif_mgr and hasattr(t.joueur_source, "id_player"):
                            msg = (
                                f"Transport de: {src_name}\n"
                                f"Vers: {dest_name}\n"
                                f"Ressources: {ressources_str}\n"
                                f"Votre transport est arrivé à destination."
                            )
                            notif_mgr.add_notification(t.joueur_source.id_player, msg, type="transport")
                        if notif_mgr and t.joueur_dest and hasattr(t.joueur_dest, "id_player"):
                            msg = (
                                f"Transport de: {src_name}\n"
                                f"Vers: {dest_name}\n"
                                f"Ressources: {ressources_str}\n"
                                f"Vous avez reçu un transport."
                            )
                            notif_mgr.add_notification(t.joueur_dest.id_player, msg, type="transport")
                    except Exception:
                        pass
                    dest_is_self = hasattr(t.ville_dest, "owner") and getattr(t.ville_dest, "owner", None) == getattr(t.joueur_source, "id_player", None)
                    if dest_is_self:
                        self.rendre_bateaux(t)
                        self.transports.remove(t)
                    else:
                        t.etat = EtatTransport.RETOUR.value
                        t.temps_restant = t.duree_transport
            elif t.etat == EtatTransport.RETOUR.value:
                t.temps_restant -= dt
                if t.temps_restant <= 0:
                    # Propagation de la peste au retour
                    if getattr(t.ville_dest, "has_plague", False):
                        t.ville_source.has_plague = True
                    self.rendre_bateaux(t)
                    self.transports.remove(t)

    def prelever_ressources_et_bateaux(self, t: Transport) -> None:
        ville_source = t.ville_source
        joueur = t.joueur_source
        print("[DEBUG] ville_source.resources.keys():", list(ville_source.resources.keys()))
        print("[DEBUG] t.ressources:", t.ressources)
        for res, qty in t.ressources.items():
            print(f"[DEBUG] prélèvement {res=} {qty=} (avant: {ville_source.resources.get(res, 'pas de clé')})")
            if qty > 0 and hasattr(ville_source, "resources"):
                ville_source.resources[res] = ville_source.resources.get(res, 0) - qty
                print(f"[DEBUG] nouveau stock {res}: {ville_source.resources[res]}")
        if hasattr(joueur, "ships_available"):
            joueur.ships_available -= t.nb_bateaux

    def crediter_destinataire(self, t: Transport) -> None:
        ville_dest = t.ville_dest
        for res, qty in t.ressources.items():
            if qty > 0 and hasattr(ville_dest, "resources"):
                ville_dest.resources[res] = ville_dest.resources.get(res, 0) + qty

    def rendre_bateaux(self, t: Transport) -> None:
        joueur = t.joueur_source
        if hasattr(joueur, "ships_available"):
            joueur.ships_available += t.nb_bateaux

    def annuler_transport(self, transport_or_id: Any) -> bool:
        if isinstance(transport_or_id, int):
            t = next((tt for tt in self.transports if tt.id == transport_or_id), None)
        else:
            t = transport_or_id

        if not t or t.etat in (EtatTransport.RETOUR.value, EtatTransport.ANNULE.value):
            return False  # Déjà annulé ou impossible à annuler

        notif_mgr = getattr(self.game_data, "notification_manager", None)
        joueur_id = getattr(t.joueur_source, "id_player", None)

        if t.etat in (EtatTransport.EN_ATTENTE.value, EtatTransport.CHARGEMENT.value):
            if getattr(t, "_ressources_bateaux_preleves", False):
                for res, qty in t.ressources.items():
                    if qty > 0 and hasattr(t.ville_source, "resources"):
                        t.ville_source.resources[res] = t.ville_source.resources.get(res, 0) + qty
                if hasattr(t.joueur_source, "ships_available"):
                    t.joueur_source.ships_available += t.nb_bateaux
            t.etat = EtatTransport.ANNULE.value
            t.date_annulation = datetime.utcnow()
            if notif_mgr and joueur_id:
                notif_mgr.add_notification(joueur_id, "Votre transport a été annulé.", type="transport")
            self.transports.remove(t)
            return True

        elif t.etat == EtatTransport.TRANSPORT.value:
            temps_navigue = t.duree_transport - t.temps_restant
            t.etat = EtatTransport.RETOUR.value
            t.temps_restant = max(temps_navigue, 1)
            t.date_annulation = datetime.utcnow()
            if notif_mgr and joueur_id:
                notif_mgr.add_notification(joueur_id, "Votre transport a été annulé : vos bateaux font demi-tour.", type="transport")
            return True

        return False

    def cancel_transport_by_id(self, transport_id: int) -> bool:
        return self.annuler_transport(transport_id)

"""def calculer_distance(ville1: Any, ville2: Any) -> float:
    dx = getattr(ville1, "x", 0) - getattr(ville2, "x", 0)
    dy = getattr(ville1, "y", 0) - getattr(ville2, "y", 0)
    return math.sqrt(dx * dx + dy * dy)"""