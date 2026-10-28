from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled


def check_global_quota(kind: str) -> None:
    limit = getattr(settings, f"AI_DAILY_LIMIT_{kind.upper()}")
    key = f"ai_quota:{kind}:{timezone.now():%Y-%m-%d}"

    cache.add(key, 0, timeout=60 * 60 * 26)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=60 * 60 * 26)
        count = 1

    if count > limit:
        raise Throttled(detail="Le quota IA du jour est atteint, réessaie demain.")
