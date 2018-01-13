"""IHC sensor platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.ihc/
"""
from xml.etree.ElementTree import Element

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_ID, CONF_NAME, CONF_UNIT_OF_MEASUREMENT, CONF_SENSORS,
    TEMP_CELSIUS)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from ..ihc import (
    validate_name, IHC_DATA, IHC_CONTROLLER)
from ..ihc.ihcdevice import IHCDevice

DEPENDENCIES = ['ihc']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SENSORS, default=[]):
        vol.All(cv.ensure_list, [
            vol.All({
                vol.Required(CONF_ID): cv.positive_int,
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT,
                             default=TEMP_CELSIUS): cv.string
            }, validate_name)
        ])
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the ihc sensor platform."""
    ihc_controller = hass.data[IHC_DATA][IHC_CONTROLLER]
    devices = []
    if discovery_info:
        for name, device in discovery_info.items():
            ihc_id = device['ihc_id']
            product_cfg = device['product_cfg']
            product = device['product']
            sensor = IHCSensor(ihc_controller, name, ihc_id,
                               product_cfg[CONF_UNIT_OF_MEASUREMENT],
                               product)
            devices.append(sensor)
    else:
        sensors = config[CONF_SENSORS]
        for sensor_cfg in sensors:
            ihc_id = sensor_cfg[CONF_ID]
            name = sensor_cfg[CONF_NAME]
            unit = sensor_cfg[CONF_UNIT_OF_MEASUREMENT]
            sensor = IHCSensor(ihc_controller, name, ihc_id, unit)
            devices.append(sensor)

    add_devices(devices)


class IHCSensor(IHCDevice, Entity):
    """Implementation of the IHC sensor."""

    def __init__(self, ihc_controller, name, ihc_id, unit,
                 product: Element=None):
        """Initialize the IHC sensor."""
        super().__init__(ihc_controller, name, ihc_id, product)
        self._state = None
        self._unit_of_measurement = unit

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def on_ihc_change(self, ihc_id, value):
        """Callback when ihc resource changes."""
        self._state = value
        self.schedule_update_ha_state()
