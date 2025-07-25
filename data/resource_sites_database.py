RESOURCE_SITE_LEVELS = {
    # Ressources de base
    "wood": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 200}, "upgrade_time": 5},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 300}, "upgrade_time": 7},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 500}, "upgrade_time": 8},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 600}, "upgrade_time": 10},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 700}, "upgrade_time": 12},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 800}, "upgrade_time": 15},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 1200}, "upgrade_time": 40},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 1600}, "upgrade_time": 45},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 1900}, "upgrade_time": 50},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "stone": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 100, "stone": 200}, "upgrade_time": 4},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 200, "stone": 400}, "upgrade_time": 5},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 400, "stone": 800}, "upgrade_time": 6},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 800, "stone": 1600}, "upgrade_time": 7},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 1600, "stone": 3200}, "upgrade_time": 8},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 3200, "stone": 6400}, "upgrade_time": 35},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 6400, "stone": 12800}, "upgrade_time": 40},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 12800, "stone": 25600}, "upgrade_time": 45},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 25600, "stone": 51200}, "upgrade_time": 50},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "iron": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 120, "stone": 120, "iron": 200}, "upgrade_time": 10},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 240, "stone": 240, "iron": 400}, "upgrade_time": 15},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 480, "stone": 480, "iron": 800}, "upgrade_time": 20},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 960, "stone": 960, "iron": 1600}, "upgrade_time": 25},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 1920, "stone": 1920, "iron": 3200}, "upgrade_time": 30},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 3840, "stone": 3840, "iron": 6400}, "upgrade_time": 35},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 7680, "stone": 7680, "iron": 12800}, "upgrade_time": 40},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 15360, "stone": 15360, "iron": 25600}, "upgrade_time": 45},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 30720, "stone": 30720, "iron": 51200}, "upgrade_time": 50},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "papyrus": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 150, "stone": 150, "papyrus": 200}, "upgrade_time": 10},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 300, "stone": 300, "papyrus": 400}, "upgrade_time": 15},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 600, "stone": 600, "papyrus": 800}, "upgrade_time": 20},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 1200, "stone": 1200, "papyrus": 1600}, "upgrade_time": 25},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 2400, "stone": 2400, "papyrus": 3200}, "upgrade_time": 30},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 4800, "stone": 4800, "papyrus": 6400}, "upgrade_time": 35},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 9600, "stone": 9600, "papyrus": 12800}, "upgrade_time": 40},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 19200, "stone": 19200, "papyrus": 25600}, "upgrade_time": 45},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 38400, "stone": 38400, "papyrus": 51200}, "upgrade_time": 50},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "cereal": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 100, "cereal": 200}, "upgrade_time": 6},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 200, "cereal": 400}, "upgrade_time": 8},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 400, "cereal": 800}, "upgrade_time": 10},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 800, "cereal": 1600}, "upgrade_time": 12},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 1600, "cereal": 3200}, "upgrade_time": 14},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 3200, "cereal": 6400}, "upgrade_time": 16},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 6400, "cereal": 12800}, "upgrade_time": 18},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 12800, "cereal": 25600}, "upgrade_time": 20},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 25600, "cereal": 51200}, "upgrade_time": 22},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 24},
    },

    # Ressources intermédiaires
    "horse": {
        1: {"max_workers_per_city": 6, "upgrade_cost": {"wood": 100, "meat": 100, "horse": 100}, "upgrade_time": 10},
        2: {"max_workers_per_city": 10, "upgrade_cost": {"wood": 200, "meat": 200, "horse": 200}, "upgrade_time": 15},
        3: {"max_workers_per_city": 14, "upgrade_cost": {"wood": 300, "meat": 300, "horse": 300}, "upgrade_time": 20},
        4: {"max_workers_per_city": 18, "upgrade_cost": {"wood": 400, "meat": 400, "horse": 400}, "upgrade_time": 25},
        5: {"max_workers_per_city": 22, "upgrade_cost": {"wood": 500, "meat": 500, "horse": 500}, "upgrade_time": 30},
        6: {"max_workers_per_city": 26, "upgrade_cost": {"wood": 600, "meat": 600, "horse": 600}, "upgrade_time": 35},
        7: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 700, "meat": 700, "horse": 700}, "upgrade_time": 40},
        8: {"max_workers_per_city": 34, "upgrade_cost": {"wood": 800, "meat": 800, "horse": 800}, "upgrade_time": 45},
        9: {"max_workers_per_city": 38, "upgrade_cost": {"wood": 900, "meat": 900, "horse": 900}, "upgrade_time": 50},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "marble": {
        1: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 120, "stone": 200, "marble": 200}, "upgrade_time": 10},
        2: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 240, "stone": 400, "marble": 400}, "upgrade_time": 15},
        3: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 480, "stone": 800, "marble": 800}, "upgrade_time": 20},
        4: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 960, "stone": 1600, "marble": 1600}, "upgrade_time": 25},
        5: {"max_workers_per_city": 25, "upgrade_cost": {"wood": 1920, "stone": 3200, "marble": 3200}, "upgrade_time": 30},
        6: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 3840, "stone": 6400, "marble": 6400}, "upgrade_time": 35},
        7: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 7680, "stone": 12800, "marble": 12800}, "upgrade_time": 40},
        8: {"max_workers_per_city": 42, "upgrade_cost": {"wood": 15360, "stone": 25600, "marble": 25600}, "upgrade_time": 45},
        9: {"max_workers_per_city": 49, "upgrade_cost": {"wood": 30720, "stone": 51200, "marble": 51200}, "upgrade_time": 50},
        10: {"max_workers_per_city": 57, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "glass": {
        1: {"max_workers_per_city": 6, "upgrade_cost": {"wood": 100, "glass": 100}, "upgrade_time": 10},
        2: {"max_workers_per_city": 10, "upgrade_cost": {"wood": 200, "glass": 200}, "upgrade_time": 15},
        3: {"max_workers_per_city": 14, "upgrade_cost": {"wood": 300, "glass": 300}, "upgrade_time": 20},
        4: {"max_workers_per_city": 18, "upgrade_cost": {"wood": 400, "glass": 400}, "upgrade_time": 25},
        5: {"max_workers_per_city": 22, "upgrade_cost": {"wood": 500, "glass": 500}, "upgrade_time": 30},
        6: {"max_workers_per_city": 26, "upgrade_cost": {"wood": 600, "glass": 600}, "upgrade_time": 35},
        7: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 700, "glass": 700}, "upgrade_time": 40},
        8: {"max_workers_per_city": 34, "upgrade_cost": {"wood": 800, "glass": 800}, "upgrade_time": 45},
        9: {"max_workers_per_city": 38, "upgrade_cost": {"wood": 900, "glass": 900}, "upgrade_time": 50},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "meat": {
        1: {"max_workers_per_city": 6, "upgrade_cost": {"wood": 100, "meat": 100}, "upgrade_time": 10},
        2: {"max_workers_per_city": 10, "upgrade_cost": {"wood": 200, "meat": 200}, "upgrade_time": 15},
        3: {"max_workers_per_city": 14, "upgrade_cost": {"wood": 300, "meat": 300}, "upgrade_time": 20},
        4: {"max_workers_per_city": 18, "upgrade_cost": {"wood": 400, "meat": 400}, "upgrade_time": 25},
        5: {"max_workers_per_city": 22, "upgrade_cost": {"wood": 500, "meat": 500}, "upgrade_time": 30},
        6: {"max_workers_per_city": 26, "upgrade_cost": {"wood": 600, "meat": 600}, "upgrade_time": 35},
        7: {"max_workers_per_city": 30, "upgrade_cost": {"wood": 700, "meat": 700}, "upgrade_time": 40},
        8: {"max_workers_per_city": 34, "upgrade_cost": {"wood": 800, "meat": 800}, "upgrade_time": 45},
        9: {"max_workers_per_city": 38, "upgrade_cost": {"wood": 900, "meat": 900}, "upgrade_time": 50},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },

    # Ressources avancées
    "coal": {
        1: {"max_workers_per_city": 4, "upgrade_cost": {"wood": 200, "coal": 100}, "upgrade_time": 15},
        2: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 400, "coal": 200}, "upgrade_time": 20},
        3: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 600, "coal": 300}, "upgrade_time": 25},
        4: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 800, "coal": 400}, "upgrade_time": 30},
        5: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 1000, "coal": 500}, "upgrade_time": 35},
        6: {"max_workers_per_city": 24, "upgrade_cost": {"wood": 1200, "coal": 600}, "upgrade_time": 40},
        7: {"max_workers_per_city": 28, "upgrade_cost": {"wood": 1400, "coal": 700}, "upgrade_time": 45},
        8: {"max_workers_per_city": 32, "upgrade_cost": {"wood": 1600, "coal": 800}, "upgrade_time": 50},
        9: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 1800, "coal": 900}, "upgrade_time": 55},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "gunpowder": {
        1: {"max_workers_per_city": 4, "upgrade_cost": {"wood": 200, "coal": 100, "gunpowder": 100}, "upgrade_time": 20},
        2: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 400, "coal": 200, "gunpowder": 200}, "upgrade_time": 25},
        3: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 600, "coal": 300, "gunpowder": 300}, "upgrade_time": 30},
        4: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 800, "coal": 400, "gunpowder": 400}, "upgrade_time": 35},
        5: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 1000, "coal": 500, "gunpowder": 500}, "upgrade_time": 40},
        6: {"max_workers_per_city": 24, "upgrade_cost": {"wood": 1200, "coal": 600, "gunpowder": 600}, "upgrade_time": 45},
        7: {"max_workers_per_city": 28, "upgrade_cost": {"wood": 1400, "coal": 700, "gunpowder": 700}, "upgrade_time": 50},
        8: {"max_workers_per_city": 32, "upgrade_cost": {"wood": 1600, "coal": 800, "gunpowder": 800}, "upgrade_time": 55},
        9: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 1800, "coal": 900, "gunpowder": 900}, "upgrade_time": 60},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "spices": {
        1: {"max_workers_per_city": 4, "upgrade_cost": {"wood": 200, "spices": 100}, "upgrade_time": 20},
        2: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 400, "spices": 200}, "upgrade_time": 25},
        3: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 600, "spices": 300}, "upgrade_time": 30},
        4: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 800, "spices": 400}, "upgrade_time": 35},
        5: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 1000, "spices": 500}, "upgrade_time": 40},
        6: {"max_workers_per_city": 24, "upgrade_cost": {"wood": 1200, "spices": 600}, "upgrade_time": 45},
        7: {"max_workers_per_city": 28, "upgrade_cost": {"wood": 1400, "spices": 700}, "upgrade_time": 50},
        8: {"max_workers_per_city": 32, "upgrade_cost": {"wood": 1600, "spices": 800}, "upgrade_time": 55},
        9: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 1800, "spices": 900}, "upgrade_time": 60},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
    "cotton": {
        1: {"max_workers_per_city": 4, "upgrade_cost": {"wood": 200, "cotton": 100}, "upgrade_time": 20},
        2: {"max_workers_per_city": 8, "upgrade_cost": {"wood": 400, "cotton": 200}, "upgrade_time": 25},
        3: {"max_workers_per_city": 12, "upgrade_cost": {"wood": 600, "cotton": 300}, "upgrade_time": 30},
        4: {"max_workers_per_city": 16, "upgrade_cost": {"wood": 800, "cotton": 400}, "upgrade_time": 35},
        5: {"max_workers_per_city": 20, "upgrade_cost": {"wood": 1000, "cotton": 500}, "upgrade_time": 40},
        6: {"max_workers_per_city": 24, "upgrade_cost": {"wood": 1200, "cotton": 600}, "upgrade_time": 45},
        7: {"max_workers_per_city": 28, "upgrade_cost": {"wood": 1400, "cotton": 700}, "upgrade_time": 50},
        8: {"max_workers_per_city": 32, "upgrade_cost": {"wood": 1600, "cotton": 800}, "upgrade_time": 55},
        9: {"max_workers_per_city": 36, "upgrade_cost": {"wood": 1800, "cotton": 900}, "upgrade_time": 60},
        10: {"max_workers_per_city": 40, "upgrade_cost": {}, "upgrade_time": 60},
    },
}