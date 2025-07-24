#!/bin/bash
# 🚀 Script de compilation APK avec Docker
# Évite tous les problèmes de versions et de dépendances

echo "🐳 COMPILATION APK AVEC DOCKER - ANTI-DEBUG"
echo "=" * 50

# Vérification Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé !"
    echo "💻 Installez Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker détecté"

# Construction de l'image
echo "🔨 Construction de l'environnement de compilation..."
docker build -t apk-builder .

if [ $? -eq 0 ]; then
    echo "✅ Image Docker créée avec succès"
else
    echo "❌ Erreur lors de la création de l'image"
    exit 1
fi

# Compilation APK
echo "🚀 Compilation de l'APK..."
echo "⏳ Ceci peut prendre 30-60 minutes la première fois..."

docker run --rm -v "$(pwd)":/src apk-builder

if [ $? -eq 0 ]; then
    echo "🎉 COMPILATION RÉUSSIE !"
    echo "📱 APK disponible dans: bin/"
    ls -la bin/*.apk 2>/dev/null || echo "❌ Aucun APK trouvé"
else
    echo "❌ Erreur de compilation"
    echo "📋 Vérifiez les logs ci-dessus"
fi

echo "=" * 50
