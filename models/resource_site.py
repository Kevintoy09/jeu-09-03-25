# data/resource_site.py

from data.resource_sites_database import RESOURCE_SITE_LEVELS

class ResourceSite:
    def __init__(self, site_type, level=1, donations=0):
        self.site_type = site_type
        self.level = level
        self.donations = donations

    def get_upgrade_cost(self):
        levels = RESOURCE_SITE_LEVELS.get(self.site_type, [])
        if self.level < len(levels):
            return levels[self.level]["upgrade_cost"]
        return None

    def get_max_workers_per_city(self):
        levels = RESOURCE_SITE_LEVELS.get(self.site_type, [])
        if 1 <= self.level <= len(levels):
            return levels[self.level - 1].get("max_workers_per_city", 0)
        return 0

    def get_next_level_benefits(self):
        levels = RESOURCE_SITE_LEVELS.get(self.site_type, [])
        if self.level < len(levels):
            next_level = levels[self.level]
            return {
                "production_per_hour": next_level.get("production_per_hour", 0),
                "max_workers_per_city": next_level.get("max_workers_per_city", 0)
            }
        return None

    def can_upgrade(self):
        cost = self.get_upgrade_cost()
        return cost is not None and self.donations >= sum(cost.values())

    def upgrade(self):
        if self.can_upgrade():
            self.level += 1
            self.donations = 0
            return True
        return False

    def to_dict(self):
        return {
            "site_type": self.site_type,
            "level": self.level,
            "donations": self.donations
        }