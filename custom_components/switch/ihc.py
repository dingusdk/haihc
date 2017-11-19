"""
IHC switch platform that implements a switch.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, bare-except, unused-argument
import logging
import xml.etree.ElementTree
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from ..ihc import IHCDevice, get_ihc_instance

DEPENDENCIES = ['ihc']

CONF_AUTOSETUP = 'autosetup'
CONF_IDS = 'ids'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_AUTOSETUP, default='False'): cv.boolean,
    vol.Optional(CONF_IDS): vol.Schema(vol.Required({cv.string: cv.string}))
})

PRODUCTAUTOSETUP = [
    # Wireless Plug outlet
    {'xpath': './/product_airlink[@product_identifier="_0x4201"]',
     'node': 'airlink_relay'},
    # Dataline universal relay
    {'xpath': './/product_airlink[@product_identifier="_0x4203"]',
     'node': 'airlink_relay'},
    # Dataline plug outlet
    {'xpath': './/product_dataline[@product_identifier="_0x2201"]',
     'node': 'dataline_output'},
    ]


_LOGGER = logging.getLogger(__name__)

_IHCSWITCHES = {}

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the ihc switch platform."""
    ihccontroller = get_ihc_instance(hass)
    devices = []
    if config.get(CONF_AUTOSETUP):
        auto_setup(ihccontroller, devices)

    ids = config.get(CONF_IDS)
    if ids != None:
        _LOGGER.info("Adding IHC Switches")
        for ihcid in ids:
            name = ids[ihcid]
            add_switch(devices, ihccontroller, int(ihcid), name, True)

    add_devices_callback(devices)
    # Start notification after device har been added
    for device in devices:
        device.ihc.add_notify_event(device.get_ihcid(), device.on_ihc_change)

def auto_setup(ihccontroller, devices):
    """Auto setup switched from the ihc project file."""
    _LOGGER.info("Auto setup for IHC light")
    project = ihccontroller.get_project()
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
                add_switch_from_node(devices, ihccontroller, ihcid, name, product)


class IHCSwitch(IHCDevice, SwitchDevice):
    """IHC Switch."""
    def __init__(self, ihccontroller, name: str, ihcid: int,
                 ihcname: str, ihcnote: str, ihcposition: str):
        IHCDevice.__init__(self, ihccontroller, name, ihcid, ihcname, ihcnote, ihcposition)
        self._state = False
        self._icon = None
        self._assumed = False

    @property
    def should_poll(self):
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
        self.ihc.set_runtime_value_bool(self._ihcid, True)
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._state = False
        self.ihc.set_runtime_value_bool(self._ihcid, False)
        self.schedule_update_ha_state()

    def on_ihc_change(self, ihcid, value):
        """Callback when the ihc resource changes."""
        try:
            self._state = value
            self.schedule_update_ha_state()
        except:
            pass


def add_switch_from_node(devices, ihccontroller, ihcid: int, name: str, product) -> IHCSwitch:
    """Add a IHC switch form the a product in the project."""
    ihcname = product.attrib['name']
    ihcnote = product.attrib['note']
    ihcposition = product.attrib['position']
    return add_switch(devices, ihccontroller, ihcid, name, False, ihcname, ihcnote, ihcposition)

def add_switch(devices, ihccontroller, ihcid: int, name: str, overwrite: bool = False,
               ihcname: str = "", ihcnote: str = "", ihcposition: str = "") -> IHCSwitch:
    """Add a new ihc switch"""
    if ihcid in _IHCSWITCHES:
        switch = _IHCSWITCHES[ihcid]
        if overwrite:
            switch.set_name(name)
            _LOGGER.info("IHC switch set name: " + name + " " + str(ihcid))
    else:
        switch = IHCSwitch(ihccontroller, name, ihcid, ihcname, ihcnote, ihcposition)
        _IHCSWITCHES[ihcid] = switch
        devices.append(switch)
        _LOGGER.info("IHC switch added: " + name + " " + str(ihcid))
    return switch
