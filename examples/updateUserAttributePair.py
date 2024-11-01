# Addresses the issue explained at https://github.com/CLOSER-Cohorts/colectica-api/issues/46.
# It updates/adds variable group references to Physical Instances.

# Create connection...

from colectica_api import ColecticaObject
hostname="INSERT HOSTNAME HERE"
username="INSERT USERNAME HERE"
password="INSERT PASSWORD HERE"
C = ColecticaObject(hostname, username, password,verify_ssl=False)

# Import libraries for processing XML/JSON...

import defusedxml
from defusedxml.ElementTree import parse
from xml.etree import ElementTree as ET
import json
import re

# Declare a utility function for getting the namespace of an element from an XML tag

def getNamespace(tag):
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)

# Declare a utility function for finding the AttributeValue within a UserAttributePair element in an 
# XML object representing a Physical instance

def getAttributeValue(physicalInstanceFragmentXML):
    userAttributePair = physicalInstanceFragmentXML[0].find(f'{{{getNamespace(physicalInstanceFragmentXML[0][0].tag)}}}UserAttributePair')
    attributeValue = userAttributePair.find(f'{{{getNamespace(physicalInstanceFragmentXML[0][0].tag)}}}AttributeValue')
    return attributeValue

# Get https://discovery.closer.ac.uk/item/uk.wchads/158e3ae8-5437-4c5f-afb2-3fdfecb59999 as a 
# String and convert it to an XML object...  

fragmentString = C.get_item_xml('uk.wchads', '158e3ae8-5437-4c5f-afb2-3fdfecb59999')['Item']
fragmentXMLFirstPhysicalInstance = defusedxml.ElementTree.fromstring(fragmentString)

# Get userAttributePair element from within the fragmentXMLFirstPhysicalInstance element, and update 
# the URN in it...

attributeValue = getAttributeValue(fragmentXMLFirstPhysicalInstance)
attributeValueJson = json.loads(attributeValue.text)
attributeValueJson['RelatedItemIdValue']={
        "URN": "urn:ddi:uk.closer:0b239724-f531-4362-afd1-927ce41a2aa7:2",
        "ItemType": "VariableGroup"
    }

# This update of the text value for attributeValue will update the fragmentXMLFirstPhysicalInstance
# object from which attributeValue was obtained, as attributeValue is a reference to an element contained
# within fragmentXMLFirstPhysicalInstance

attributeValue.text = json.dumps(attributeValueJson)

# Get https://discovery.closer.ac.uk/item/uk.cls.ncds/3d55f967-5ea9-407b-811f-850fe1629944 as a 
# String and convert it to an XML object...  

fragmentString = C.get_item_xml('uk.cls.ncds', '3d55f967-5ea9-407b-811f-850fe1629944')['Item']
fragmentXMLSecondPhysicalInstance = defusedxml.ElementTree.fromstring(fragmentString)

# Get userAttributePair element from within the fragmentXMLSecondPhysicalInstance element, and add a 'RelatedItemIdValue' 
# object to it containing the URN for a Variable Group...

attributeValue = getAttributeValue(fragmentXMLSecondPhysicalInstance)
attributeValueJson = json.loads(attributeValue.text)
attributeValueJson['RelatedItemIdValue']={
        "URN": "urn:ddi:uk.closer:0b239724-f531-4362-afd1-927ce41a2aa7:2",
        "ItemType": "VariableGroup"
    }

# This update of the text value for attributeValue will update the fragmentXMLSecondPhysicalInstance
# object from which attributeValue was obtained, as attributeValue is a reference to an element contained
# within fragmentXMLSecondPhysicalInstance

attributeValue.text = json.dumps(attributeValueJson)

# Create a transation, add the modified PhysicalInstance elements from above to the transaction,
# and commit the transaction

transactionResponse = C.create_transaction()
transactionId = transactionResponse['TransactionId']
version=fragmentXMLFirstPhysicalInstance[0].find(f'{{{getNamespace(fragmentXMLFirstPhysicalInstance[0][0].tag)}}}Version').text
physicalInstanceItemTypeUuid='a51e85bb-6259-4488-8df2-f08cb43485f8'
C.add_items_to_transaction('uk.wchads', 
                           '158e3ae8-5437-4c5f-afb2-3fdfecb59999', 
                           version, 
                           defusedxml.ElementTree.tostring(fragmentXMLFirstPhysicalInstance, encoding='unicode'),
                           physicalInstanceItemTypeUuid, 
                           transactionId)
version=fragmentXMLSecondPhysicalInstance[0].find(f'{{{getNamespace(fragmentXMLSecondPhysicalInstance[0][0].tag)}}}Version').text
C.add_items_to_transaction('uk.cls.ncds',
                           '3d55f967-5ea9-407b-811f-850fe1629944', 
                           version,
                           defusedxml.ElementTree.tostring(fragmentXMLSecondPhysicalInstance, encoding='unicode'),
                           physicalInstanceItemTypeUuid, 
                           transactionId)                           
C.commit_transaction(transactionId, "Update userAttributePair", 3)
