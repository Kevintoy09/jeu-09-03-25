buildings_database = {
    "Hôtel de Ville": {
        "description": "Gère la capacité maximale de la population et la limite de nourriture.",
        "image": "assets/buildings/town_hall.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 100, "stone": 50}, "construction_time": 6, "effect": {"population_growth": 1.2, "food_capacity": 50, "population_capacity": 100}},
            {"level": 2, "cost": {"wood": 200, "stone": 100}, "construction_time": 15, "effect": {"population_growth": 3.3, "food_capacity": 65, "population_capacity": 220}},
            {"level": 3, "cost": {"wood": 400, "stone": 200}, "construction_time": 16, "effect": {"population_growth": 4.5, "food_capacity": 80, "population_capacity": 300}},
        ],
    },
    "Windmill": {
        "description": "Permet d'augmenter la croissance de la population et la capacité de nourriture.",
        "image": "assets/buildings/windmill.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 120, "stone": 80}, "construction_time": 2, "effect": {"food_supply": 10, "cereal_consumption_multiplier": 2}},
            {"level": 2, "cost": {"wood": 240, "stone": 160}, "construction_time": 4, "effect": {"food_supply": 20, "cereal_consumption_multiplier": 3}},
            {"level": 3, "cost": {"wood": 480, "stone": 320}, "construction_time": 36, "effect": {"food_supply": 40, "cereal_consumption_multiplier": 4}}
        ],
    },
    "Academy": {
        "description": "Permet de produire des points de recherche.",
        "image": "assets/buildings/academy.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 150, "papyrus": 50}, "construction_time": 5, "effect": {"research_points_per_worker": 1, "max_workers": 25}},
            {"level": 2, "cost": {"wood": 300, "papyrus": 100}, "construction_time": 13, "effect": {"research_points_per_worker": 1.5, "max_workers": 50}},
            {"level": 3, "cost": {"wood": 600, "papyrus": 200}, "construction_time": 18, "effect": {"research_points_per_worker": 2, "max_workers": 75}},
        ],
    },
    "Entrepôt": {
        "description": "Gère la capacité de stockage des ressources.",
        "image": "assets/buildings/warehouse.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {
                "level": 1,
                "cost": {"wood": 100, "stone": 50},
                "construction_time": 10,
                "effect": {
                    "storage": {
                        "wood": 1000, "stone": 1000, "iron": 1000, "cereal": 1000, "papyrus": 1000,
                        "meat": 500, "marble": 500, "horse": 500, "glass": 500,
                        "gunpowder": 100, "coal": 100, "cotton": 100, "spices": 100
                    },
                    "secure_storage": {
                        "wood": 100, "stone": 100, "iron": 100, "cereal": 100, "papyrus": 100,
                        "meat": 50, "marble": 50, "horse": 50, "glass": 50,
                        "gunpowder": 10, "coal": 10, "cotton": 10, "spices": 10
                    }
                }
            },
            {
                "level": 2,
                "cost": {"wood": 200, "stone": 100},
                "construction_time": 20,
                "effect": {
                    "storage": {
                        "wood": 2000, "stone": 2000, "iron": 2000, "cereal": 2000, "papyrus": 2000,
                        "meat": 1500, "marble": 1500, "horse": 1500, "glass": 1500,
                        "gunpowder": 500, "coal": 500, "cotton": 500, "spices": 500
                    },
                    "secure_storage": {
                        "wood": 1000, "stone": 1000, "iron": 1000, "cereal": 1000, "papyrus": 1000,
                        "meat": 500, "marble": 500, "horse": 500, "glass": 500,
                        "gunpowder": 50, "coal": 50, "cotton": 50, "spices": 50
                    }
                }
            },
            {
                "level": 3,
                "cost": {"wood": 400, "stone": 200},
                "construction_time": 30,
                "effect": {
                    "storage": {
                        "wood": 3000, "stone": 3000, "iron": 3000, "cereal": 3000, "papyrus": 3000,
                        "meat": 2500, "marble": 2500, "horse": 2500, "glass": 2500,
                        "gunpowder": 1000, "coal": 1000, "cotton": 1000, "spices": 1000
                    },
                    "secure_storage": {
                        "wood": 2000, "stone": 2000, "iron": 2000, "cereal": 2000, "papyrus": 2000,
                        "meat": 1000, "marble": 1000, "horse": 1000, "glass": 1000,
                        "gunpowder": 100, "coal": 100, "cotton": 100, "spices": 100
                    }
                }
            },
        ],
    },
    "Caserne": {
        "description": "Permet de produire des unités militaires.",
        "image": "assets/buildings/barracks.png",
        "category": "defensive",
        "required_research": "Agriculture",
        "levels": [
            {"level": 1, "cost": {"wood": 150, "stone": 100}, "construction_time": 15, "effect": {"unit_production": "infantry"}},
            {"level": 2, "cost": {"wood": 300, "stone": 200}, "construction_time": 25, "effect": {"unit_production": "archers"}},
            {"level": 3, "cost": {"wood": 600, "stone": 400}, "construction_time": 35, "effect": {"unit_production": "cavalry"}},
        ],
    },
    "Port": {
        "description": "Permet de produire des bateaux pour le commerce et la guerre.",
        "image": "assets/buildings/port.png",
        "category": "marine",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 200, "stone": 150}, "construction_time": 2, "effect": {"ship_production": "transport", "loading_speed": 10}},
            {"level": 2, "cost": {"wood": 400, "stone": 300}, "construction_time": 3, "effect": {"ship_production": "merchant", "loading_speed": 14}},
            {"level": 3, "cost": {"wood": 800, "stone": 600}, "construction_time": 4, "effect": {"ship_production": "warship", "loading_speed": 19}},
        ],
    },
    "Muraille": {
        "description": "Augmente la défense de la ville.",
        "image": "assets/buildings/wall.png",
        "category": "defensive",
        "required_research": "Agriculture",
        "levels": [
            {"level": 1, "cost": {"wood": 200, "stone": 150}, "construction_time": 15, "effect": {"defense": 50}},
            {"level": 2, "cost": {"wood": 400, "stone": 300}, "construction_time": 25, "effect": {"defense": 100}},
            {"level": 3, "cost": {"wood": 800, "stone": 600}, "construction_time": 35, "effect": {"defense": 150}},
        ],
    },
    "Scierie": {
        "description": "Augmente la production de bois.",
        "image": "assets/buildings/sawmill.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 150, "stone": 100}, "construction_time": 5, "effect": {"resource_bonus": {"wood": 10}}},
            {"level": 2, "cost": {"wood": 300, "stone": 200}, "construction_time": 10, "effect": {"resource_bonus": {"wood": 20}}},
            {"level": 3, "cost": {"wood": 600, "stone": 400}, "construction_time": 35, "effect": {"resource_bonus": {"wood": 30}}},
        ],
    },
    "Mine": {
        "description": "Augmente la production des ressources de base (fer, céréales, pierre, verre).",
        "image": "assets/buildings/mine.png",
        "category": "general",
        "required_research": "Extraction Minière",
        "levels": [
            {"level": 1, "cost": {"wood": 200, "stone": 150}, "construction_time": 5, "effect": {"resource_bonus": {"stone": 10, "iron": 10, "cereal": 10, "papyrus": 10}}},
            {"level": 2, "cost": {"wood": 400, "stone": 300, "iron": 100}, "construction_time": 10, "effect": {"resource_bonus": {"stone": 20, "iron": 20, "cereal": 20, "papyrus": 20}}},
            {"level": 3, "cost": {"wood": 800, "stone": 600, "iron": 200}, "construction_time": 45, "effect": {"resource_bonus": {"stone": 30, "iron": 30, "cereal": 30, "papyrus": 30}}},
        ],
    },
    "Ambassade": {
        "description": "Permet de fonder et de gérer des colonies. Chaque niveau augmente le nombre maximum de colonies.",
        "image": "assets/buildings/ambassade.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 200, "stone": 150}, "construction_time": 5, "effect": { "max_colonies": 2 }},
            {"level": 2, "cost": {"wood": 100, "stone": 100, "iron": 100}, "construction_time": 10, "effect": { "max_colonies": 3 }},
            {"level": 3, "cost": {"wood": 100, "stone": 100, "iron": 100}, "construction_time": 5, "effect": { "max_colonies": 4 }},
        ],
    },
    "Atelier d'Architecte": {
        "description": "Réduit les coûts et le temps de construction des bâtiments.",
        "image": "assets/buildings/architect_workshop.png",
        "category": "general",
        "required_research": "Architecte",
        "levels": [
            {"level": 1, "cost": {"wood": 120, "stone": 100}, "construction_time": 10, "effect": {"construction_cost_reduction": 10, "construction_time_reduction": 10}},
            {"level": 2, "cost": {"wood": 240, "stone": 200}, "construction_time": 15, "effect": {"construction_cost_reduction": 20, "construction_time_reduction": 20}},
            {"level": 3, "cost": {"wood": 480, "stone": 400}, "construction_time": 20, "effect": {"construction_cost_reduction": 30, "construction_time_reduction": 30}},
        ],
    },
    "Thermes": {
        "description": "Améliore le bonheur et la santé de la population.",
        "image": "assets/buildings/thermes.png",
        "category": "general",
        "required_research": None,
        "levels": [
            {"level": 1, "cost": {"wood": 100, "stone": 50}, "construction_time": 5, "effect": {"cleanliness_capacity": 50, "satisfaction_bonus": 5}},
            {"level": 2, "cost": {"wood": 200, "stone": 100}, "construction_time": 10, "effect": {"cleanliness_capacity": 150, "satisfaction_bonus": 10}},
            {"level": 3, "cost": {"wood": 400, "stone": 200}, "construction_time": 15, "effect": {"cleanliness_capacity": 200, "satisfaction_bonus": 15}},
        ],
    },
}