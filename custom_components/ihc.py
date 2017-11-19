"""
IHC platform.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, bare-except
import time
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD

REQUIREMENTS = ['ihcsdk==2.0.1']

DOMAIN = 'ihc'

CONF_INFO = 'info'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_URL): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_INFO): cv.boolean
    }),
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Setyp the IHC platform."""
    from ihcsdk.ihccontroller import IHCController
    url = config[DOMAIN].get(CONF_URL)
    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    ihc = IHCController(url, username, password)
    ihc.info = config[DOMAIN].get(CONF_INFO)

    if  not ihc.authenticate():
        _LOGGER.error("Unable to authenticate on ihc controller. Username/password may be wrong")
        return False

#    hass.states.set( "ihc.status", 'Ok')

    hass.data[DOMAIN] = ihc

    def set_runtime_value_bool(call):
        """Set a IHC runtime bool value service function """
        ihcid = int(call.data.get('ihcid', 0))
        value = bool(call.data.get('value', 0))
        ihc.set_runtime_value_bool(ihcid, value)

    def set_runtime_value_int(call):
        """Set a IHC runtime integer value service function """
        ihcid = int(call.data.get('ihcid', 0))
        value = int(call.data.get('value', 0))
        ihc.set_runtime_value_int(ihcid, value)

    def set_runtime_value_float(call):
        """Set a IHC runtime float value service function """
        ihcid = int(call.data.get('ihcid', 0))
        value = float(call.data.get('value', 0))
        ihc.set_runtime_value_float(ihcid, value)

    hass.services.register(DOMAIN, 'set_runtime_value_bool', set_runtime_value_bool)
    hass.services.register(DOMAIN, 'set_runtime_value_int', set_runtime_value_int)
    hass.services.register(DOMAIN, 'set_runtime_value_float', set_runtime_value_float)

    return True

def get_ihc_instance(hass):
    """Get the ihc instance from the hass configuration"""
    while not DOMAIN in hass.data:
        time.sleep(0.1)
    return hass.data[DOMAIN]


class IHCDevice:
    """Base class for all ihc devices"""
    def __init__(self, ihccontroller, name, ihcid, ihcname: str, ihcnote: str, ihcposition: str):
        self.ihc = ihccontroller
        self._name = name
        self._ihcid = ihcid
        self.ihcname = ihcname
        self.ihcnote = ihcnote
        self.ihcposition = ihcposition

    @property
    def name(self):
        """Return the device name"""
        return self._name

    def get_ihcid(self) -> int:
        """Return the ihc resource id."""
        return self._ihcid

    def set_name(self, name):
        """Set the name"""
        self._name = name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.ihc.info:
            return {}
        return {
            'ihcid': self._ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote,
            'ihcposition' : self.ihcposition
        }
