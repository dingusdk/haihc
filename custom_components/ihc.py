import logging
import threading
import time
from homeassistant.helpers.discovery import load_platform
from ihcsdk.ihcclient import IHCSoapClient
from ihcsdk.ihccontroller import IHCController

DOMAIN = 'ihc'
#REQUIREMENTS = ['ihcsdk==1.0.0']

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):

    url = config[DOMAIN].get('url')
    username = config[DOMAIN].get('username')
    password = config[DOMAIN].get('password')
    ihc = IHCController( url,username,password)
    ihc.info = config[DOMAIN].get('info')

    if  not ihc.Authenticate():
        return false

# Set the intial state
#    hass.states.set( "ihc.status", 'No data')

    hass.data[ DOMAIN] = ihc
    return True

