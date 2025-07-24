from flask import Blueprint, request, jsonify

server_buildings_bp = Blueprint('server_buildings', __name__)

# Ces variables doivent être injectées ou importées
game_data = None
buildings_manager = None
save_load_manager = None

def inject_dependencies(gd, bm, slm):
    global game_data, buildings_manager, save_load_manager
    game_data = gd
    buildings_manager = bm
    save_load_manager = slm

@server_buildings_bp.route("/build", methods=["POST"])
def build():
    data = request.get_json()
    username = data.get("username")
    player_id = data.get("player_id")
    city_id = data.get("city_id")
    building_name = data.get("building_name")
    slot_index = data.get("slot_index", 0)

    player = None
    if player_id:
        player = game_data.player_manager.get_player(player_id)
    if not player and username:
        player = game_data.player_manager.get_player_by_username(username)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    city = game_data.city_manager.get_city_by_id(city_id)
    if not city or city.owner != player.id_player:
        return jsonify({"error": "City not found or not owned by player"}), 404

    res = buildings_manager.build_or_upgrade_building(
        city_data=city,
        slot_index=slot_index,
        building_name=building_name,
        player_id=player.id_player
    )

    city = game_data.city_manager.get_city_by_id(city_id)
    player = game_data.player_manager.get_player(player.id_player)
    building = None
    try:
        building = city.get_buildings()[slot_index]
        if hasattr(building, "to_dict"):
            building = building.to_dict()
        else:
            building = dict(building.__dict__)
    except Exception:
        building = None

    if res.get("success", False):
        save_load_manager.save_game()
        return jsonify({
            "success": True,
            "message": res.get("message", "Construction ou développement réussi."),
            "city": city.to_dict() if city else None,
            "player": player.to_dict() if player else None,
            "building": building
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": res.get("message", "Erreur lors de la construction ou du développement : condition non remplie."),
            "city": city.to_dict() if city else None,
            "player": player.to_dict() if player else None,
            "building": building
        }), 400

@server_buildings_bp.route("/destroy_building", methods=["POST"])
def destroy_building():
    data = request.get_json()
    player_id = data.get("player_id")
    city_id = data.get("city_id")
    slot_index = data.get("slot_index")
    if not player_id or not city_id or slot_index is None:
        return jsonify({"success": False, "error": "Missing player_id, city_id or slot_index"}), 400

    player = game_data.player_manager.get_player(player_id)
    city = game_data.city_manager.get_city_by_id(city_id)
    if not player:
        return jsonify({"success": False, "error": "Player not found"}), 404
    if not city or city.owner != player.id_player:
        return jsonify({"success": False, "error": "City not found or not owned by player"}), 404

    result = buildings_manager.destroy_building(
        city_data=city,
        slot_index=slot_index,
        player_id=player.id_player
    )
    if isinstance(result, bool):
        result = {"success": result, "message": ""}

    city = game_data.city_manager.get_city_by_id(city_id)
    player = game_data.player_manager.get_player(player.id_player)
    building = None
    try:
        building = city.get_buildings()[slot_index]
        if hasattr(building, "to_dict"):
            building = building.to_dict()
        else:
            building = dict(building.__dict__)
    except Exception:
        building = None

    return jsonify({
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "city": city.to_dict() if city else None,
        "player": player.to_dict() if player else None,
        "building": building
    }), (200 if result.get("success", False) else 400)

@server_buildings_bp.route("/building/details", methods=["POST"])
def building_details():
    data = request.get_json()
    building_name = data.get("building_name")
    level = data.get("level")
    city_id = data.get("city_id")
    player_id = data.get("player_id")
    city = game_data.city_manager.get_city_by_id(city_id) if city_id else None
    player = game_data.player_manager.get_player(player_id) if player_id else None
    details = buildings_manager.get_building_details(building_name, level, city)
    can_finish_instantly = False

    if city and player:
        slot_index = None
        for idx, b in enumerate(city.get_buildings()):
            if b and hasattr(b, "name") and b.name == building_name and getattr(b, "status", None) == "En construction":
                slot_index = idx
                break
        if slot_index is not None:
            building = city.get_buildings()[slot_index]
            remaining = 0
            if hasattr(building, "get_remaining_time"):
                remaining = building.get_remaining_time()
            seuil = 8
            has_research = hasattr(player, "unlocked_research") and any(
                r.lower().replace("_", " ") == "plan de construction" or r.lower() == "plan_de_construction"
                for r in player.unlocked_research
            )
            if has_research and 0 < remaining <= seuil:
                can_finish_instantly = True

    if not details:
        return jsonify({"success": False, "error": "Bâtiment ou niveau inconnu"}), 404
    return jsonify({
        "success": True,
        "details": details,
        "can_finish_instantly": can_finish_instantly
    })

@server_buildings_bp.route("/complete_instantly", methods=["POST"])
def complete_instantly():
    data = request.get_json()
    player_id = data.get("player_id")
    city_id = data.get("city_id")
    slot_index = data.get("slot_index")
    building_name = data.get("building_name")

    if not player_id or not city_id or slot_index is None:
        return jsonify({"success": False, "error": "Missing player_id, city_id or slot_index"}), 400

    player = game_data.player_manager.get_player(player_id)
    city = game_data.city_manager.get_city_by_id(city_id)
    if not player:
        return jsonify({"success": False, "error": "Player not found"}), 404
    if not city or city.owner != player.id_player:
        return jsonify({"success": False, "error": "City not found or not owned by player"}), 404

    res = buildings_manager.complete_instantly(city, slot_index, building_name=building_name)

    building = None
    try:
        building = city.get_buildings()[slot_index]
        if hasattr(building, "to_dict"):
            building = building.to_dict()
        else:
            building = dict(building.__dict__)
    except Exception:
        building = None

    return jsonify({
        "success": bool(res),
        "city": city.to_dict(),
        "building": building
    }), (200 if res else 400)
