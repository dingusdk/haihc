"""IHC switch platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.ihc/
"""
from xml.etree.ElementTree import Element
import voluptuous as vol

from ..ihc.const import CONF_AUTOSETUP
from ..ihc import validate_name, IHC_DATA
from ..ihc.ihcdevice import IHCDevice
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import CONF_ID, CONF_NAME, CONF_SWITCHES
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['ihc']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_AUTOSETUP, default='False'): cv.boolean,
    vol.Optional(CONF_SWITCHES, default=[]):
        vol.All(cv.ensure_list, [
            vol.All({
                vol.Required(CONF_ID): cv.positive_int,
                vol.Optional(CONF_NAME): cv.string,
            }, validate_name)
        ])
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the ihc switch platform."""
    ihc = hass.data[IHC_DATA]
    devices = []
    if config.get(CONF_AUTOSETUP):
        def setup_product(ihc_id, name, product, product_cfg):
            """Product setup callback."""
            sensor = IHCSwitch(ihc, name, ihc_id, product)
            devices.append(sensor)
        ihc.auto_setup('switch', setup_product)

    switches = config.get(CONF_SWITCHES)
    for switch in switches:
        ihc_id = switch[CONF_ID]
        name = switch[CONF_NAME]
        sensor = IHCSwitch(ihc, name, ihc_id)
        devices.append(sensor)

    add_devices(devices)


class IHCSwitch(IHCDevice, SwitchDevice):
    """IHC Switch."""

    def __init__(self, ihc, name: str, ihc_id: int, product: Element = None):
        """Initialize the IHC switch."""
        super().__init__(ihc, name, ihc_id, product)
        self._state = False
        self._icon = None
        self._assumed = False

    @property
    def should_poll(self):
        """We do not need to poll."""
        return False

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def assumed_state(self):
        """Return if the state is based on assumptions."""
        return self._assumed

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return 0

    @property
    def today_energy_kwh(self):
        """Return the today total energy usage in kWh."""
        return 0

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        self.ihc.ihc_controller.set_runtime_value_bool(self._ihc_id, True)
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._state = False
        self.ihc.ihc_controller.set_runtime_value_bool(self._ihc_id, False)
        self.schedule_update_ha_state()

    def on_ihc_change(self, ihc_id, value):
        """Callback when the ihc resource changes."""
        self._state = value
        self.schedule_update_ha_state()
