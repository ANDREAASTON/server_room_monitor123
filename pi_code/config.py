"""
config.py - Load and validate all configuration from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

def _get(key, default=None, required=False):
    val = os.environ.get(key, default)
    if required and val is None:
        raise EnvironmentError(f"Required env var {key} is not set")
    return val

def _bool(key, default="true"):
    return _get(key, default).strip().lower() == "true"

def _int(key, default):
    return int(_get(key, str(default)))

def _float(key, default):
    return float(_get(key, str(default)))

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL       = _get("SUPABASE_URL", required=True)
SUPABASE_SERVICE_KEY = _get("SUPABASE_SERVICE_KEY", required=True)  # service role key
DEVICE_ID          = _get("DEVICE_ID", "pi-serverroom-01")

# ── GPIO (BCM) — DO NOT CHANGE ────────────────────────────────────────────────
PIN_DHT22          = 4    # Physical 7
PIN_GRID_SENSE     = 24   # Physical 18
PIN_MQ_DO          = 17   # Physical 11
PIN_RELAY          = 18   # Physical 12
PIN_LED_GREEN      = 23   # Physical 16
PIN_LED_RED        = 25   # Physical 22
PIN_BUZZER         = 12   # Physical 32
# I2C: SDA=GPIO2 (Physical 3), SCL=GPIO3 (Physical 5) — managed by OS

# ── Thresholds ────────────────────────────────────────────────────────────────
TEMP_HIGH_C        = _float("TEMP_HIGH_C", 35.0)
HUMID_HIGH_PCT     = _float("HUMID_HIGH_PCT", 70.0)

# ── Timing ────────────────────────────────────────────────────────────────────
SENSOR_READ_INTERVAL_SEC  = _int("SENSOR_READ_INTERVAL_SEC", 5)
POST_INTERVAL_SEC         = _int("POST_INTERVAL_SEC", 30)
GRID_STABLE_DELAY_SEC     = _int("GRID_STABLE_DELAY_SEC", 15)
GRID_SENSE_FILTER_MS      = _int("GRID_SENSE_FILTER_MS", 500)
BUZZ_PATTERN_ON_MS        = _int("BUZZ_PATTERN_ON_MS", 200)
BUZZ_PATTERN_OFF_MS       = _int("BUZZ_PATTERN_OFF_MS", 800)

# ── Polarity flags ────────────────────────────────────────────────────────────
# GRID_ACTIVE_HIGH=true  → GPIO24 HIGH means grid is present
# RELAY_ACTIVE_HIGH=true → relay energised when GPIO18 HIGH (active-high board)
# MQ_ACTIVE_HIGH=true    → GPIO17 HIGH means gas/smoke detected
GRID_ACTIVE_HIGH   = _bool("GRID_ACTIVE_HIGH", "true")
RELAY_ACTIVE_HIGH  = _bool("RELAY_ACTIVE_HIGH", "true")
MQ_ACTIVE_HIGH     = _bool("MQ_ACTIVE_HIGH", "true")

# ── LCD I2C ───────────────────────────────────────────────────────────────────
LCD_I2C_ADDRESS    = int(_get("LCD_I2C_ADDRESS", "0x27"), 16)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE           = _get("LOG_FILE", "/var/log/serverroom/monitor.log")
LOG_MAX_BYTES      = _int("LOG_MAX_BYTES", 5_000_000)
LOG_BACKUP_COUNT   = _int("LOG_BACKUP_COUNT", 3)
