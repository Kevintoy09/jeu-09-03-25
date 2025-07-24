"""
Fichier centralisé pour tous les messages d'information et d'erreur utilisateur du jeu,
et pour l'affichage des popups Kivy.
"""

# --- MESSAGES D'ERREUR GENERIQUES ---
ERROR_INVALID_DONATION = "Entrée don invalide."
ERROR_NO_ACTIVE_CITY = "Aucune ville active sélectionnée."
ERROR_CITY_NOT_ON_ISLAND = "Vous ne pouvez affecter des ouvriers que depuis une ville présente sur cette île."
ERROR_NOT_ENOUGH_RESOURCE = "Pas assez de ressources dans la ville."
ERROR_SERVER = "Erreur serveur."
ERROR_LOADING_SITE = "Erreur de chargement du site."
ERROR_UNKNOWN = "Une erreur inconnue est survenue."

# --- MESSAGES D'INFORMATION ---
INFO_DONATION_SUCCESS = "Don effectué avec succès !"
INFO_WORKERS_ASSIGNED = "Ouvriers affectés avec succès."

# --- MESSAGES AVEC PARAMETRES ---
def not_enough_resource(resource):
    return f"Pas assez de {resource} dans la ville."

def donation_success(resource, amount):
    return f"Don de {amount} {resource} effectué avec succès !"

# --- AFFICHAGE POPUP KIVY ---
def show_error_popup(message, title="Erreur"):
    from kivy.uix.popup import Popup
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.boxlayout import BoxLayout

    popup = Popup(title=title, size_hint=(0.8, 0.4))
    content = BoxLayout(orientation='vertical')
    msg_label = Label(text=message)
    content.add_widget(msg_label)
    close_button = Button(text='Fermer', size_hint_y=None, height='40dp')
    close_button.bind(on_press=popup.dismiss)
    content.add_widget(close_button)
    popup.content = content
    popup.open()