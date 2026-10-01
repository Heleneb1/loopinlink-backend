# 🚀 LoopInLink (Backend)

API Django REST Framework pour **LoopInLink**, l'application de création de visuels pour LinkedIn.

---

## 🛠️ Installation et Démarrage en Local

### 1. Cloner le projet et configurer l'environnement virtuel

```bash
git clone <url-du-repo>
cd <nom-du-repo>
python -m venv venv
# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Duplique le fichier `.env.example` en `.env` à la racine du projet et renseigne tes valeurs :

```bash
copy .env.example .env
```

> ⚠️ **Sécurité :** Ne commite **jamais** ton fichier `.env` réel sur Git !

### 4. Générer une nouvelle `SECRET_KEY`

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie la clé générée dans ton fichier `.env` (`DJANGO_SECRET_KEY=...`).

### 5. Lancer les migrations et démarrer le serveur

```bash
python manage.py migrate
python manage.py runserver
```

---

## 📱 Guide de Test sur Mobile (Réseau Local)

Si tu souhaites tester ton application depuis un smartphone connecté au même réseau Wi-Fi :

1. **Trouver l'adresse IP locale de ton PC :**
   Exécute `ipconfig` (Windows) ou `ifconfig` (Mac/Linux) pour récupérer ton IP (ex: `192.168.1.XX`).

2. **Configurer les hôtes et CORS :**
   Ajoute ton IP dans ton `.env` :

   ```env
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.XX
   CORS_ALLOWED_ORIGINS=http://localhost:4200,http://192.168.1.XX:4200
   ```

   > 💡 **Attention aux fins de ligne (LF vs CRLF) :** Assure-toi que ton fichier `.env` est bien enregistré en encodage **LF** pour éviter les erreurs `DisallowedHost`.

3. **Lancer Django sur toutes les interfaces :**

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Lancer Angular (frontend) :**

   ```bash
   ng serve --host 0.0.0.0
   ```

5. **Accéder depuis le téléphone :**
   - App : `http://192.168.1.XX:4200`
   - API : `http://192.168.1.XX:8000/api/`

---

# 🛡️ Mémo Sécurité : Django REST Framework en Production

Bienvenue dans ce guide de sécurisation essentiel pour préparer ton API DRF avant le grand saut en production ! 🚀

Voici le plan des étapes clés que nous allons aborder :

1. Désactiver le mode Debug 🚫
2. Protéger les clés secrètes 🔑
3. Forcer le HTTPS (SSL/TLS) 🔒
4. Configurer l'authentification et les permissions 👮‍♂️
5. Sécuriser les CORS 🌐

---

## 1. Désactiver le mode Debug 🚫

- **Le principe :** En développement, `DEBUG = True` affiche des pages d'erreur détaillées qui révèlent ton code et tes secrets. En production, cela doit impérativement être désactivé pour masquer ces informations aux utilisateurs malveillants.
- **Configuration (`settings.py`) :**

```python
DEBUG = False
ALLOWED_HOSTS = ["ton-domaine.com"]
```

## 2. Ségrégation et protection des clés secrètes 🔑

- **Le principe :** Ne jamais stocker de mots de passe ou de clés API directement dans le code source. Utilise toujours des variables d'environnement (via `.env` et `python-decouple`).
- **Exemple :**

```python
import os
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')
```

## 3. Forcer HTTPS (SSL/TLS) 🔒

- **Le principe :** Chiffrer toutes les données échangées entre le client et ton serveur pour empêcher l'interception de mots de passe, de tokens ou de données personnelles.
- **Configuration (`settings.py`) :**

```python
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
```

## 4. Authentification et Permissions par défaut 👮‍♂️

- **Le principe :** Ne jamais laisser l'accès public par défaut à tes endpoints. Exige au moins un utilisateur authentifié et affine les permissions au cas par cas.
- **Configuration (`settings.py`) :**

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

## 5. Configurer strictement CORS 🌐

- **Le principe :** Restreindre l'accès à ton API uniquement aux domaines autorisés (par exemple, ton frontend de production) pour empêcher les scripts tiers d'interagir frauduleusement avec ton API.
- **Configuration (`settings.py`) :**

```python
CORS_ALLOWED_ORIGINS = [
    "https://ton-frontend.com",
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
```
