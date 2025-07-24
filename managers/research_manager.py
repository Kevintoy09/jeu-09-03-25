from models.player import Player

class ResearchManager:
    def __init__(self, game_data):
        self.game_data = game_data

    def unlock_research(self, player_id: str, research: dict) -> bool:
        player = self.game_data.player_manager.get_player(player_id)
        city_manager = self.game_data.city_manager
        owned_cities = city_manager.get_cities_for_player(player.id_player) if player else []
        if not player or not owned_cities:
            print("[SERVER] unlock_research: Joueur ou ville manquante")
            return False
        city = owned_cities[0]
        if research["name"] in player.unlocked_research:
            print("[SERVER] unlock_research: Recherche déjà débloquée")
            return False
        research_points_cost = research["cost"].get("research_points", 0)
        if player.research_points < research_points_cost:
            print(f"[SERVER] unlock_research: Pas assez de points ({player.research_points} < {research_points_cost})")
            return False
        for resource, amount in research["cost"].items():
            if resource == "research_points":
                continue
            if city.resources.get(resource, 0) < amount:
                print(f"[SERVER] unlock_research: Pas assez de {resource} ({city.resources.get(resource, 0)} < {amount})")
                return False
        player.research_points -= research_points_cost
        for resource, amount in research["cost"].items():
            if resource == "research_points":
                continue
            city.resources[resource] -= amount

        player.unlocked_research.append(research["name"])
        self.apply_research_effect(research.get("effect", {}), player)
        print("[SERVER] unlock_research: Recherche débloquée avec succès")
        return True

    def apply_research_effect(self, effect: dict, player: Player):
        if "unlock_building" in effect:
            self.game_data.unlock_building(effect["unlock_building"])
        if "research_bonus" in effect:
            player.apply_research_effects_to_cities(effect, self.game_data.city_manager)
        # Extension possible : autres effets (trade_bonus, exploration_bonus, etc.)