from data.resources_database import RESOURCES

# Génère dynamiquement les clés de ressources récoltables
RESOURCE_KEYS = list(RESOURCES.keys())

TIME_SCALE = 1.0

NORMAL_CONSUMPTION_RATE = 0.1

DEFAULT_STORAGE_CAPACITY = {
    "wood": 1800,
    "stone": 2000,
    "iron": 2000,
    "cereal": 2000,
    "papyrus": 2000,
    "horse": 1600,
    "marble": 1600,
    "glass": 1600,
    "meat": 1600,
    "coal": 1600,
    "gunpowder": 1600,
    "spices": 1600,
    "cotton": 1600,
    "gold": 1000000,
    "population": 1000
}

DEFAULT_RESOURCES = {
    "wood": 1500,
    "stone": 3000,
    "iron": 1000,
    "cereal": 2000,
    "papyrus": 1000,
    "horse": 10,
    "marble": 20,
    "glass": 30,
    "meat": 40,
    "coal": 50,
    "gunpowder": 60,
    "spices": 70,
    "cotton": 80,
    "gold": 80,
    "population_total": 40,
    "population_free": 40,
    "research_points": 800,
    "production_bonus": {
        "wood": 0,
        "stone": 0,
        "iron": 0,
        "cereal": 0,
        "papyrus": 0,
        "horse": 0,
        "marble": 0,
        "glass": 0,
        "meat": 0,
        "coal": 0,
        "gunpowder": 0,
        "spices": 0,
        "cotton": 0,
        "gold": 0
    },
    "building_bonus": {
        "wood": 0,
        "stone": 0,
        "iron": 0,
        "cereal": 0,
        "papyrus": 0,
        "horse": 0,
        "marble": 0,
        "glass": 0,
        "meat": 0,
        "coal": 0,
        "gunpowder": 0,
        "spices": 0,
        "cotton": 0,
        "gold": 0
    },
    "research_bonus": {
        "wood": 4,
        "stone": 8,
        "iron": 0,
        "cereal": 0,
        "papyrus": 0,
        "horse": 0,
        "marble": 0,
        "glass": 0,
        "meat": 0,
        "coal": 0,
        "gunpowder": 0,
        "spices": 0,
        "cotton": 0,
        "gold": 0
    },
}

STARTING_DIAMONDS = 100