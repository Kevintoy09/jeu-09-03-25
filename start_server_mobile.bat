@echo off
echo.
echo ========================================
echo 🎮 SERVEUR JEU - MODE MOBILE
echo ========================================
echo.
echo 🌐 IP de ce PC : 192.168.1.246
echo 🔌 Port du serveur : 5000
echo 📱 URL mobile : http://192.168.1.246:5000
echo.
echo ⚠️  IMPORTANT :
echo    - PC et mobile sur le même WiFi
echo    - Désactivez firewall si problème
echo.
echo 🚀 Démarrage du serveur...
echo    Ctrl+C pour arrêter
echo.
cd /d "%~dp0"
python server.py
pause
