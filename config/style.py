from kivy.core.window import Window

# Définir les couleurs et styles pour un thème antique
Window.clearcolor = (0.94, 0.87, 0.8, 1)  # Fond beige clair

STYLES = {
    "header_bar": {
        "height": 50,
        "background_color": [0.9, 0.8, 0.7, 1],  # Effet marbre
        "font_size": 18,
        "font_name": "Roboto",  # Police moderne
        "text_color": [0.3, 0.2, 0.1, 1],  # Texte sombre
    },
    "button": {
        "background_color": [0.6, 0.4, 0.2, 1],  # Brun antique
        "font_size": 16,
        "font_name": "assets/fonts/TrajanPro-Regular.ttf",  # Chemin complet
        "text_color": [0.9, 0.9, 0.8, 1],  # Couleur claire (presque beige)
    },
    "label": {
        "font_size": 15,
        "font_name": "Roboto",  # Police moderne
        "text_color": [0.1, 0.1, 0.1, 1],  # Texte sombre
    },
    "background": {
        "color": [0.94, 0.87, 0.8, 1],  # Beige clair
    },
}

RESOURCE_STYLES = {
    "wood": {"icon": "assets/icons/wood.png", "color": "#8B4513"},
    "stone": {"icon": "assets/icons/stone.png", "color": "#808080"},
    "iron": {"icon": "assets/icons/iron.png", "color": "#B22222"},
    "cereal": {"icon": "assets/icons/cereal.png", "color": "#FFD700"},
    "papyrus": {"icon": "assets/icons/papyrus.png", "color": "#87CEEB"},
}

TEXT_STYLE = {
    "font_size": "18sp",
    "color": [0.3, 0.2, 0.1, 1],  # Texte sombre
    "halign": "center",
    "valign": "middle",
}

BUTTON_STYLE = {
    "size_hint": (0.3, None),
    "height": 40,
    "background_color": [0.9, 0.8, 0.7, 1],  # Effet marbre
    "color": [0.3, 0.2, 0.1, 1],  # Texte sombre
    "font_size": 18,
    "font_name": "Roboto",  # Police moderne
}

def apply_button_style(button):
    """Appliquer un style uniforme à un bouton."""
    style = STYLES["button"]
    button.background_color = style["background_color"]
    button.font_size = style["font_size"]
    button.color = style["text_color"]
    button.font_name = style["font_name"]

def apply_label_style(label):
    """Appliquer un style uniforme à un label."""
    style = STYLES["label"]
    label.font_size = style["font_size"]
    label.color = style["text_color"]
    label.font_name = style["font_name"]

def apply_header_bar_style(header_bar):
    """Appliquer un style uniforme à une barre d'en-tête."""
    style = STYLES["header_bar"]
    header_bar.height = style["height"]
    header_bar.background_color = style["background_color"]
    header_bar.font_size = style["font_size"]
    header_bar.color = style["text_color"]
    header_bar.font_name = style["font_name"]