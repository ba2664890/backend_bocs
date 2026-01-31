FROM python:3.11-slim

# Installer les dépendances système pour GeoDjango
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Définir les variables d'environnement pour GDAL
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p media staticfiles logs

# Exposer le port
EXPOSE 8000

# Commande par défaut
CMD ["gunicorn", "fati_backend.wsgi:application", "-b", "0.0.0.0:8000"]
