"""
IHC platform.
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD

REQUIREMENTS = ['ihcsdk==1.0.4']

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

    if  not ihc.Authenticate():
        _LOGGER.error("Unable to authenticate on ihc controller. Username/password may be wrong")
        return False

# Set the intial state
#    hass.states.set( "ihc.status", 'No data')

    hass.data[DOMAIN] = ihc
    return True
