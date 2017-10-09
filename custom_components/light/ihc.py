"""
IHC light platform that implements lights.
"""
import logging
import asyncio
import threading
import time
import xml.etree.ElementTree
import homeassistant.loader as loader
from homeassistant.components.light import ( ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS,Light)

_LOGGER = logging.getLogger(__name__)

ihclights = {}
# a dictionary of all ihc lights ihcid->IhcLight object

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
            dimmers = group.findall( './/product_airlink[@product_identifier="_0x4406"]')
            for product in dimmers:
                dimmer = product.find( "airlink_dimming")
                id = int( dimmer.attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddLightFromNode( devices,ihccontroller,id,name,product)
            dimmers = group.findall( './/product_airlink[@product_identifier="_0x4306"]')
            for product in dimmers:
                dimmer = product.find( "airlink_dimming")
                id = int( dimmer.attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddLightFromNode( devices,ihccontroller,id,name,product)

            relays = group.findall( './/product_airlink[@product_identifier="_0x4404"]')
            for product in relays:
                relay = product.find( "airlink_relay")
                id = int( relay.attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddLightFromNode( devices,ihccontroller,id,name,product)

            # dataline lampeudtag 
            lights = group.findall( './/product_dataline[@product_identifier="_0x2201"]')
            for product in lights:
                relay = product.find( "dataline_output")
                id = int( relay.attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddLightFromNode( devices,ihccontroller,id,name,product)

    ids = config.get( 'ids')
    if ids != None:
        _LOGGER.info("Adding/Changing IHC light names")
        for id in ids:
            name = ids[id]
            AddLight( devices,ihccontroller,id,name,True)

    add_devices_callback( devices)
    # Start notification after device har been added
    for device in devices:
        device.ihc.AddNotifyEvent( device.ihcid,device.IhcChange)


class IhcLight(Light):
    """Representation of a IHC light."""

    def __init__(self,controller,name, id,ihcname,ihcnote):
        """Initialize the light."""
        self._name = name
        self._brightness = 0
        value = controller.GetRuntimeValue( id)
        self._dimmable = type(value) is int
        if self._dimmable: 
            self._brightness = int(value *255 / 100)
            self._state = self._brightness > 0
        else:
            self._state = value

        self.ihcid = id
        self.ihc = controller
        self.ihcname = ihcname
        self.ihcnote = ihcnote

    @property
    def should_poll(self) -> bool:
        """No polling needed for a ihc light."""
        return False

    @property
    def name(self) -> str:
        """Return the name of the light if any."""
        return self._name

    @property
    def available(self) -> bool:
        """Return availability."""
        return True

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self._dimmable: return ( SUPPORT_BRIGHTNESS)
        return ()

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.ihc.info: return {}
        return {
            '_ihcid': self.ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote
        }

    def turn_on(self, **kwargs) -> None:

        """Turn the light on."""
        self._state = True
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        if self._dimmable:
            if self._brightness == 0: self._brightness = 255
            self.ihc.SetRuntimeValueInt( self.ihcid,int(self._brightness * 100 / 255))
        else:
            self.ihc.SetRuntimeValueBool( self.ihcid,True)


        # As we have disabled polling, we need to inform
        # Home Assistant about updates in our state ourselves.
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        self._state = False

        if self._dimmable:
            self.ihc.SetRuntimeValueInt( self.ihcid,0)
        else:
            self.ihc.SetRuntimeValueBool( self.ihcid,False)

        # As we have disabled polling, we need to inform
        # Home Assistant about updates in our state ourselves.
        self.schedule_update_ha_state()

    @asyncio.coroutine
    def async_restore_state(self, is_on, **kwargs):
        t = 1
        """
        self._state = is_on
        if 'brightness' in kwargs:
            self._brightness = kwargs['brightness']
        if self._dimmable:
            if not self._state:
                self.ihc.SetRuntimeValueInt( self.ihcid,0)
            else:
                if self._brightness == 0: self._brightness = 255;
                self.ihc.SetRuntimeValueInt( self.ihcid,int(self._brightness * 100 / 255))
        else:
            self.ihc.SetRuntimeValueBool( self.ihcid,self._state )
		"""

    def IhcChange( self,id,v):
        """Callback from Ihc notifications"""
        try:
            if v is int: 
                self._brightness = v * 255 / 100
                self._state = self._brightness > 0
            else:
                self._state = v
            self.schedule_update_ha_state()
        except:
            pass

def AddLightFromNode( devices,ihccontroller,id : int,name:str,product) -> IhcLight:
    ihcname = product.attrib['name']
    ihcnote = product.attrib['note']
    return AddLight( devices,ihccontroller,id,name,False,ihcname,ihcnote)

def AddLight( devices,ihccontroller,id : int,name: str,overwrite :bool= False,ihcname:str = "", ihcnote:str="") -> IhcLight:
    if id in ihclights:
        light = ihclights[ id]
        if overwrite: 
            light._name = name
            _LOGGER.info("IHC light set name: " + name + " " + str(id))
    else:
        light = IhcLight( ihccontroller,name,id,ihcname,ihcnote)
        ihclights[ id] = light
        devices.append( light)
        _LOGGER.info("IHC light added: " + name + " " + str(id))
    return light

