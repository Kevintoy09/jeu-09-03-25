# Base de données centralisée des ressources récoltables
# Chaque ressource a un nom, une catégorie (tier), et éventuellement une icône ou une description

RESOURCES = {
    # Ressources de base
    "wood": {
        "name": "Bois",
        "tier": "base",
        "icon": "assets/icons/wood.png",
        "description": "Matériau de base pour la construction."
    },
    "stone": {
        "name": "Pierre",
        "tier": "base",
        "icon": "assets/icons/stone.png",
        "description": "Utilisée pour les bâtiments solides."
    },
    "iron": {
        "name": "Fer",
        "tier": "base",
        "icon": "assets/icons/iron.png",
        "description": "Nécessaire pour l'acier et les outils."
    },
    "papyrus": {
        "name": "Verre",
        "tier": "base",
        "icon": "assets/icons/papyrus.png",
        "description": "Pour les fenêtres et objets spéciaux."
    },
    "cereal": {
        "name": "Céréales",
        "tier": "base",
        "icon": "assets/icons/cereal.png",
        "description": "Nourriture de base pour la population et l'élevage."
    },

    # Ressources intermédiaires
    "horse": {
        "name": "Chevaux",
        "tier": "intermediate",
        "icon": "assets/icons/horse.png",
        "description": "Permet la cavalerie et accélère les transports."
    },
    "marble": {
        "name": "Marbre",
        "tier": "intermediate",
        "icon": "assets/icons/marble.png",
        "description": "Pour les bâtiments prestigieux."
    },
    "glass": {
        "name": "Papyrus",
        "tier": "intermediate",
        "icon": "assets/icons/glass.png",
        "description": "Nécessaire à la recherche et à l'administration."
    },
    "meat": {
        "name": "Viande",
        "tier": "intermediate",
        "icon": "assets/icons/meat.png",
        "description": "Améliore la croissance de la population."
    },

    # Ressources avancées
    "coal": {
        "name": "Charbon",
        "tier": "advanced",
        "icon": "assets/icons/coal.png",
        "description": "Nécessaire pour la production d'acier et d'énergie."
    },
    "gunpowder": {
        "name": "Poudre",
        "tier": "advanced",
        "icon": "assets/icons/gunpowder.png",
        "description": "Permet la fabrication d'armes avancées."
    },
    "spices": {
        "name": "Épices",
        "tier": "advanced",
        "icon": "assets/icons/spices.png",
        "description": "Augmente le bonheur et le commerce."
    },
    "cotton": {
        "name": "Coton",
        "tier": "advanced",
        "icon": "assets/icons/cotton.png",
        "description": "Pour les vêtements et l'industrie textile."
    },
}