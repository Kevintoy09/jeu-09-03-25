"""
Script de diagnostic pour la compilation APK
Vérifie l'environnement et les prérequis
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python():
    """Vérifie la version Python"""
    version = sys.version_info
    print(f"🐍 Python : {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Version Python compatible")
        return True
    else:
        print("   ❌ Python 3.8+ requis")
        return False

def check_java():
    """Vérifie Java"""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            java_info = result.stderr.split('\n')[0]
            print(f"☕ Java : {java_info}")
            print("   ✅ Java disponible")
            return True
    except:
        pass
    
    print("❌ Java non trouvé")
    print("   💡 Installez OpenJDK 11 : https://adoptium.net/")
    return False

def check_buildozer():
    """Vérifie Buildozer"""
    try:
        result = subprocess.run(['buildozer', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"🔨 Buildozer : {result.stdout.strip()}")
            print("   ✅ Buildozer installé")
            return True
    except:
        pass
    
    print("❌ Buildozer non installé")
    return False

def check_project_structure():
    """Vérifie la structure du projet"""
    required_files = ['main.py', 'buildozer.spec']
    missing = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing.append(file)
    
    return len(missing) == 0

def main():
    print("🔍 DIAGNOSTIC COMPILATION APK")
    print("=" * 40)
    
    checks = [
        ("Python", check_python()),
        ("Java", check_java()),
        ("Buildozer", check_buildozer()),
        ("Structure projet", check_project_structure())
    ]
    
    print("\n📊 RÉSUMÉ :")
    all_ok = True
    for name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {name}")
        if not status:
            all_ok = False
    
    if all_ok:
        print("\n🚀 PRÊT POUR LA COMPILATION !")
        print("   Exécutez : buildozer android debug")
    else:
        print("\n⚠️  PRÉREQUIS MANQUANTS")
        print("   Installez les éléments manquants avant de compiler")
    
    print("=" * 40)

if __name__ == "__main__":
    main()
