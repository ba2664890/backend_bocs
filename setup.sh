#!/bin/bash
# Script de configuration rapide pour FATI Backend

set -e

echo "=========================================="
echo "  FATI Backend - Configuration Rapide"
echo "=========================================="
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✓ Python trouvé: $(python3 --version)"

# Créer l'environnement virtuel
echo ""
echo "📦 Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Environnement virtuel créé"
else
    echo "✓ Environnement virtuel existant"
fi

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
echo ""
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dépendances installées"

# Créer le fichier .env si inexistant
echo ""
echo "⚙️ Configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Fichier .env créé (modifiez-le avec vos paramètres)"
else
    echo "✓ Fichier .env existant"
fi

echo ""
echo "=========================================="
echo "  Configuration terminée!"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo ""
echo "1. Configurez votre base de données PostgreSQL:"
echo "   createdb fati_db"
echo "   psql -d fati_db -c 'CREATE EXTENSION postgis;'"
echo ""
echo "2. Modifiez le fichier .env avec vos paramètres"
echo ""
echo "3. Lancez les migrations et initialisez les données:"
echo "   python manage.py migrate"
echo "   python manage.py create_superuser"
echo "   python manage.py seed_geography"
echo "   python manage.py seed_indicators"
echo "   python manage.py seed_users"
echo ""
echo "4. Démarrez le serveur:"
echo "   python manage.py runserver"
echo ""
echo "📚 Documentation API: http://localhost:8000/api/docs/"
echo ""
