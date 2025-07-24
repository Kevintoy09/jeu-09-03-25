from flask import Blueprint, request, jsonify, current_app

server_cities_bp = Blueprint('server_cities', __name__)

# On suppose que game_data et save_load_manager sont injectés dans le module principal
game_data = None
save_load_manager = None

def inject_dependencies(gd, slm):
    global game_data, save_load_manager
    game_data = gd
    save_load_manager = slm

@server_cities_bp.route('/set_tax_rate', methods=['POST'])
def set_tax_rate():
    data = request.get_json()
    city_id = data.get("city_id")
    player_id = data.get("player_id")
    tax_rate = data.get("tax_rate")
    if game_data is None or save_load_manager is None:
        return jsonify({"success": False, "error": "Dépendances non injectées"}), 500
    city = game_data.city_manager.get_city_by_id(city_id)
    player = game_data.player_manager.get_player(player_id)
    if not city or not player or city.owner != player.id_player:
        return jsonify({"success": False, "error": "Ville ou joueur non trouvé"}), 404

    # Appliquer le taux d’impôt et MAJ satisfaction/malus
    city.gold_rate = tax_rate
    if tax_rate == 1:
        city.satisfaction_factors["bonus"]["impots"] = 30
        city.satisfaction_factors["malus"].pop("impots", None)
    elif tax_rate == 2:
        city.satisfaction_factors["bonus"]["impots"] = 20
        city.satisfaction_factors["malus"].pop("impots", None)
    elif tax_rate == 3:
        city.satisfaction_factors["bonus"]["impots"] = 10
        city.satisfaction_factors["malus"].pop("impots", None)
    else:
        city.satisfaction_factors["malus"]["impots"] = 0
        city.satisfaction_factors["bonus"].pop("impots", None)

    save_load_manager.save_game()
    return jsonify({"success": True, "city": city.to_dict()})

@server_cities_bp.route('/set_windmill_multiplier', methods=['POST'])
def set_windmill_multiplier():
    data = request.get_json()
    city_id = data.get("city_id")
    windmill_cereal_multiplier = data.get("windmill_cereal_multiplier")
    if game_data is None or save_load_manager is None:
        return jsonify({"success": False, "error": "Dépendances non injectées"}), 500
    city = game_data.city_manager.get_city_by_id(city_id)
    if not city:
        return jsonify({"success": False, "error": "Ville non trouvée"}), 404

    # Met à jour le multiplicateur du moulin (accepte les décimales)
    try:
        city.windmill_cereal_multiplier = float(windmill_cereal_multiplier)
    except Exception:
        city.windmill_cereal_multiplier = 1.0
    save_load_manager.save_game()
    return jsonify({"success": True, "city": city.to_dict()})

# Ajoute ici d'autres routes liées aux villes (ex : /update_city, /rename_city, etc.)

@server_cities_bp.route('/cure_plague', methods=['POST'])
def cure_plague():
    data = request.get_json()
    city_id = data.get("city_id")
    if game_data is None or save_load_manager is None:
        return jsonify({"success": False, "error": "Dépendances non injectées"}), 500
    city = game_data.city_manager.get_city_by_id(city_id)
    if not city:
        return jsonify({"success": False, "error": "Ville non trouvée"}), 404

    # Guérison de la peste
    if not city.has_plague:
        return jsonify({"success": False, "error": "Pas de peste à guérir"}), 400
    city.has_plague = False
    save_load_manager.save_game()
    return jsonify({"success": True, "city": city.to_dict()})

@server_cities_bp.route('/sync/city', methods=['POST'])
def sync_city():
    data = request.get_json()
    city_id = data.get("city_id")
    city = game_data.city_manager.get_city_by_id(city_id)
    if not city:
        return jsonify({"success": False, "error": "Ville introuvable"}), 404
    # Ajout du retour du joueur associé à la ville
    player = None
    if hasattr(city, "owner") and city.owner:
        player = game_data.player_manager.get_player(city.owner)
    return jsonify({
        "success": True,
        "city": city.to_dict(),
        "player": player.to_dict() if player else None
    })

@server_cities_bp.route('/rename_city', methods=['POST'])
def rename_city():
    data = request.get_json()
    city_id = data.get("city_id")
    new_name = data.get("new_name")
    if game_data is None or save_load_manager is None:
        return jsonify({"success": False, "error": "Dépendances non injectées"}), 500
    city = game_data.city_manager.get_city_by_id(city_id)
    if not city:
        return jsonify({"success": False, "error": "Ville non trouvée"}), 404
    city.name = new_name
    save_load_manager.save_game()
    return jsonify({"success": True, "city": city.to_dict()})