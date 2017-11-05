"""
IHC binary sensor platform.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, bare-except
import logging
import time
import xml.etree.ElementTree
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA, DEVICE_CLASSES_SCHEMA)
from homeassistant.const import STATE_UNKNOWN, CONF_NAME, CONF_TYPE

DEPENDENCIES = ['ihc']

IHCDATA = 'ihc'

CONF_AUTOSETUP = 'autosetup'
CONF_IDS = 'ids'
CONF_INVERTING = 'inverting'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_AUTOSETUP, default='False') : cv.boolean,
    vol.Optional(CONF_IDS) : {
        cv.string: vol.All({
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_TYPE): DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_INVERTING): cv.boolean,
        })
    }
})

PRODUCTAUTOSETUP = [
    # Magnet contact
    {'xpath': './/product_dataline[@product_identifier="_0x2109"]',
     'node': 'dataline_input',
     'type': 'opening',
     'inverting': True},
    # Pir sensors
    {'xpath': './/product_dataline[@product_identifier="_0x210e"]',
     'node': 'dataline_input',
     'type': 'motion',
     'inverting': False},
    # Pir sensors twilight sensor
    {'xpath': './/product_dataline[@product_identifier="_0x0"]',
     'node': 'dataline_input',
     'type': 'motion',
     'inverting': False},
]

_LOGGER = logging.getLogger(__name__)
_IHCBINARYSENSORS = {}

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the IHC binary setsor platform."""
    while not IHCDATA in hass.data:
        time.sleep(0.1)
    ihccontroller = hass.data[IHCDATA]

    devices = []
    if config.get(CONF_AUTOSETUP):
        auto_setup(ihccontroller, devices)

    ids = config.get(CONF_IDS)
    if ids != None:
        _LOGGER.info("Adding IHC Binary Sensors")
        for ihcid in ids:
            data = ids[ihcid]
            name = data[CONF_NAME]
            sensortype = sensortype = data[CONF_TYPE] if CONF_TYPE in data else None
            inverting = data[CONF_INVERTING] if CONF_INVERTING in data else False
            add_sensor(devices, ihccontroller, int(ihcid), name, sensortype, True, inverting)

    add_devices(devices)
    # Start notification after devices has been added
    for device in devices:
        device.ihc.AddNotifyEvent(device.get_ihcid(), device.on_ihc_change)

def auto_setup(ihccontroller, devices):
    """auto setup ihc binary sensors from ihc project."""
    _LOGGER.info("Auto setup - IHC Binary sensors")
    project = ihccontroller.GetProject()
    xdoc = xml.etree.ElementTree.fromstring(project)
    groups = xdoc.findall(r'.//group')
    for group in groups:
        groupname = group.attrib['name']
        for productcfg in PRODUCTAUTOSETUP:
            products = group.findall(productcfg['xpath'])
            for product in products:
                node = product.find(productcfg['node'])
                ihcid = int(node.attrib['id'].strip('_'), 0)
                name = groupname + "_" + str(ihcid)
                add_sensor_from_node(devices, ihccontroller, ihcid, name,
                                     product, productcfg['type'],
                                     productcfg['inverting'])

class IHCBinarySensor(BinarySensorDevice):
    """IHC Binary Sensor."""
    def __init__(self, ihccontroller, name, ihcid, sensortype: str, inverting: bool,
                 ihcname: str, ihcnote: str):
        self._name = name
        self._state = STATE_UNKNOWN
        self._sensor_type = sensortype

        self._ihcid = ihcid
        self.ihc = ihccontroller
        self.inverting = inverting
        self.ihcname = ihcname
        self.ihcnote = ihcnote

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the BinarySensorDevice."""
        return self._name

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._sensor_type

    @property
    def is_on(self):
        """Return true if the binary sensor is on/open."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.ihc.info:
            return {}
        return {
            'ihcid': self._ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote
        }

    def update(self):
        pass

    def get_ihcid(self) -> int:
        """Return the ihc resource id."""
        return self._ihcid

    def set_name(self, name: str):
        """Set te aReturn the ihc resource id."""
        self._name = name

    def on_ihc_change(self, ihcid, value):
        """Callback when ihc resource changes."""
        try:
            if self.inverting:
                self._state = not value
            else:
                self._state = value
            self.schedule_update_ha_state()
        except:
            pass


def add_sensor_from_node(devices, ihccontroller, ihcid: int, name: str,
                         product, sensortype, inverting: bool) -> IHCBinarySensor:
    """Add a sensor from the ihc project node."""
    ihcname = product.attrib['name']
    ihcnote = product.attrib['note']
    return add_sensor(devices, ihccontroller, ihcid, name, sensortype, False,
                      inverting, ihcname, ihcnote)

def add_sensor(devices, ihccontroller, ihcid: int, name: str,
               sensortype: str = None, overwrite: bool = False,
               inverting: bool = False, ihcname: str = "",
               ihcnote: str = "") -> IHCBinarySensor:
    """Add a new a sensor."""
    if ihcid in _IHCBINARYSENSORS:
        sensor = _IHCBINARYSENSORS[ihcid]
        if overwrite:
            sensor.set_name(name)
            _LOGGER.info("IHC sensor set name: " + name + " " + str(ihcid))
    else:
        sensor = IHCBinarySensor(ihccontroller, name, ihcid, sensortype,
                                 inverting, ihcname, ihcnote)
        _IHCBINARYSENSORS[ihcid] = sensor
        devices.append(sensor)
        _LOGGER.info("IHC sensor added: " + name + " " + str(ihcid))
    return sensor
