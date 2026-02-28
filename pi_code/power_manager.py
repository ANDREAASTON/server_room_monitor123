"""
power_manager.py - Relay state machine: GRID → BACKUP → WAIT_GRID_STABLE → GRID
Avoids relay chatter by requiring grid to be stable for GRID_STABLE_DELAY_SEC
before switching back.
"""
import time
import logging
from enum import Enum, auto
from gpiozero import OutputDevice
import config
import actuators

log = logging.getLogger(__name__)

class PowerState(Enum):
    GRID             = auto()
    BACKUP           = auto()
    WAIT_GRID_STABLE = auto()

# active_high=True  → pin HIGH energises relay (active-high board)
# active_high=False → pin LOW  energises relay (active-low board)
_relay = OutputDevice(
    config.PIN_RELAY,
    active_high=config.RELAY_ACTIVE_HIGH,
    initial_value=False   # safe default: de-energised
)

class PowerManager:
    def __init__(self):
        self.state = PowerState.GRID
        self._wait_start = None
        # Assume grid on boot; correct immediately on first update
        self._apply_state()

    # ── Public ────────────────────────────────────────────────────────────────
    def update(self, grid_present: bool):
        """Call every sensor cycle. Returns current power source string."""
        if self.state == PowerState.GRID:
            if not grid_present:
                self._transition(PowerState.BACKUP)

        elif self.state == PowerState.BACKUP:
            if grid_present:
                self._transition(PowerState.WAIT_GRID_STABLE)

        elif self.state == PowerState.WAIT_GRID_STABLE:
            if not grid_present:
                # Grid disappeared again — stay on backup
                self._transition(PowerState.BACKUP)
            else:
                elapsed = time.monotonic() - self._wait_start
                if elapsed >= config.GRID_STABLE_DELAY_SEC:
                    self._transition(PowerState.GRID)

        return self.power_source

    @property
    def power_source(self):
        return "GRID" if self.state == PowerState.GRID else "BACKUP"

    @property
    def on_grid(self):
        return self.state == PowerState.GRID

    # ── Private ───────────────────────────────────────────────────────────────
    def _transition(self, new_state: PowerState):
        log.info("Power state: %s → %s", self.state.name, new_state.name)
        self.state = new_state
        if new_state == PowerState.WAIT_GRID_STABLE:
            self._wait_start = time.monotonic()
        self._apply_state()

    def _apply_state(self):
        if self.state == PowerState.GRID:
            _relay.off()          # de-energised = GRID path
            actuators.set_grid_mode()
            log.debug("Relay: de-energised (GRID)")
        else:
            _relay.on()           # energised = BACKUP path
            actuators.set_backup_mode()
            log.debug("Relay: energised (BACKUP)")

    def safe_shutdown(self):
        """Return relay to safe default before exiting."""
        _relay.off()
        log.info("Relay de-energised (safe shutdown)")
