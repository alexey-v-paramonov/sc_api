import json
import logging

import requests

from django.conf import settings

logger = logging.getLogger('django')

YANDEX_SMARTCAPTCHA_VALIDATE_URL = "https://smartcaptcha.yandexcloud.net/validate"


def verify_smartcaptcha(token, ip=None):
    """Validate a Yandex SmartCaptcha token against the Yandex backend.

    Returns True when the token is valid. Following Yandex's reference
    implementation, we "fail open" (return True) on any Yandex-side or
    network error so that a captcha outage does not block sign-ups.

    An empty token is always treated as a failed check, and when no server
    key is configured (e.g. local dev) the check is skipped.
    """
    server_key = getattr(settings, "SMARTCAPTCHA_SERVER_KEY", "")
    if not server_key:
        logger.warning("SMARTCAPTCHA_SERVER_KEY is not set; skipping captcha check")
        return True

    if not token:
        return False

    try:
        resp = requests.get(
            YANDEX_SMARTCAPTCHA_VALIDATE_URL,
            params={"secret": server_key, "token": token, "ip": ip or ""},
            timeout=1,
        )
    except requests.RequestException as exc:
        logger.error("SmartCaptcha request failed: %s", exc)
        return True  # fail open on network error

    server_output = resp.content.decode()
    if resp.status_code != 200:
        logger.error(
            "SmartCaptcha error: code=%s; message=%s", resp.status_code, server_output
        )
        return True  # fail open per Yandex reference implementation

    return json.loads(server_output).get("status") == "ok"
