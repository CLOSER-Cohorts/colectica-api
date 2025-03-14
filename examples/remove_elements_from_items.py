"""
This code demonstrates how to remove XML elements from DDI items, how to update the
repository with the modified items, and how to verify that item updates have been
successful. In this case we are:

1. Getting all the items from the Millenium Cohort Study (MCS)
2. Retrieving all the Data Collection and the Study items from the MCS items
3. Removing InstrumentReference and QuestionSchemeReference elements from the Data Collections
4. Removing PhysicalInstanceReference and RequiredResourcePackages elements from the Study items.
5. Updating the Data Collections and Studies in the repository with the changes that have been
   made to the local copies of these items.
6. Verifying that the removal of the references has been successful.
"""

from lib.utility import (
    update_repository,
    get_elements_of_type,
    remove_elements_from_item
)
import defusedxml
from xml.etree import ElementTree as ET
from defusedxml.ElementTree import parse
from colectica_api import ColecticaObject
from copy import deepcopy

USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)

# Specify the Millenium Cohort Study (MCS) which we want to search for items in...
search_sets = [{"agencyId": "uk.cls.mcs", 
                "identifier": "0d8a7220-c61b-4542-967d-a40cb5aca430", 
                "version": "57"}]
                
allItemsInOneQuery = C.search_items([], SearchSets=search_sets)['Results']

studies = [x for x in allItemsInOneQuery if x['ItemType']
           == C.item_code('Study')]

dataCollections = [x for x in allItemsInOneQuery if x['ItemType']
                   == C.item_code('Data Collection')]

dataCollectionItems = []
updatedDataCollections = []
for dataCollection in dataCollections:
    dataCollectionItem=defusedxml.ElementTree.fromstring(C.get_item_xml(dataCollection['AgencyId'],
        dataCollection['Identifier'], version=dataCollection['Version'])['Item'])
    # We use deepcopy to create a list of the unmodified items that we will use in a
    # 'before' and 'after' comparison'.
    dataCollectionItems.append(deepcopy(dataCollectionItem))
    dataCollectionWithoutInstrumentReferences = remove_elements_from_item(
        dataCollectionItem, "InstrumentReference", C)
    dataCollectionWithoutInstrumentAndQuestionSchemeReferences = remove_elements_from_item(
        dataCollectionWithoutInstrumentReferences, "QuestionSchemeReference", C)
    updatedDataCollections.append({
        "Identifier": dataCollection['Identifier'],
        "AgencyId": dataCollection['AgencyId'],
        "Version": dataCollection['Version'],
        "ItemType": C.item_code('Data Collection'),
        "Item": dataCollectionWithoutInstrumentAndQuestionSchemeReferences
    })

studyItems = []
updatedStudies = []
for study in studies:
    studyItem=defusedxml.ElementTree.fromstring(C.get_item_xml(study['AgencyId'],
        study['Identifier'], version=study['Version'])['Item'])
    # We use deepcopy to create a list of the unmodified items that we will use in a
    # 'before' and 'after' comparison'.    
    studyItems.append(deepcopy(studyItem))
    studiesWithoutPhysicalInstanceReferences = remove_elements_from_item(
        studyItem, "PhysicalInstanceReference", C)
    studiesWithoutPhysicalInstanceAndRequiredResourceReferences = remove_elements_from_item(
        studyItem, "RequiredResourcePackages", C)
    updatedStudies.append({
        "Identifier": study['Identifier'],
        "AgencyId": study['AgencyId'],
        "Version": study['Version'],
        "ItemType": C.item_code('Study'),
        "Item": studiesWithoutPhysicalInstanceAndRequiredResourceReferences
    })

update_repository(updatedDataCollections,
    "Remove instrument and questionScheme references from data collections", C)

update_repository(updatedStudies,
    "Remove physicalInstance and resourcePackage references from studies", C)

# Code for validating that the reference elements have been removed from the data collection
# and study items. The code will print the number of reference elements that were present in
# the item before we removed them, and the number of reference elements present after we
# removed them (there should be 0 reference elements present after we perform the removal
# operations).
#
# Execute this code by making sure you have defined the 'validate_removal_of_references' and
# 'count_elements_in_items' methods in your Python interpreter environment (e.g. by copying 
# and pasting the method code below into your Python interpreter) and typing:
#
# validate_removal_of_references()

def count_elements_in_items(items, elementTagname):
    """Given a list of items and the tag name of an element, this function counts
    the number of occurrences across all items of elements with that tag name."""
    elementCount=0
    for item in items: 
       elementCount += len(get_elements_of_type(item, elementTagname))
    return elementCount

def validate_removal_of_references():
    print("Number of instrument references in data collections before removal: "
       f"{count_elements_in_items(dataCollectionItems, "InstrumentReference")}")
    print("Number of instrument references in data collections after removal: " 
       f"{count_elements_in_items([x['Item'] for x in updatedDataCollections], "InstrumentReference")}")
    print("Number of question scheme references in data collections before removal: "
       f"{count_elements_in_items(dataCollectionItems, "QuestionSchemeReference")}")
    print("Number of question scheme references in data collections after removal: "
       f"{count_elements_in_items([x['Item'] for x in updatedDataCollections], "QuestionSchemeReference")}")
    print("Number of physical instance references in studies before removal: "
       f"{count_elements_in_items(studyItems, "PhysicalInstanceReference")}")
    print("Number of physical instance references in studies after removal: "
       f"{count_elements_in_items([x['Item'] for x in updatedStudies], "PhysicalInstanceReference")}") 
    print("Number of required resource packages in studies before removal: "
       f"{count_elements_in_items(studyItems, "RequiredResourcePackages")}")
    print("Number of required resource packages in studies after removal: "
       f"{count_elements_in_items([x['Item'] for x in updatedStudies], "RequiredResourcePackages")}")