"""
sensors.py - DHT22 temperature/humidity + MQ gas sensor (digital) + grid sense
"""
import time
import logging
import board
import adafruit_dht
from gpiozero import Button
import config

log = logging.getLogger(__name__)

# ── DHT22 ─────────────────────────────────────────────────────────────────────
_dht = adafruit_dht.DHT22(board.D4, use_pulseio=False)

def read_dht22():
    """Return (temperature_c, humidity_pct) or (None, None) on failure."""
    for attempt in range(3):
        try:
            temp = _dht.temperature
            hum  = _dht.humidity
            if temp is not None and hum is not None:
                return round(temp, 1), round(hum, 1)
        except RuntimeError as e:
            log.debug("DHT22 read attempt %d failed: %s", attempt + 1, e)
            time.sleep(0.5)
    log.warning("DHT22: all 3 read attempts failed")
    return None, None

# ── MQ gas sensor (digital DO only) ──────────────────────────────────────────
# Many MQ modules output 5 V on DO — ensure level-shifting before GPIO17!
_mq_pin = Button(config.PIN_MQ_DO, pull_up=not config.MQ_ACTIVE_HIGH)

def read_gas_alert():
    """Return True if gas/smoke detected (respects MQ_ACTIVE_HIGH polarity)."""
    raw = _mq_pin.is_pressed  # True = pin pulled to active level
    return raw  # Button(pull_up=False) is_pressed=True when HIGH

# ── Grid sense with software debounce ─────────────────────────────────────────
_grid_pin = Button(config.PIN_GRID_SENSE, pull_up=not config.GRID_ACTIVE_HIGH)

class GridSensor:
    """Reads grid-present state with configurable software filter (debounce)."""

    def __init__(self):
        self._stable_value = self._raw()
        self._last_change  = time.monotonic()

    def _raw(self):
        raw = _grid_pin.is_pressed
        # is_pressed=True means pin is at active level
        # With GRID_ACTIVE_HIGH=True  and pull_up=False: HIGH → is_pressed=True → grid present
        # With GRID_ACTIVE_HIGH=False and pull_up=True:  LOW  → is_pressed=True → grid present
        return raw  # both cases: is_pressed=True == grid present

    def read(self):
        """Return True if grid is confirmed present after debounce filter."""
        current_raw = self._raw()
        if current_raw != self._stable_value:
            elapsed_ms = (time.monotonic() - self._last_change) * 1000
            if elapsed_ms >= config.GRID_SENSE_FILTER_MS:
                self._stable_value = current_raw
                log.info("Grid sense changed → %s (after %.0f ms stable)",
                         "PRESENT" if current_raw else "ABSENT", elapsed_ms)
        else:
            self._last_change = time.monotonic()
        return self._stable_value
