"""
IHC sensor platform.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, bare-except, unused-argument
import logging
import time
import xml.etree.ElementTree
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_NAME, CONF_TYPE, CONF_UNIT_OF_MEASUREMENT

DEPENDENCIES = ['ihc']

IHCDATA = 'ihc'

CONF_AUTOSETUP = 'autosetup'
CONF_IDS = 'ids'

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
    while not IHCDATA in hass.data:
        time.sleep(0.1)
    ihccontroller = hass.data[IHCDATA]

    devices = []
    if config.get('autosetup'):
        auto_setup(ihccontroller, devices)

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
            add_sensor(devices, ihccontroller, int(ihcid), name, sensortype, unit, True)

    add_devices(devices)
    # Start notification after devices has been added
    for sensor in devices:
        sensor.ihc.AddNotifyEvent(sensor.ihcid, sensor.on_ihc_change)

def auto_setup(ihccontroller, devices):
    """Setup ihc sensors from the ihc project file."""
    _LOGGER.info("Auto setup for IHC sensor")
    project = ihccontroller.GetProject()
    xdoc = xml.etree.ElementTree.fromstring(project)
    groups = xdoc.findall(r'.//group')
    for group in groups:
        groupname = group.attrib['name']
        for productcfg in PRODUCTAUTOSETUP:
            products = group.findall(productcfg['xpath'])
            for product in products:
                nodes = product.findall(productcfg['node'])
                for node in nodes:
                    if 'setting' in node.attrib and node.attrib['setting'] == 'yes':
                        continue
                    ihcid = int(node.attrib['id'].strip('_'), 0)
                    name = groupname + "_" + str(ihcid)
                    add_sensor(devices, ihccontroller, ihcid, name,
                               productcfg['sensortype'],
                               productcfg['unit_of_measurement'],
                               False, product.attrib['name'],
                               product.attrib['note'])

class IHCSensor(Entity):
    """Implementation of the IHC sensor."""
    def __init__(self, ihccontroller, name, ihcid, sensortype, unit, ihcname, ihcnote):
        self._name = name
        self._state = None
        self._icon = None
        self._assumed = False

        self.ihcid = ihcid
        self.ihc = ihccontroller
        self.ihcname = ihcname
        self.ihcnote = ihcnote

        self.type = sensortype
        self._unit_of_measurement = unit

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.ihc.info:
            return {}
        return {
            '_ihcid': self.ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        pass

    def set_name(self, name):
        """Set the name."""
        self._name = name

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
               ihcname: str = "", ihcnote: str = "") -> IHCSensor:
    """Add a new ihc sensor"""
    if ihcid in _IHCSENSORS:
        sensor = _IHCSENSORS[ihcid]
        if overwrite:
            sensor.set_name(name)
            sensor.type = sensortype
            sensor.set_unit(unit)
            _LOGGER.info("IHC sensor set name: " + name + " " + str(ihcid))
    else:
        sensor = IHCSensor(ihccontroller, name, ihcid, sensortype, unit, ihcname, ihcnote)
        sensor.type = sensortype
        _IHCSENSORS[ihcid] = sensor
        devices.append(sensor)
        _LOGGER.info("IHC sensor added: " + name + " " + str(ihcid))
    return sensor
