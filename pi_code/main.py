"""
main.py - Server Room Monitor — main loop
Reads sensors, drives actuators, manages power state, posts telemetry.
Handles SIGINT/SIGTERM for graceful shutdown.
"""
import signal
import sys
import time
import logging
import logging.handlers
import os

# ── Logging setup (before importing config) ───────────────────────────────────
os.makedirs(os.path.dirname("/var/log/serverroom/monitor.log"), exist_ok=True)

import config

_log_handler = logging.handlers.RotatingFileHandler(
    config.LOG_FILE,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT,
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("main")

import sensors
import actuators
import power_manager
import supabase_client

# ── State ─────────────────────────────────────────────────────────────────────
_running        = True
_grid_sensor    = sensors.GridSensor()
_power          = power_manager.PowerManager()
_last_post_time = 0
_alarm_cooldown = 0   # monotonic timestamp after which buzzer can re-trigger

def _shutdown(signum, frame):
    global _running
    log.info("Signal %d received — shutting down …", signum)
    _running = False

signal.signal(signal.SIGINT,  _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

# ── Main loop ─────────────────────────────────────────────────────────────────
log.info("Server Room Monitor starting (device=%s)", config.DEVICE_ID)

try:
    while _running:
        loop_start = time.monotonic()

        # 1. Read sensors
        temp, humidity  = sensors.read_dht22()
        gas_alert       = sensors.read_gas_alert()
        grid_present    = _grid_sensor.read()

        # 2. Update power state machine
        power_source    = _power.update(grid_present)

        # 3. Evaluate alarm condition
        temp_alarm  = (temp    is not None) and (temp    > config.TEMP_HIGH_C)
        humid_alarm = (humidity is not None) and (humidity > config.HUMID_HIGH_PCT)
        alarm_active = temp_alarm or humid_alarm or gas_alert

        now = time.monotonic()
        if alarm_active and now >= _alarm_cooldown:
            actuators.start_alarm()
            _alarm_cooldown = now + (config.BUZZ_PATTERN_ON_MS + config.BUZZ_PATTERN_OFF_MS) / 1000
        elif not alarm_active:
            actuators.stop_alarm()
            if not _power.on_grid:
                actuators.red_led.on()  # keep red on for backup even without alarm

        # 4. Update LCD
        actuators.update_lcd(temp, humidity, gas_alert, grid_present, alarm_active)

        # 5. Log locally
        log.info(
            "T=%.1f°C H=%.1f%% Gas=%s Grid=%s PWR=%s ALM=%s",
            temp or -99, humidity or -99,
            "ALERT" if gas_alert else "OK",
            "YES" if grid_present else "NO",
            power_source,
            "ON" if alarm_active else "OFF",
        )

        # 6. Post telemetry at configured interval
        if now - _last_post_time >= config.POST_INTERVAL_SEC:
            supabase_client.post_telemetry(
                temperature_c=temp,
                humidity_pct=humidity,
                gas_alert=gas_alert,
                grid_present=grid_present,
                power_source=power_source,
                alarm_active=alarm_active,
            )
            _last_post_time = now

        # 7. Sleep for remainder of interval
        elapsed = time.monotonic() - loop_start
        sleep_for = max(0, config.SENSOR_READ_INTERVAL_SEC - elapsed)
        time.sleep(sleep_for)

except Exception as e:
    log.exception("Fatal error in main loop: %s", e)
    sys.exit(1)

finally:
    log.info("Cleaning up …")
    actuators.stop_alarm()
    actuators.lcd_clear()
    _power.safe_shutdown()
    log.info("Shutdown complete.")
