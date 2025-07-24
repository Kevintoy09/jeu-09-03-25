from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from data.resource_sites_database import RESOURCE_SITE_LEVELS

resource_sites_bp = Blueprint('resource_sites', __name__)

game_data = None
save_load_manager = None
RESOURCE_TO_SITE = None

@resource_sites_bp.route("/assign_workers", methods=["POST"])
def assign_workers():
    data = request.get_json()
    city_id = data.get("city_id")
    resource = data.get("resource")
    workers = int(data.get("workers", 0))
    player_id = data.get("player_id")

    global game_data, RESOURCE_TO_SITE
    city = game_data.city_manager.get_city_by_id(city_id)
    if not city or city.owner != player_id:
        return jsonify({"success": False, "status": "error", "error": "Ville introuvable ou non possédée"})

    # Limite le nombre d’ouvriers à la capacité max du site
    island = None
    for ile in game_data.islands:
        elements = ile.get("elements", []) if isinstance(ile, dict) else getattr(ile, "elements", [])
        for c in elements:
            if hasattr(c, "id") and getattr(c, "id") == city_id:
                island = ile
                break
        if island:
            break

    max_workers = None
    if island:
        resource_sites = [e for e in (island.get("elements", []) if isinstance(island, dict) else getattr(island, "elements", [])) if isinstance(e, dict) and "type" in e]
        site_type_backend = RESOURCE_TO_SITE.get(resource, resource)
        for s in resource_sites:
            if s.get("type") == site_type_backend:
                level = s.get("level", 1)
                site_config = RESOURCE_SITE_LEVELS.get(resource, {})
                level_config = site_config.get(level, {})
                max_workers = level_config.get("max_workers_per_city", None)
                break

    if max_workers is not None:
        workers = min(workers, max_workers)
    # Vérification de la population libre
    free_population = getattr(city, "free_population", None)
    if free_population is not None:
        workers = min(workers, free_population)
        # Met à jour la population libre après affectation
        city.free_population = max(0, free_population - workers)
    if not hasattr(city, "resource_workers"):
        city.resource_workers = {}
    city.resource_workers[resource] = workers
    city.workers_assigned[resource] = workers

    return jsonify({
        "success": True,
        "status": "ok",
        "workers_assigned": workers,
        "free_population": getattr(city, "free_population", None)
    })

@resource_sites_bp.route('/resource_site_info', methods=['POST'])
def resource_site_info():
    data = request.get_json()
    site_type = data.get("site_type")   # <-- CORRECTION : récupère bien le site_type
    player_id = data.get("player_id")
    island_coords = data.get("island_coords")

    # --- ici, il faut accéder à game_data, save_load_manager, RESOURCE_TO_SITE depuis l'app principale ---
    global game_data, save_load_manager, RESOURCE_TO_SITE

    islands = getattr(game_data, "islands", [])
    ile_trouvee = None
    if island_coords:
        for ile in islands:
            coords = ile.get("coords") if isinstance(ile, dict) else getattr(ile, "coords", None)
            if coords and tuple(coords) == tuple(island_coords):
                ile_trouvee = ile
                break
    else:
        for ile in islands:
            elements = ile.get("elements", []) if isinstance(ile, dict) else getattr(ile, "elements", [])
            for city in elements:
                if hasattr(city, "owner") and getattr(city, "owner") == player_id:
                    ile_trouvee = ile
                    break
            if ile_trouvee:
                break

    if not ile_trouvee:
        return jsonify({"error": "Île ou site non trouvé", "success": False})

    elements = ile_trouvee.get("elements", []) if isinstance(ile_trouvee, dict) else getattr(ile_trouvee, "elements", [])
    cities = []
    resource_sites = []
    for elem in elements:
        if hasattr(elem, "owner"):  # City object
            cities.append(elem)
        elif isinstance(elem, dict) and "type" in elem:
            resource_sites.append(elem)

    site = None
    site_type_backend = RESOURCE_TO_SITE.get(site_type, site_type)
    for s in resource_sites:
        if s.get("type") == site_type_backend:
            # Gestion du timer et passage de niveau
            if s.get("upgrade_start_time"):
                start_time = s["upgrade_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                now = datetime.now(timezone.utc)
                upgrade_time = s.get("upgrade_time", 0)
                elapsed = (now - start_time).total_seconds()
                if elapsed >= upgrade_time:
                    s["level"] = s.get("level", 1) + 1
                    s.pop("upgrade_start_time", None)
                    s.pop("upgrade_time", None)
                    s["donations"] = {}  # Remise à zéro des dons pour le nouveau niveau
                    save_load_manager.save_game()
            site = s
            break
    if not site:
        return jsonify({"error": "Île ou site non trouvé", "success": False})

    # Infos du niveau courant
    level = site.get("level", 1)
    site_config = RESOURCE_SITE_LEVELS.get(site_type, {})
    level_config = site_config.get(level, {})
    max_workers_per_city = level_config.get("max_workers_per_city", 0)
    upgrade_time = level_config.get("upgrade_time", 0)
    upgrade_cost = level_config.get("upgrade_cost", {})

    next_level_config = site_config.get(level + 1, {})
    next_level_benefits = {}
    if next_level_config:
        next_level_benefits = {
            "max_workers_per_city": next_level_config.get("max_workers_per_city", 0),
            "production_per_hour": next_level_config.get("production_per_hour", 0)
        }

    # Liste des villes du joueur sur l’île
    player_cities = []
    others = []
    for city in cities:
        city_id = getattr(city, "id", None)
        city_name = getattr(city, "name", "")
        resource_workers = getattr(city, "resource_workers", {})
        # Synchronisation dynamique du nombre d'ouvriers selon la population totale
        population_total = None
        if hasattr(city, "resources"):
            population_total = city.resources.get("population_total", None)
        # On ajuste le nombre d'ouvriers affectés si la population totale a diminué
        if population_total is not None:
            total_assigned = sum(resource_workers.values())
            if total_assigned > population_total:
                # On réduit les ouvriers affectés à chaque ressource, en priorité sur les ressources avancées
                # (ou on répartit équitablement, ici on réduit dans l'ordre de la dict)
                surplus = total_assigned - population_total
                for res in sorted(resource_workers, key=lambda r: -resource_workers[r]):
                    if surplus <= 0:
                        break
                    removed = min(resource_workers[res], surplus)
                    resource_workers[res] -= removed
                    if hasattr(city, "workers_assigned"):
                        city.workers_assigned[res] = resource_workers[res]
                    surplus -= removed
        workers = resource_workers.get(site_type, 0)
        owner = getattr(city, "owner", None)
        # Récupère la population libre de façon robuste
        free_pop = getattr(city, "free_population", None)
        if free_pop is None and hasattr(city, "resources"):
            free_pop = city.resources.get("population_free", None)
        city_info = {
            "city_id": city_id,
            "city_name": city_name,
            "workers": int(workers),
            "max": int(max_workers_per_city),
            "free_population": int(free_pop) if free_pop is not None else 0
        }
        if owner == player_id:
            player_cities.append(city_info)
        elif owner:
            others.append({
                "player": owner,
                "city_name": city_name,
                "workers": workers
            })

    all_cities = []
    for city in cities:
        city_id = getattr(city, "id", None)
        city_name = getattr(city, "name", "")
        resource_workers = getattr(city, "resource_workers", {})
        workers = resource_workers.get(site_type, 0)
        owner = getattr(city, "owner", None)
        all_cities.append({
            "city_id": city_id,
            "city_name": city_name,
            "player": owner,
            "workers": workers
        })

    donations = site.get("donations", {})

    # Timer d'upgrade en cours ?
    upgrade_in_progress = False
    upgrade_remaining_time = 0
    if site.get("upgrade_start_time"):
        start_time = site["upgrade_start_time"]
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        now = datetime.now(timezone.utc)
        current_upgrade_time = site.get("upgrade_time", 0)
        elapsed = (now - start_time).total_seconds()
        if elapsed < current_upgrade_time:
            upgrade_in_progress = True
            upgrade_remaining_time = int(current_upgrade_time - elapsed)
        else:
            upgrade_in_progress = False
            upgrade_remaining_time = 0

    return jsonify({
        "level": level,
        "max_workers_per_city": max_workers_per_city,
        "upgrade_time": upgrade_time,
        "upgrade_cost": upgrade_cost,
        "player_cities": player_cities,
        "others": others,
        "all_cities": all_cities,
        "donations": donations,
        "donations_history": site.get("donations_history", {}),
        "next_level_benefits": next_level_benefits,
        "upgrade_in_progress": upgrade_in_progress,
        "upgrade_remaining_time": upgrade_remaining_time,
        "success": True
    })

@resource_sites_bp.route('/donate_to_resource_site', methods=['POST'])
def donate_to_resource_site():
    data = request.get_json()
    site_type = data.get("site_type")   # <-- AJOUT ICI pour cohérence
    player_id = data.get("player_id")
    city_id = data.get("city_id")
    island_coords = tuple(data.get("island_coords"))
    amount = int(data.get("amount", 0))
    resource_type = data.get("resource_type")

    global game_data, save_load_manager, RESOURCE_TO_SITE

    islands = getattr(game_data, "islands", [])

    # Recherche de l’île
    ile_trouvee = None
    if island_coords:
        for ile in islands:
            coords = ile.get("coords") if isinstance(ile, dict) else getattr(ile, "coords", None)
            if coords and tuple(coords) == tuple(island_coords):
                ile_trouvee = ile
                break
    else:
        for ile in islands:
            elements = ile.get("elements", []) if isinstance(ile, dict) else getattr(ile, "elements", [])
            for city in elements:
                if hasattr(city, "owner") and getattr(city, "owner") == player_id:
                    ile_trouvee = ile
                    break
            if ile_trouvee:
                break

    if not ile_trouvee:
        return jsonify({"success": False, "error": "Île introuvable"}), 404

    # Trouver la ville demandée par le client (ville active)
    city_obj = None
    elements = ile_trouvee.get("elements", []) if isinstance(ile_trouvee, dict) else getattr(ile_trouvee, "elements", [])
    for elem in elements:
        if hasattr(elem, "id") and getattr(elem, "id", None) == city_id:
            city_obj = elem
            break

    # Vérifier que la ville existe, appartient au joueur, et est bien sur cette île
    if not city_obj or getattr(city_obj, "owner", None) != player_id:
        return jsonify({"success": False, "error": "Veuillez sélectionner une ville à vous présente sur cette île pour faire un don."}), 400

    # Recherche du site de ressource sur l'île
    site = None
    site_type_backend = RESOURCE_TO_SITE.get(site_type, site_type)
    for s in elements:
        if isinstance(s, dict) and s.get("type") == site_type_backend:
            # Vérification passage de niveau si timer terminé
            if s.get("upgrade_start_time"):
                start_time = s["upgrade_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                now = datetime.now(timezone.utc)
                upgrade_time = s.get("upgrade_time", 0)
                elapsed = (now - start_time).total_seconds()
                if elapsed >= upgrade_time:
                    s["level"] = s.get("level", 1) + 1
                    s.pop("upgrade_start_time", None)
                    s.pop("upgrade_time", None)
                    s["donations"] = {}  # Remise à zéro des dons pour le nouveau niveau
                    save_load_manager.save_game()
            site = s
            break
    if not site:
        return jsonify({"success": False, "error": "Site non trouvé sur l'île"}), 404

    # Limiter le don à ce qu'il manque pour l'upgrade (niveau courant)
    level = site.get("level", 1)
    site_config = RESOURCE_SITE_LEVELS.get(site_type, {})
    level_config = site_config.get(level, {})
    upgrade_cost = level_config.get("upgrade_cost", {})
    if resource_type not in upgrade_cost:
        return jsonify({"success": False, "error": f"La ressource {resource_type} n'est pas requise pour l'amélioration."}), 400

    # Calculer le total donné pour ce niveau UNIQUEMENT (on reset à chaque passage de niveau)
    donations = site.setdefault("donations", {})
    total_donated = sum(city_dons.get(resource_type, 0) for city_dons in donations.values())
    max_possible = max(0, upgrade_cost[resource_type] - total_donated)
    if max_possible <= 0:
        return jsonify({"success": False, "error": f"Le site a déjà reçu tout le {resource_type} nécessaire pour ce niveau."}), 400
    if amount > max_possible:
        amount = max_possible

    # Vérifier et déduire les ressources de la ville
    if getattr(city_obj, "resources", None) is None or city_obj.resources.get(resource_type, 0) < amount:
        return jsonify({"success": False, "error": f"Pas assez de {resource_type} dans la ville."}), 400
    city_obj.resources[resource_type] -= amount

    # Ajouter la donation pour ce niveau
    donations.setdefault(city_id, {})
    donations[city_id][resource_type] = donations[city_id].get(resource_type, 0) + amount

    # Historique cumulé des dons (jamais remis à zéro)
    site.setdefault("donations_history", {})
    site["donations_history"].setdefault(city_id, {})
    site["donations_history"][city_id][resource_type] = site["donations_history"][city_id].get(resource_type, 0) + amount

    upgraded = False

    # 1. Si un timer est en cours, vérifier s'il doit faire passer le niveau
    if site.get("upgrade_start_time"):
        start_time = site["upgrade_start_time"]
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        now = datetime.now(timezone.utc)
        elapsed = (now - start_time).total_seconds()
        upgrade_time = site.get("upgrade_time", 0)
        if elapsed >= upgrade_time:
            # Passage de niveau
            site["level"] = site.get("level", 1) + 1
            site.pop("upgrade_start_time", None)
            site.pop("upgrade_time", None)
            site["donations"] = {}  # On ne touche PAS à donations_history !
            upgraded = True
            save_load_manager.save_game()

    # 2. Si pas de timer, vérifier si on peut le démarrer (après la donation)
    if not site.get("upgrade_start_time"):
        # Recalcule le total après la donation
        donations_total = {}
        for city_dons in donations.values():
            for res, val in city_dons.items():
                donations_total[res] = donations_total.get(res, 0) + val
        upgrade_possible = all(donations_total.get(res, 0) >= cost for res, cost in upgrade_cost.items())
        if upgrade_possible:
            site["upgrade_start_time"] = datetime.now(timezone.utc).isoformat()
            site["upgrade_time"] = level_config.get("upgrade_time", 0)
            upgraded = False
            save_load_manager.save_game()

    save_load_manager.save_game()

    return jsonify({
        "success": True,
        "upgraded": upgraded,
        "current_level": site.get("level", 1),
        "upgrade_in_progress": bool(site.get("upgrade_start_time")),
        "upgrade_remaining_time": site.get("upgrade_time", 0)
    })