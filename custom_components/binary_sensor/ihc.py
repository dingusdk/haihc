"""
IHC binary sensor platform.
"""
import logging
import asyncio
import threading
import time
import xml.etree.ElementTree

from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import STATE_UNKNOWN

_LOGGER = logging.getLogger(__name__)

ihcsensors = {}


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):

    while not 'ihc' in hass.data:
        time.sleep( 0.1)
    ihccontroller = hass.data[ 'ihc']

    devices = []
    if config.get( 'autosetup'):
        _LOGGER.info("Auto setup for IHC Binary sensor")
        project = ihccontroller.GetProject()
        xdoc = xml.etree.ElementTree.fromstring( project)
        groups = xdoc.findall( r'.//group')
        for group in groups:
            groupname = group.attrib['name']
            doorsensors = group.findall( './/product_dataline[@product_identifier="_0x2109"]')
            for product in doorsensors:
                id = int( product.find( "dataline_input").attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddSensorFromNode( devices,ihccontroller,id,name,product,"opening",True)
            pirsensors = group.findall( './/product_dataline[@product_identifier="_0x210e"]')
            for product in pirsensors:
                id = int( product.find( "dataline_input").attrib['id'].strip( '_'),0)
                name = groupname + "_" + str(id) 
                AddSensorFromNode( devices,ihccontroller,id,name,product,'motion',False)

    type = config.get( 'type')
    ids = config.get( 'ids')
    if ids != None:
        _LOGGER.info("Adding IHC Sensor")
        for id in ids:
            data = ids[ id]
            type = None
            name = data
            inverting = False
            if 'name' in data:
                name = data['name']
            if 'type' in data:
                type = data['type']
            if 'inverting' in data:
              inverting = data['inverting'] = "True"

            AddSensor( devices,ihccontroller,int(id),name,type,True,inverting)

    add_devices( devices)
    # Start notification after devices has been added
    for device in devices:
        device.ihc.AddNotifyEvent( device.ihcid,device.IhcChange)


class IHCBinarySensor(BinarySensorDevice):

    def __init__(self, ihccontroller, name,id,inverting:bool,ihcname:str,ihcnote:str):
        self._name = name
        self._state = STATE_UNKNOWN

        self.ihcid = id
        self.ihc = ihccontroller
        self.inverting = inverting
        self._sensor_type = None
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
        if not self.ihc.info: return {}
        return {
            '_ihcid': self.ihcid,
            'ihcname' : self.ihcname,
            'ihcnote' : self.ihcnote
        }

    def update(self):
        pass

    def IhcChange( self,id,v):
        try:
            if self.inverting:
                self._state = not v
            else:
                self._state = v
            self.schedule_update_ha_state()
        except:
            pass


def AddSensorFromNode( devices,ihccontroller,id : int,name:str,product,type,inverting:bool) -> IHCBinarySensor:
    ihcname = product.attrib['name']
    ihcnote = product.attrib['note']
    return AddSensor( devices,ihccontroller,id,name,type,False,inverting,ihcname,ihcnote)

def AddSensor( devices,ihccontroller,id : int,name: str,type:str=None,overwrite :bool= False,inverting:bool=False,ihcname:str = "", ihcnote:str="") -> IHCBinarySensor:
    if id in ihcsensors:
        sensor = ihcsensors[ id]
        if overwrite: 
            sensor._name = name
            _LOGGER.info("IHC sensor set name: " + name + " " + str(id))
    else:
        sensor = IHCBinarySensor( ihccontroller,name,id,inverting,ihcname,ihcnote)
        sensor._sensor_type= type
        ihcsensors[ id] = sensor
        devices.append( sensor)
        _LOGGER.info("IHC sensor added: " + name + " " + str(id))
    return sensor

