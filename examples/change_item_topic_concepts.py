"""
The set of commands that need to be executed from the root directory of the colectica-api
repository within a Python shell for changing item topics is:

from examples.lib.utility import update_repository
from colectica_api import ColecticaObject
import examples.change_item_topic_concepts

USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)

updated_items=[]
examples.change_item_topic_concepts.update_topics('examples/smallTest.xlsx', C, updated_items)
update_repository(updated_items, "Update item topics/concepts", C)
"""

from colectica_api import ColecticaObject
import defusedxml
#pip install openpyxl #might need to install openpyxl, a dependency for read-excel
import pandas as pd
from examples.lib.utility import (
    get_current_state_of_topic_group,
    get_elements_of_type,
    get_namespace,
    create_concept_reference,
    update_list_of_topic_groups,
    update_repository
)

def update_topics(topic_updates_file, C, updated_items=None):
    """Method used for reassigning new topics/concepts to items. The code iterates through a 
    data frame containing details of new item topic assignments and creates DDI objects 
    representing the updated items, which will then be used to perform the reassignments.

    Arguments:
        topic_updates_file (string): The name of a file containing details of a topic reassignment.
        C (ColecticaObject): an authenticated ColecticaObject instance.
        updated_items (list): List of dict-like entries representing items.

    Returns:
        A list of dict-like objects containing the items which have had their topics updated.  
    """
    # Initialise lists...
    if updated_items is None:
        updated_items = []
    items_not_present_in_source_topic = []
    items_present_in_destination_topic = []
    reference_from_source_ddi_version = None
    data = pd.read_excel(topic_updates_file)
    # Iterate through the rows in the data frame. Each row contains details of a topic
    # reassignment for a item...
    for index, topic_reassignment_details in data.iterrows():
        print("Performing the following topic reassignment...")
        print(f"Item {topic_reassignment_details['ItemName']} to {topic_reassignment_details['NewTopic']}")
        url = topic_reassignment_details.iloc[2]
        item_agency_id = url.split("/")[4]
        item_identifier = url.split("/")[5]
        # We get the current state of the item, including it's topic reference
        item = get_current_state_of_topic_group(
            item_agency_id,
            item_identifier,
            updated_items,
            C
            )
        item_dict = C.get_item_xml(
            item_agency_id, 
            item_identifier)
        item = defusedxml.ElementTree.fromstring(item_dict['Item'])
        namespaces=get_namespaces(item)
        reusable_ns = next(
            (ns for ns in namespaces if 'reusable' in ns),
            None
            )
        references_to_remove=get_elements_of_type(item, 'ConceptReference')
        for reference_to_remove in references_to_remove:
            item[0].remove(reference_to_remove)
            # We need to take note of the namespace version for the reusable element,
            # we may use this later when determining if we need to update the version
            # number to the version used in the destination topic group.
            reference_from_source_ddi_version = ("ddi:reusable:"
                f"{get_namespace(reference_to_remove.tag).split(':')[2]}")
        concept_item = C.search_items(C.item_code('Concept'),
                     SearchTerms=[topic_reassignment_details['NewTopic']],
                     SearchTargets="Name")['Results']
        if len(concept_item)==1:            
            new_reference=create_concept_reference(concept_item[0]['AgencyId'], 
                concept_item[0]['Identifier'],
                concept_item[0]['Version'],
                reusable_ns)
            item[0].append(new_reference)
            # below needs to be updated for items
            update_list_of_topic_groups(item, 
                                   item_agency_id,
                                   item_identifier,
                                   item_dict['Version'],
                                   item_dict['ItemType'],
                                   updated_items)
        else:
            print(f"Multiple concept items found for topic {topic_reassignment_details['NewTopic']}"
                  f", could not perform topic reassignment.")
    return updated_items

def get_namespaces(element):
    """Get the set of namespaces used in an XML block."""
    namespaces = set()
    for elem in element.iter():
        # Check element tag
        if elem.tag.startswith('{'):
            namespaces.add(elem.tag.split('}')[0][1:])
        # Check attribute names
        for attr in elem.attrib:
            if attr.startswith('{'):
                namespaces.add(attr.split('}')[0][1:])
    return namespaces