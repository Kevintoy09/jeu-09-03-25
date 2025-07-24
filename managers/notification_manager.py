"""
NotificationManager : gère la création, l'affichage et le suivi des notifications du jeu.

Version serveur : notifications par joueur.
- Stocke les notifications par joueur_id.
- Fournit méthodes pour ajouter, récupérer, marquer comme lues pour chaque joueur.
"""

from datetime import datetime
from collections import defaultdict

class NotificationManager:
    def __init__(self):
        # Clé = joueur_id, valeur = liste de notifications
        self.notifications = defaultdict(list)

    def add_notification(self, joueur_id, message, type="info"):
        """Ajoute une notification pour un joueur (joueur_id = int ou str)."""
        print(f"[DEBUG] Notification ajoutée: joueur={joueur_id}, message={message}, type={type}")  # Ajout temporaire
        # Debug print peut rester, ou être remplacé par un vrai log si besoin
        # print(f"[DEBUG] Notification ajoutée: joueur={joueur_id}, message={message}, type={type}")
        self.notifications[joueur_id].append({
            "message": message,
            "type": type,
            "timestamp": datetime.utcnow(),
            "lu": False
        })

    def get_notifications(self, joueur_id):
        """Renvoie la liste des notifications du joueur, les plus récentes en haut."""
        return list(self.notifications[joueur_id])[::-1]

    def mark_all_as_read(self, joueur_id):
        """Marque toutes les notifications du joueur comme lues."""
        for notif in self.notifications[joueur_id]:
            notif["lu"] = True

    def unread_count(self, joueur_id, notif_type=None):
        """
        Renvoie le nombre de notifications non lues pour le joueur.
        - Si notif_type est None : compte toutes les non lues.
        - Si notif_type est un str : compte celles de ce type.
        - Si notif_type est une liste/tuple/set : compte celles de n'importe quel type de cette liste.
        """
        if notif_type is None:
            return sum(1 for n in self.notifications[joueur_id] if not n["lu"])
        if isinstance(notif_type, (list, tuple, set)):
            return sum(1 for n in self.notifications[joueur_id] if not n["lu"] and n.get("type") in notif_type)
        return sum(1 for n in self.notifications[joueur_id] if not n["lu"] and n.get("type") == notif_type)