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

# Specify the Millenium Cohort Study (MCS) which we want to search for items in. Make sure you 
# use the most up to date version of the study/series!
search_sets = [{"agencyId": "uk.cls.mcs", 
                "identifier": "0d8a7220-c61b-4542-967d-a40cb5aca430", 
                "version": "58"}]
                
studies=C.search_items([C.item_code('Study')], SearchSets=search_sets)['Results']

dataCollections=C.search_items([C.item_code('Data Collection')], SearchSets=search_sets)['Results']

dataCollectionItems = []
updatedDataCollections = []
for dataCollection in dataCollections:
    dataCollectionItem=defusedxml.ElementTree.fromstring(C.get_item_xml(dataCollection['AgencyId'],
        dataCollection['Identifier'])['Item'])
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
        study['Identifier'])['Item'])
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
# the items before we removed them, and the number of reference elements present after we
# removed them (there should be 0 reference elements present after we perform the removal
# operations).
#
# Execute this code by making sure you have defined the 'validate_removal_of_references' and
# 'count_elements_in_items' methods in your Python interpreter environment (e.g. by copying 
# and pasting the methods code below into your Python interpreter) and typing commands such as
# the one below, which checks that the 'InstrumentReference' elements that were present in the
# objects in the dataCollectionItems array are not present in the objects in the 
# updatedDataCollections array:
#
# validate_removal_of_references(dataCollectionItems, updatedDataCollections, "InstrumentReference")

def count_elements_in_items(items, elementTagname):
    """Given a list of items and the tag name of an element, this function counts
    the number of occurrences across the list of items of elements with that tag name."""
    elementCount=0
    for item in items: 
       elementCount += len(get_elements_of_type(item, elementTagname))
    return elementCount

def validate_removal_of_references(itemsBefore, itemsAfter, referenceTagName):
    referencesBefore = count_elements_in_items(itemsBefore, referenceTagName)
    itemTypes = set([C.item_code_inv(x['ItemType']) for x in itemsAfter])
    print(f"Number of {referenceTagName} elements in {itemTypes} items before removal: {referencesBefore}")
    referencesAfter = count_elements_in_items([x['Item'] for x in itemsAfter], "VariableReference")
    print(f"Number of {referenceTagName} elements in {itemTypes} items after removal: {referencesAfter}")

validate_removal_of_references(dataCollectionItems, updatedDataCollections, "InstrumentReference")
validate_removal_of_references(dataCollectionItems, updatedDataCollections, "QuestionSchemeReference")
validate_removal_of_references(studyItems, updatedStudies, "PhysicalInstanceReference")
validate_removal_of_references(studyItems, updatedStudies, "RequiredResourcePackages")
