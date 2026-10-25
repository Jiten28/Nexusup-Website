"""Feed image selection and approval. Pure functions: no Django, no network.

Policy is unchanged and deliberately strict: a remote image is stored only when the
source owner has enabled image reuse (``allow_images``) AND the image's exact hostname is
listed in ``image_hosts``. Nothing here invents, rewrites or upgrades a publisher URL.
"""
from urllib.parse import urlsplit

MAX_URL = 1000

# Machine-readable reasons, shown by ``news_report`` / ``backfill_images``.
OK = 'ok'
NO_IMAGE = 'no_image_in_feed'
UNSAFE = 'unsafe_or_non_https_url'
NOT_ENABLED = 'source_allow_images_is_off'
NO_HOSTS = 'source_has_no_approved_image_hosts'
HOST_NOT_APPROVED = 'host_not_in_approved_image_hosts'


def safe_https_url(value):
    """Return the URL when it is a plain, credential-free https URL of sane length, else ''."""
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if not value or len(value) > MAX_URL:
        return ''
    try:
        parts = urlsplit(value)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            return ''
        parts.port  # raises ValueError on a malformed port
    except (ValueError, AttributeError):
        return ''
    return value


def best_candidate(candidates):
    """Pick one image from ``(url, declared_width_or_None)`` pairs, in feed order.

    The widest *declared* width wins so a 1200px media:content beats a 240px thumbnail.
    Ties, and candidates without a width, keep feed order. Unsafe URLs are skipped.
    """
    best, best_width = '', -1
    for url, width in candidates:
        url = safe_https_url(url)
        if not url:
            continue
        try:
            width = int(width or 0)
        except (TypeError, ValueError):
            width = 0
        if width > best_width:
            best, best_width = url, width
    return best


def image_decision(url, allow_images, hosts):
    """Return ``(approved_url_or_empty, reason)``."""
    if not url:
        return '', NO_IMAGE
    safe = safe_https_url(url)
    if not safe:
        return '', UNSAFE
    if not allow_images:
        return '', NOT_ENABLED
    approved = {h.lower() for h in (hosts or []) if isinstance(h, str) and h}
    if not approved:
        return '', NO_HOSTS
    if urlsplit(safe).hostname.lower() not in approved:
        return '', HOST_NOT_APPROVED
    return safe, OK


def approved_remote_image(url, allow_images, hosts):
    return image_decision(url, allow_images, hosts)[0]
