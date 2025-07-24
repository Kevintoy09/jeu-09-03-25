@echo off
echo.
echo ==========================================
echo 📱 TRANSFERT VIA ADB (Méthode alternative)
echo ==========================================
echo.
echo ⚠️  PRÉREQUIS :
echo    - ADB installé sur PC
echo    - Debug USB activé sur Android
echo.
echo 💻 COMMANDES À EXÉCUTER :
echo.
echo 1. Vérifier connexion :
echo    adb devices
echo.
echo 2. Créer dossiers :
echo    adb shell mkdir -p /sdcard/kivy/votrejeu
echo.
echo 3. Transférer fichiers :
echo    adb push "kivy_launcher_package/*" /sdcard/kivy/votrejeu/
echo.
echo 4. Vérifier :
echo    adb shell ls /sdcard/kivy/votrejeu/
echo.
echo 🔧 INSTALLATION ADB :
echo    https://developer.android.com/studio/command-line/adb
echo.
pause
