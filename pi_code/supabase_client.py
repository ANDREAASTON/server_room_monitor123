"""
supabase_client.py - HTTP POST telemetry to Supabase REST API with retry + backoff
"""
import time
import logging
import requests
import config

log = logging.getLogger(__name__)

_HEADERS = {
    "apikey":        config.SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}
_URL = f"{config.SUPABASE_URL}/rest/v1/telemetry"

def post_telemetry(temperature_c, humidity_pct, gas_alert,
                   grid_present, power_source, alarm_active,
                   max_retries=3):
    """
    Insert one telemetry row via Supabase REST.
    Retries up to max_retries times with exponential backoff.
    Returns True on success, False on failure.
    """
    payload = {
        "device_id":     config.DEVICE_ID,
        "temperature_c": temperature_c,
        "humidity_pct":  humidity_pct,
        "gas_alert":     bool(gas_alert),
        "grid_present":  bool(grid_present),
        "power_source":  power_source,
        "alarm_active":  bool(alarm_active),
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(_URL, json=payload, headers=_HEADERS, timeout=10)
            if resp.status_code in (200, 201):
                log.debug("Telemetry posted (attempt %d)", attempt)
                return True
            else:
                log.warning("Supabase returned %d on attempt %d: %s",
                            resp.status_code, attempt, resp.text[:200])
        except requests.exceptions.RequestException as e:
            log.warning("HTTP error on attempt %d: %s", attempt, e)

        if attempt < max_retries:
            backoff = 2 ** attempt  # 2s, 4s, …
            log.info("Retrying in %d s …", backoff)
            time.sleep(backoff)

    log.error("Failed to post telemetry after %d attempts", max_retries)
    return False
