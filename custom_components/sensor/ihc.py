"""
IHC sensor.
"""
import logging
import time
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    TEMP_FAHRENHEIT, CONF_NAME, CONF_MONITORED_CONDITIONS)
from homeassistant.helpers.entity import Entity
import xml.etree.ElementTree

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

ihcsensors = {}

def setup_platform(hass, config, add_devices, discovery_info=None):

    while not 'ihc' in hass.data:
        time.sleep( 0.1)
    ihccontroller = hass.data[ 'ihc']

    devices = []
    if config.get( 'autosetup'):
        _LOGGER.info("Auto setup for IHC sensor")
        project = ihccontroller.GetProject()
        xdoc = xml.etree.ElementTree.fromstring( project)
        groups = xdoc.findall( r'.//group')
        for group in groups:
            groupname = group.attrib['name']
            products = group.findall( './/product_dataline[@product_identifier="_0x2124"]')
            for product in products:
              DoProduct( product,groupname,devices,ihccontroller)
            products = group.findall( './/product_dataline[@product_identifier="_0x2135"]')
            for product in products:
              DoProduct( product,groupname,devices,ihccontroller)
            products = group.findall( './/product_dataline[@product_identifier="_0x2136"]')
            for product in products:
              DoProduct( product,groupname,devices,ihccontroller)

    ids = config.get( 'ids')
    if ids != None:
        _LOGGER.info("Adding IHC Sensor")
        for id in ids:
            data = ids[ id]
            type = "Temperature"
            unit = "°C"
            name = data
            if 'name' in data:
                name = data['name']
            if 'type' in data:
                type = data['type']
            if 'unit' in data:
                unit = data['unit']
            AddSensor( devices,ihccontroller,int(id),name,type,unit,True)

    add_devices( devices)
    # Start notification after devices has been added
    for sensor in devices:
        sensor.ihc.AddNotifyEvent( sensor.ihcid,sensor.IhcChange)


class IHCSensor(Entity):
    """Implementation of the IHC sensor."""
    def __init__(self, ihccontroller,name, id,type,unit,ihcname,ihcnote):
        self._name = name
        self._state =  None
        self._icon = None
        self._assumed = False

        self.ihcid = id
        self.ihc = ihccontroller
        self.ihcname = ihcname
        self.ihcnote = ihcnote

        self.type = type
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
        if not self.ihc.info: return {}
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

    def IhcChange( self,id,v):
        try:
            self._state = v
            self.schedule_update_ha_state()
        except:
            pass

def DoProduct( product,groupname,devices,ihccontroller):
    for temperatureresource in product.findall( "resource_temperature"):
      if 'setting' in temperatureresource.attrib and temperatureresource.attrib['setting'] == 'yes':
        continue
      id = int( temperatureresource.attrib['id'].strip( '_'),0)
      ihcname = temperatureresource.attrib['name']
      ihcnote = temperatureresource.attrib['note']
      name = groupname + "_" + str(id) 
      AddSensor( devices,ihccontroller,id,name,"Temperature","°C",False,ihcname,ihcnote)
    for humidityresource in product.findall( "resource_humidity_level"):
      if "setting" in humidityresource.attrib:
        continue
      id = int( humidityresource.attrib['id'].strip( '_'),0)
      ihcname = humidityresource.attrib['name']
      ihcnote = humidityresource.attrib['note']
      name = groupname + "_" + str(id) 
      AddSensor( devices,ihccontroller,id,name,"Humidity","%",False,ihcname,ihcnote)
    for lightresource in product.findall( "resource_light"):
      if "setting" in lightresource.attrib:
        continue
      id = int( lightresource.attrib['id'].strip( '_'),0)
      ihcname = lightresource.attrib['name']
      ihcnote = lightresource.attrib['note']
      name = groupname + "_" + str(id) 
      AddSensor( devices,ihccontroller,id,name,"Light","Lux",False,ihcname,ihcnote)

def AddSensor( devices,ihccontroller,id : int,name: str,type:str,unit:str,overwrite :bool= False,ihcname:str = "", ihcnote:str="") -> IHCSensor:
    if id in ihcsensors:
        sensor = ihcsensors[ id]
        if overwrite: 
            sensor._name = name
            sensor.type = type
            sensor._unit_of_measurement = unit
            _LOGGER.info("IHC sensor set name: " + name + " " + str(id))
    else:
        sensor = IHCSensor( ihccontroller,name,id,type,unit,ihcname,ihcnote)
        sensor.type = type
        ihcsensors[ id] = sensor
        devices.append( sensor)
        _LOGGER.info("IHC sensor added: " + name + " " + str(id))
    return sensor
