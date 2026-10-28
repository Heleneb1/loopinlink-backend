# IA dans LoopInLink (texte + images)

Génération de texte et d'images, à coût nul pour la phase gratuite du projet.

## Architecture

```
Angular → DRF (auth + throttling + quota global) → Fournisseur IA → DRF → Angular
```

Angular n'appelle jamais l'API IA directement : les clés restent côté serveur.
`ai/services.py` isole les fournisseurs, on peut en changer sans toucher au reste.

## Fournisseurs

| Usage  | Fournisseur                           | Coût                         |
| ------ | ------------------------------------- | ---------------------------- |
| Texte  | Google Gemini (`gemini-flash-latest`) | Palier gratuit               |
| Images | Cloudflare Workers AI (FLUX schnell)  | 10 000 Neurons/jour gratuits |

Groq a été écarté (inscription bloquée). Au-delà du gratuit, une image 1024×1024
coûte environ 0,0006 $.

> Les paliers gratuits servent surtout à tester. Avant de rendre le projet payant,
> relire les conditions d'utilisation de chaque fournisseur et passer sur leurs
> offres payantes.

## Configuration

Variables dans `.env` (à côté de `manage.py`, jamais commité) :

```
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-flash-latest
CF_ACCOUNT_ID=...
CF_API_TOKEN=...
# optionnel
AI_DAILY_LIMIT_TEXT=500
AI_DAILY_LIMIT_IMAGE=150
```

`settings.py` (lecture avec `python-decouple`) :

```python
GEMINI_API_KEY = config("GEMINI_API_KEY")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-flash-latest")
CF_ACCOUNT_ID = config("CF_ACCOUNT_ID")
CF_API_TOKEN = config("CF_API_TOKEN")
AI_DAILY_LIMIT_TEXT = config("AI_DAILY_LIMIT_TEXT", default=500, cast=int)
AI_DAILY_LIMIT_IMAGE = config("AI_DAILY_LIMIT_IMAGE", default=150, cast=int)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}
```

Table du cache : `python manage.py createcachetable`.
App déclarée dans `INSTALLED_APPS` avec simplement `'ai'`.

## Structure de l'app `ai/`

| Fichier       | Rôle                                                                                                                                               |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services.py` | Appels Gemini (3 essais, timeout 60 s) et Cloudflare, erreur `AIUnavailable` (503)                                                                 |
| `views.py`    | `GenerateTextView`, `GenerateImageView` : authentification, throttling par utilisateur (30 textes/h, 10 images/h), prompt limité à 1000 caractères |
| `quota.py`    | Quota global journalier via le cache (`check_global_quota`), erreur 429                                                                            |
| `urls.py`     | `text/` et `image/`                                                                                                                                |
| `images.py`   | (optionnel) conversion/redimensionnement en WebP avec Pillow                                                                                       |

Routes : `POST /ai/text/` et `POST /ai/image/`, branchées dans le `urls.py` **du projet**
avec `path("ai/", include("ai.urls"))` (pas dans celui de `accounts`).
Réponses : `{"text": "..."}` et `{"image": "data:image/...;base64,..."}`.

## Décisions

- Les images générées ne sont **pas** enregistrées automatiquement : elles restent
  temporaires dans le navigateur.
- Si l'utilisateur en garde une, elle passe par le circuit d'upload existant
  (`DesignImage.file`, avec `validate_image_size`, `validate_image_extension`, `rename_image`).
  Côté Angular, convertir la data URL en `File` avec un nom en `.webp`.
- Pas de cache des réponses pour l'instant (résultats variables, base64 lourd).

## Tests réalisés

```bash
py manage.py shell
```

- Texte et image : `200` depuis le shell avec `APIClient(HTTP_HOST="localhost")`.
- Sans connexion : `401`.
- Quota global : `200`, `200`, `429` avec une limite à 2.

## Plan

- [x] 1. Clés API dans `.env`
- [x] 2. App `ai` et configuration
- [x] 3. `services.py` (Gemini + Cloudflare)
- [x] 4. Endpoints DRF et tests
- [ ] 5. Branchement Angular (`AiService`, composant, envoi vers `DesignImage`)
- [x] 6. Quota global
- [ ] 7. Modération des prompts, signalement des contenus
- [ ] 8. Production : `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, mention IA/RGPD

## Sécurité

- Ne jamais afficher une sortie IA avec `[innerHTML]` côté Angular.
- Les erreurs détaillées vont dans les logs, l'utilisateur reçoit un message générique.
- Le throttling DRF et le quota global utilisent un cache partagé (base de données).
- Mentionner l'usage de l'IA et le transfert de prompts à des tiers dans la politique de confidentialité (RGPD).
