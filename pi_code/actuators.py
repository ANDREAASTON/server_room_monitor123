"""
actuators.py - LEDs, buzzer, and I2C LCD 16x2 control
"""
import time
import threading
import logging
from gpiozero import LED, Buzzer as _Buzzer
import config

log = logging.getLogger(__name__)

# ── LEDs ──────────────────────────────────────────────────────────────────────
green_led = LED(config.PIN_LED_GREEN)
red_led   = LED(config.PIN_LED_RED)

def set_grid_mode():
    green_led.on()
    red_led.off()

def set_backup_mode():
    green_led.off()
    red_led.on()

# ── Buzzer (beep pattern in background thread) ────────────────────────────────
_buzzer     = _Buzzer(config.PIN_BUZZER)
_buzz_lock  = threading.Lock()
_buzz_active = False
_buzz_thread = None

def _beep_loop():
    global _buzz_active
    while _buzz_active:
        _buzzer.on()
        time.sleep(config.BUZZ_PATTERN_ON_MS / 1000)
        _buzzer.off()
        time.sleep(config.BUZZ_PATTERN_OFF_MS / 1000)

def start_alarm():
    global _buzz_active, _buzz_thread
    with _buzz_lock:
        if not _buzz_active:
            _buzz_active = True
            _buzz_thread = threading.Thread(target=_beep_loop, daemon=True)
            _buzz_thread.start()
            red_led.on()
            log.info("Alarm started")

def stop_alarm():
    global _buzz_active
    with _buzz_lock:
        if _buzz_active:
            _buzz_active = False
            _buzzer.off()
            log.info("Alarm stopped")

# ── I2C LCD 16x2 via PCF8574 backpack ────────────────────────────────────────
try:
    from RPLCD.i2c import CharLCD
    _lcd = CharLCD(
        i2c_expander='PCF8574',
        address=config.LCD_I2C_ADDRESS,
        port=1,
        cols=16,
        rows=2,
        charmap='A02',
        auto_linebreaks=False,
    )
    _lcd_available = True
    log.info("LCD initialised at 0x%02X", config.LCD_I2C_ADDRESS)
except Exception as e:
    _lcd_available = False
    log.warning("LCD not available: %s", e)

def update_lcd(temp, humidity, gas_alert, grid_present, alarm_active):
    """Write two 16-char lines to LCD."""
    if not _lcd_available:
        return
    try:
        t_str = f"{temp:.1f}" if temp is not None else "--.-"
        h_str = f"{humidity:.0f}" if humidity is not None else "--"
        line1 = f"T:{t_str}C H:{h_str}%"[:16].ljust(16)

        pwr = "GRID" if grid_present else "BKUP"
        gas = "ALRT" if gas_alert   else "OK  "
        alm = "A:ON" if alarm_active else "A:OF"
        line2 = f"P:{pwr} G:{gas} {alm}"[:16].ljust(16)

        _lcd.cursor_pos = (0, 0)
        _lcd.write_string(line1)
        _lcd.cursor_pos = (1, 0)
        _lcd.write_string(line2)
    except Exception as e:
        log.warning("LCD write error: %s", e)

def lcd_clear():
    if _lcd_available:
        try:
            _lcd.clear()
        except Exception:
            pass
