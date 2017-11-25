"""
IHC sensor platform.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, bare-except, unused-argument, missing-docstring
import logging
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_NAME, CONF_TYPE, CONF_UNIT_OF_MEASUREMENT

from ..ihc.const import *
from ..ihc import get_ihc_platform
from ..ihc.ihcdevice import IHCDevice

DEPENDENCIES = ['ihc']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_AUTOSETUP, default='False') : cv.boolean,
    vol.Optional(CONF_IDS) : {
        cv.string: vol.All({
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_TYPE): cv.string,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string
        })
    }
})

PRODUCTAUTOSETUP = [
    # Temperature sensor
    {'xpath': './/product_dataline[@product_identifier="_0x2124"]',
     'node': 'resource_temperature',
     'sensortype': "Temperature",
     'unit_of_measurement': '°C'},
    # Humidity/temperature
    {'xpath': './/product_dataline[@product_identifier="_0x2135"]',
     'node': 'resource_humidity_level',
     'sensortype': "Humidity",
     'unit_of_measurement': '%'},
    # Humidity/temperature
    {'xpath': './/product_dataline[@product_identifier="_0x2135"]',
     'node': 'resource_temperature',
     'sensortype': "Temperature",
     'unit_of_measurement': '°C'},
    # Lux/temperature
    {'xpath': './/product_dataline[@product_identifier="_0x2136"]',
     'node': 'resource_light',
     'sensortype': "Light",
     'unit_of_measurement': 'Lux'},
    # Lux/temperature
    {'xpath': './/product_dataline[@product_identifier="_0x2136"]',
     'node': 'resource_temperature',
     'sensortype': "Temperature",
     'unit_of_measurement': '°C'},
]

_LOGGER = logging.getLogger(__name__)

_IHCSENSORS = {}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the ihc sensor platform"""
    ihcplatform = get_ihc_platform(hass)
    devices = []
    if config.get('autosetup'):
        auto_setup(ihcplatform, devices)

    ids = config.get('ids')
    if ids != None:
        _LOGGER.info("Adding IHC Sensor")
        for ihcid in ids:
            data = ids[ihcid]
            sensortype = "Temperature"
            unit = "°C"
            name = data
            if CONF_NAME in data:
                name = data[CONF_NAME]
            if CONF_TYPE in data:
                sensortype = data[CONF_TYPE]
            if CONF_UNIT_OF_MEASUREMENT in data:
                unit = data[CONF_UNIT_OF_MEASUREMENT]
            add_sensor(devices, ihcplatform.ihc, int(ihcid), name, sensortype, unit, True)

    add_devices(devices)
    # Start notification after devices has been added
    for sensor in devices:
        sensor.ihc.add_notify_event(sensor.get_ihcid(), sensor.on_ihc_change, True)

def auto_setup(ihcplatform, devices):
    """Setup ihc sensors from the ihc project file."""
    _LOGGER.info("Auto setup for IHC sensor")
    def setup_product(ihcid, name, product, productcfg):
        add_sensor(devices, ihcplatform.ihc, ihcid, name,
                   productcfg['sensortype'], productcfg['unit_of_measurement'],
                   False, product.attrib['name'], product.attrib['note'],
                   product.attrib['position'])
    ihcplatform.autosetup(PRODUCTAUTOSETUP, setup_product)


class IHCSensor(IHCDevice, Entity):
    """Implementation of the IHC sensor."""
    def __init__(self, ihccontroller, name, ihcid, sensortype, unit, ihcname, ihcnote, ihcposition):
        IHCDevice.__init__(self, ihccontroller, name, ihcid, ihcname, ihcnote, ihcposition)
        self._state = None
        self._icon = None
        self._assumed = False
        self.type = sensortype
        self._unit_of_measurement = unit

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        pass

    def set_unit(self, unit):
        """Set unit of measusement"""
        self._unit_of_measurement = unit

    def on_ihc_change(self, ihcid, value):
        """Callback when ihc resource changes."""
        try:
            self._state = value
            self.schedule_update_ha_state()
        except:
            pass

def add_sensor(devices, ihccontroller, ihcid: int, name: str, sensortype: str,
               unit: str, overwrite: bool = False,
               ihcname: str = "", ihcnote: str = "", ihcposition: str = "") -> IHCSensor:
    """Add a new ihc sensor"""
    if ihcid in _IHCSENSORS:
        sensor = _IHCSENSORS[ihcid]
        if overwrite:
            sensor.set_name(name)
            sensor.type = sensortype
            sensor.set_unit(unit)
            _LOGGER.info("IHC sensor set name: " + name + " " + str(ihcid))
    else:
        sensor = IHCSensor(ihccontroller, name, ihcid, sensortype, unit,
                           ihcname, ihcnote, ihcposition)
        sensor.type = sensortype
        _IHCSENSORS[ihcid] = sensor
        devices.append(sensor)
        _LOGGER.info("IHC sensor added: " + name + " " + str(ihcid))
    return sensor
