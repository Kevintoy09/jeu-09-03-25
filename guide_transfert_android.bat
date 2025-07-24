@echo off
echo.
echo ==========================================
echo 📱 TRANSFERT VERS ANDROID - GUIDE COMPLET
echo ==========================================
echo.
echo 🔌 MÉTHODE 1 : Câble USB (Recommandé)
echo    1. Connectez votre téléphone en USB
echo    2. Activez "Transfert de fichiers" sur Android
echo    3. Ouvrez l'Explorateur Windows
echo    4. Naviguez vers votre téléphone
echo    5. Allez dans le stockage interne
echo    6. Créez le dossier "kivy" à la racine
echo    7. Dans "kivy", créez le dossier "votrejeu"
echo    8. Copiez TOUT le contenu de "kivy_launcher_package"
echo.
echo 📶 MÉTHODE 2 : WiFi/Cloud
echo    - Google Drive, Dropbox, etc.
echo    - Puis téléchargez sur le téléphone
echo.
echo 📁 STRUCTURE FINALE SUR TÉLÉPHONE :
echo    /sdcard/kivy/votrejeu/
echo    ├── main.py
echo    ├── config/
echo    ├── assets/
echo    ├── data/
echo    └── ... (tous les fichiers)
echo.
echo 🎯 DOSSIER À COPIER :
echo    %~dp0kivy_launcher_package\
echo.
pause
