@echo off
echo.
echo 🔨 COMPILATION APK LOCALE AVEC BUILDOZER
echo ==========================================
echo.
echo ⚠️  ATTENTION : Cette méthode peut prendre du temps
echo    et nécessiter plusieurs ajustements !
echo.
echo 📋 PRÉREQUIS :
echo    - Python 3.9 installé
echo    - Java 8 ou 11 installé
echo    - Android SDK (sera téléchargé automatiquement)
echo.
echo 🚀 INSTALLATION BUILDOZER :
pip install buildozer
pip install cython==0.29.36
echo.
echo 🔧 INITIALISATION :
buildozer init
echo.
echo 📱 COMPILATION (peut prendre 30-60 minutes) :
buildozer android debug
echo.
echo 🎯 RÉSULTAT :
echo    APK disponible dans le dossier bin/
echo.
pause
