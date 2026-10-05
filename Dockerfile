# Image Python légère et récente sur Debian slim
FROM python:3.14-rc-slim

# Évite la création de fichiers .pyc et assure des logs Python en direct
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Mise à jour des paquets et installation des dépendances système nécessaires (ex: PostgreSQL / compilateurs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copie du code source Django
COPY . .

# Port d'écoute du conteneur pour CapRover
EXPOSE 8000

# Commande de lancement (adapter "core" selon le nom du dossier de ton projet Django contenant wsgi.py)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
