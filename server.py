from flask import Flask, request, jsonify
from datetime import datetime
import logging

from models.game_data import GameData
from managers.buildings_manager import BuildingsManager
from managers.save_load_manager import SaveLoadManager
from data.research_data import RESEARCH_TREE
from managers.game_loop_manager import GameLoopManager
from data.resource_sites_database import RESOURCE_SITE_LEVELS

from routes import server_resource_sites as resource_sites
from routes import server_cities
from routes import server_buildings

# Initialisation des dépendances
game_data = GameData()
save_load_manager = SaveLoadManager(game_data)
city_view = None
buildings_manager = BuildingsManager(game_data, city_view, update_all_callback=None)
game_data.last_update_time = datetime.utcnow()
game_data.accumulated_dt = 0.0
game_data.buildings_manager = buildings_manager

RESOURCE_TO_SITE = {
    "wood": "forest",
    "stone": "quarry",
    "iron": "iron_mine",
    "papyrus": "papyrus_pond",
    "cereal": "grain_field",
    "horse": "horse_ranch",
    "marble": "marble_mine",
    "glass": "glassworks",
    "meat": "pasture",
    "coal": "coal_mine",
    "gunpowder": "gunpowder_lab",
    "spices": "spice_garden",
    "cotton": "cotton_field"
}

# Injection des dépendances dans les Blueprints
resource_sites.game_data = game_data
resource_sites.save_load_manager = save_load_manager
resource_sites.RESOURCE_TO_SITE = RESOURCE_TO_SITE

server_cities.inject_dependencies(game_data, save_load_manager)
server_buildings.inject_dependencies(game_data, buildings_manager, save_load_manager)

app = Flask(__name__)

# Enregistrement des Blueprints (une seule fois chacun)
app.register_blueprint(server_cities.server_cities_bp)
app.register_blueprint(resource_sites.resource_sites_bp)
app.register_blueprint(server_buildings.server_buildings_bp)

# Robustesse au démarrage
try:
    save_load_manager.load_game()
    if not game_data.islands:
        game_data.load_islands_from_json("data/islands.json")
except Exception:
    game_data.load_islands_from_json("data/islands.json")

def update_resources(dt):
    game_data.resource_manager.update_all(dt)

def update_transports(dt):
    game_data.transport_manager.update_transports(dt)

def update_constructions(dt):
    if hasattr(game_data, "buildings_manager"):
        buildings_manager = game_data.buildings_manager
        for city in game_data.city_manager.get_all_cities():
            for i, building in enumerate(city.get_buildings()):
                if building and getattr(building, "status", None) == "En construction":
                    if buildings_manager.get_remaining_time(building) <= 0:
                        construction_key = (city.coords, city.name, i)
                        buildings_manager.complete_task(
                            construction_key=construction_key,
                            city_data=city,
                            slot_index=i
                        )

def update_game_resources_and_transports():
    now = datetime.utcnow()
    dt = (now - game_data.last_update_time).total_seconds()
    game_data.last_update_time = now
    game_data.accumulated_dt += dt
    while game_data.accumulated_dt >= 1.0:
        update_resources(1.0)
        update_transports(1.0)
        update_constructions(1.0)
        game_data.accumulated_dt -= 1.0

game_loop_manager = GameLoopManager(
    game_data=game_data,
    save_load_manager=save_load_manager,
)
game_loop_manager.register_callback(update_game_resources_and_transports)
game_loop_manager.start()

# --- ROUTES PRINCIPALES (hors bâtiments et villes) ---

@app.route("/join", methods=["POST"])
def join():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password", "")
    player = game_data.player_manager.get_player_by_username(username)
    if not player:
        game_data.player_manager.create_account(username, password)
        player = game_data.player_manager.get_player_by_username(username)
        if player:
            game_data.player_manager.players[player.id_player] = player
    else:
        if player.id_player not in game_data.player_manager.players:
            game_data.player_manager.players[player.id_player] = player
    return jsonify({"status": "ok", "player_id": player.id_player})

@app.route("/get_state", methods=["GET"])
def get_state():
    if not game_data.islands:
        game_data.load_islands_from_json("data/islands.json")
    state = game_data.to_dict()
    return jsonify(state)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"success": True, "message": "pong"})


@app.route("/push_city_state", methods=["POST"])
def push_city_state():
    return jsonify({"error": "Pushing city state is not allowed"}), 403

def find_research_by_name(research_name):
    for researches in RESEARCH_TREE.values():
        for research in researches:
            if research["name"] == research_name:
                return research
    return None

@app.route("/unlock_research", methods=["POST"])
def unlock_research():
    data = request.get_json()
    player_id = data.get("player_id")
    research_name = data.get("research_name")
    if not player_id or not research_name:
        return jsonify({"success": False, "error": "Missing player_id or research_name"}), 400
    player = game_data.player_manager.get_player(player_id)
    research = find_research_by_name(research_name)
    if not player or not research:
        return jsonify({"success": False, "error": "Invalid player or research"}), 400
    try:
        success = game_data.research_manager.unlock_research(player_id, research)
        return jsonify({
            "success": success,
            "available_points": player.research_points if player else 0,
            "unlocked_research": player.unlocked_research,
        }), (200 if success else 400)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/add_notification", methods=["POST"])
def add_notification():
    data = request.get_json()
    joueur_id = data.get("joueur_id")
    message = data.get("message")
    notif_type = data.get("type", "info")
    if not joueur_id or not message:
        return jsonify({"success": False, "error": "Missing joueur_id or message"}), 400
    game_data.notification_manager.add_notification(joueur_id, message, notif_type)
    return jsonify({"success": True})

@app.route("/get_notifications", methods=["POST"])
def get_notifications():
    data = request.get_json()
    joueur_id = data.get("joueur_id")
    if not joueur_id:
        return jsonify({"success": False, "error": "Missing joueur_id"}), 400
    notifs = game_data.notification_manager.get_notifications(joueur_id)
    notifications_serialized = []
    for notif in notifs:
        notif_copy = notif.copy()
        ts = notif_copy.get("timestamp")
        if isinstance(ts, datetime):
            notif_copy["timestamp"] = ts.isoformat()
        notifications_serialized.append(notif_copy)
    return jsonify({"success": True, "notifications": notifications_serialized})

@app.route("/mark_notifications_read", methods=["POST"])
def mark_notifications_read():
    data = request.get_json()
    joueur_id = data.get("joueur_id")
    if not joueur_id:
        return jsonify({"success": False, "error": "Missing joueur_id"}), 400
    game_data.notification_manager.mark_all_as_read(joueur_id)
    return jsonify({"success": True})

@app.route("/add_transport", methods=["POST"])
def add_transport():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Missing payload"}), 400
    try:
        ville_source = game_data.city_manager.get_city_by_id(data["ville_source"])
        ville_dest = game_data.city_manager.get_city_by_id(data["ville_dest"])
        joueur_source = game_data.player_manager.get_player(data["joueur_source"])
        joueur_dest = game_data.player_manager.get_player(data["joueur_dest"]) if data.get("joueur_dest") else None
        ressources = data.get("ressources", {})
        nb_bateaux = data.get("nb_bateaux", 1)
        duree_chargement = data.get("duree_chargement", 0)
        duree_transport = data.get("duree_transport", 0)
        etat = str(data.get("etat", "Waiting"))
        temps_restant = data.get("temps_restant", 0)

        if not ville_source or not ville_dest or not joueur_source:
            return jsonify({"success": False, "error": "City or player not found"}), 400
        for k, v in ressources.items():
            if ville_source.resources.get(k, 0) < v:
                return jsonify({"success": False, "error": f"Not enough {k}"}), 400
        if getattr(joueur_source, 'ships_available', 0) < nb_bateaux:
            return jsonify({"success": False, "error": "Not enough ships"}), 400
        t = game_data.transport_manager.create_and_add_transport(
            ville_source, ville_dest, ressources, nb_bateaux, joueur_source, joueur_dest, 
            duree_chargement, duree_transport, etat=etat, temps_restant=temps_restant
        )
        return jsonify({
            "success": True,
            "transport": t.to_dict() if hasattr(t, "to_dict") else t,
            "transport_id": getattr(t, "id", None),
            "ville_source": ville_source.to_dict()
        })
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/cancel_transport", methods=["POST"])
def cancel_transport():
    data = request.get_json()
    transport_id = data.get("transport_id")
    if not transport_id:
        return jsonify({"success": False, "error": "Missing transport_id"}), 400
    try:
        result = game_data.transport_manager.cancel_transport_by_id(transport_id)
        if result:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Transport not found or already completed"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_transports_for_player", methods=["POST"])
def get_transports_for_player():
    data = request.get_json()
    joueur_id = data.get("joueur_id")
    if not joueur_id:
        return jsonify({"success": False, "error": "Missing joueur_id"}), 400
    try:
        transports = game_data.transport_manager.get_transports_for_player(joueur_id)
        return jsonify({
            "success": True,
            "transports": [t.to_dict() for t in transports]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/buy_ship", methods=["POST"])
def buy_ship():
    data = request.get_json()
    joueur_id = data.get("joueur_id")
    ville_id = data.get("ville_id")
    if not joueur_id or not ville_id:
        return jsonify({"success": False, "error": "Missing joueur_id or ville_id"}), 400
    try:
        joueur = game_data.player_manager.get_player(joueur_id)
        ville = game_data.city_manager.get_city_by_id(ville_id)
        if not joueur or not ville:
            return jsonify({"success": False, "error": "City or player not found"}), 400
        price = int(100 * (1.5 ** (getattr(joueur, 'ships', 1) - 1)))
        if ville.resources.get("gold", 0) < price:
            return jsonify({"success": False, "error": "Not enough gold"}), 400
        ville.resources["gold"] -= price
        joueur.ships = getattr(joueur, "ships", 0) + 1
        joueur.ships_available = getattr(joueur, "ships_available", 0) + 1
        return jsonify({
            "success": True,
            "ships": joueur.ships,
            "ships_available": joueur.ships_available,
            "gold": ville.resources["gold"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add_diamonds', methods=['POST'])
def add_diamonds():
    data = request.get_json()
    player_id = data.get('player_id')
    amount = int(data.get('amount', 0))
    player = game_data.player_manager.get_player(player_id)
    if not player:
        return jsonify({"success": False, "message": "Joueur introuvable"})
    player.add_diamonds(amount)
    return jsonify({"success": True, "diamonds": player.diamonds})

@app.route("/select_city", methods=["POST"])
def select_city():
    data = request.get_json()
    username = data.get("username")
    city_id = data.get("city_id")
    if not username or not city_id:
        return jsonify({"error": "Missing parameters"}), 400
    player = game_data.player_manager.get_player_by_username(username)
    city = game_data.city_manager.get_city_by_id(city_id)
    if not player or not city:
        return jsonify({"error": "Player or city not found"}), 404
    if city.owner not in ["", player.id_player]:
        return jsonify({"error": "City already owned by someone else"}), 403
    city.owner = player.id_player
    save_load_manager.save_game()
    return jsonify({"status": "city_selected", "city": city.to_dict(), "city_id": getattr(city, 'id', None)})

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)