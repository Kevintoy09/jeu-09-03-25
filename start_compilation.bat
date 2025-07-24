@echo off
echo.
echo 🚀 COMPILATION APK EN COURS
echo ============================
echo.
echo ⏱️  Durée estimée : 30-60 minutes
echo 📱 Résultat : APK dans le dossier bin/
echo.
echo 🔄 Démarrage de la compilation...
cd /d "%~dp0"
buildozer android debug
echo.
echo ✅ Compilation terminée !
echo 📁 Vérifiez le dossier bin/ pour votre APK
pause
