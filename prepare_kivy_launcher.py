#!/usr/bin/env python3
"""
Script de préparation pour Kivy Launcher
Copie le jeu vers la structure attendue par Kivy Launcher
"""

import os
import shutil
from pathlib import Path

def prepare_for_kivy_launcher():
    """Prépare le projet pour Kivy Launcher"""
    
    print("🎮 Préparation du jeu pour Kivy Launcher...")
    
    # Dossier source (votre jeu)
    source_dir = Path(__file__).parent
    
    # Dossier de destination pour Kivy Launcher
    # Sur Android, ce sera /sdcard/kivy/votrejeu/
    dest_dir = source_dir / "kivy_launcher_package"
    
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    dest_dir.mkdir(exist_ok=True)
    
    # Fichiers et dossiers à copier
    items_to_copy = [
        "main.py",
        "assets/",
        "config/",
        "data/", 
        "managers/",
        "models/",
        "views/",
        "popups/",
        "widgets/",
        "database/",
        "network/",
        "requirements.txt"
    ]
    
    print("📁 Copie des fichiers...")
    for item in items_to_copy:
        source_path = source_dir / item
        dest_path = dest_dir / item
        
        if source_path.exists():
            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
                print(f"   ✅ {item}")
            elif source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                print(f"   ✅ {item}/")
        else:
            print(f"   ⚠️  {item} non trouvé")
    
    # Créer un fichier de config spécial pour Kivy Launcher
    create_launcher_config(dest_dir)
    
    print(f"\n🎯 Package prêt dans : {dest_dir}")
    print("\n📱 ÉTAPES SUIVANTES :")
    print("1. Installez 'Kivy Launcher' depuis Google Play Store")
    print("2. Créez le dossier /sdcard/kivy/ sur votre téléphone")
    print(f"3. Copiez le contenu de '{dest_dir}' vers /sdcard/kivy/votrejeu/")
    print("4. Ouvrez Kivy Launcher et sélectionnez votre jeu")
    
    return dest_dir

def create_launcher_config(dest_dir):
    """Crée un fichier de configuration pour optimiser l'exécution"""
    
    config_content = '''# Configuration pour Kivy Launcher
[app]
title = VotreJeu
package.name = votrejeu
package.domain = org.example

[kivy]
log_level = 2

[graphics]
multisamples = 0
'''
    
    config_path = dest_dir / "android.txt"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("   ✅ Configuration Kivy Launcher créée")

if __name__ == "__main__":
    prepare_for_kivy_launcher()
