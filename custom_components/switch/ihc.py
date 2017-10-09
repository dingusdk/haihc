"""
IHC switch platform that implements a switch.
"""
import logging
import threading
import time
import xml.etree.ElementTree
from homeassistant.components.switch import SwitchDevice
from homeassistant.const import DEVICE_DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

ihcswitches = {}

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    
    while not 'ihc' in hass.data:
        time.sleep( 0.1)
    ihccontroller = hass.data[ 'ihc']

    devices = []
    if config.get( 'autosetup'):
        _LOGGER.info("Auto setup for IHC light")
        project = ihccontroller.GetProject()
        xdoc = xml.etree.ElementTree.fromstring( project)
        groups = xdoc.findall( r'.//group')
        for group in groups:
            groupname = group.attrib['name']
            switches = group.findall( './/product_airlink[@product_identifier="_0x4201"]')
            for product in switches :
                id = int( product.find( "airlink_relay").attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddSwitchFromNode( devices,ihccontroller,id,name,product)
            # universal relæ
            switches = group.findall( './/product_airlink[@product_identifier="_0x4203"]')
            for product in switches :
                id = int( product.find( "airlink_relay").attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddSwitchFromNode( devices,ihccontroller,id,name,product)
            # dataline stikkontakt
            switches = group.findall( './/product_dataline[@product_identifier="_0x2201"]')
            for product in switches :
                id = int( product.find( "dataline_output").attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddSwitchFromNode( devices,ihccontroller,id,name,product)

    ids = config.get( 'ids')
    if ids != None:
        _LOGGER.info("Adding IHC Switches")
        for id in ids:
            name = ids[id]
            AddSwitch( devices,ihccontroller,id,name,True)

    add_devices_callback( devices)
    # Start notification after device har been added
    for device in devices:
        device.ihc.AddNotifyEvent( device.ihcid,device.IhcChange)


class IHCSwitch(SwitchDevice):

    def __init__(self, ihccontroller,name, id,ihcname,ihcnote):
        self._name = name or DEVICE_DEFAULT_NAME
        self._state =  False
        self._icon = None
        self._assumed = False

        self.ihcid = id
        self.ihc = ihccontroller
        self.ihcname = ihcname
        self.ihcnote = ihcnote

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

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

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.ihc.info: return {}
        return {
            '_ihcid': self.ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote
        }

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        self.ihc.SetRuntimeValueBool( self.ihcid,True)
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._state = False
        self.ihc.SetRuntimeValueBool( self.ihcid,False)
        self.schedule_update_ha_state()

    def IhcChange( self,id,v):
        try:
            self._state = v
            self.schedule_update_ha_state()
        except:
            pass


def AddSwitchFromNode( devices,ihccontroller,id : int,name:str,product) -> IHCSwitch:
    ihcname = product.attrib['name']
    ihcnote = product.attrib['note']
    return AddSwitch( devices,ihccontroller,id,name,False,ihcname,ihcnote)

def AddSwitch( devices,ihccontroller,id : int,name: str,overwrite :bool= False,ihcname:str = "", ihcnote:str="") -> IHCSwitch:
    if id in ihcswitches:
        switch = ihcswitches[ id]
        if overwrite: 
            switch._name = name
            _LOGGER.info("IHC switch set name: " + name + " " + str(id))
    else:
        switch = IHCSwitch( ihccontroller,name,id,ihcname,ihcnote)
        ihcswitches[ id] = switch
        devices.append( switch)
        _LOGGER.info("IHC switch added: " + name + " " + str(id))
    return switch

