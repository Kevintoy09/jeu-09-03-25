"""
Script de test de connectivité pour Android
Vérifie si le serveur est accessible depuis le mobile
"""

import requests
import socket
from config.mobile_config import get_server_url

def test_network_connectivity():
    """Test la connectivité réseau pour Android"""
    
    print("🔍 TEST DE CONNECTIVITÉ RÉSEAU")
    print("=" * 40)
    
    # 1. Vérifier l'IP locale
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"🖥️  IP de ce PC : {local_ip}")
    
    # 2. Tester l'URL configurée
    server_url = get_server_url()
    print(f"🌐 URL serveur configurée : {server_url}")
    
    # 3. Tester si le serveur répond
    try:
        print("\n🚀 Test de connexion au serveur...")
        response = requests.get(f"{server_url}/", timeout=5)
        print(f"✅ Serveur accessible ! Status: {response.status_code}")
        
        # Test d'une route de jeu
        try:
            test_response = requests.get(f"{server_url}/players", timeout=5)
            print(f"✅ API du jeu fonctionne ! Status: {test_response.status_code}")
        except Exception as e:
            print(f"⚠️  API du jeu non accessible : {e}")
            
    except Exception as e:
        print(f"❌ Serveur non accessible : {e}")
        print("\n🔧 SOLUTIONS POSSIBLES :")
        print("   1. Lancez 'python server.py' dans un autre terminal")
        print("   2. Vérifiez le firewall Windows")
        print("   3. Assurez-vous que PC et mobile sont sur le même WiFi")
    
    print("\n📱 POUR TESTER DEPUIS MOBILE :")
    print(f"   Ouvrez le navigateur mobile et allez à : {server_url}")
    print("   Vous devriez voir la réponse du serveur")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    test_network_connectivity()
