"""Utility functions for processing XML and DDI data."""
import re
from xml.etree import ElementTree as ET
from colectica_api import ColecticaObject
import defusedxml

def get_namespace(tag):
    """Get the namespace for an XML element."""
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)

def referencesAreEquivalent(reference1, reference2):
    ref1Elems=[]
    ref2Elems=[]
    for elem in reference1.findall(".//"):
        ref1Elems.append(elem.tag + ": " + elem.text)
    print(sorted(ref1Elems))
    for elem in reference2.findall(".//"):
        ref2Elems.append(elem.tag + ": " + elem.text)
    print(sorted(ref2Elems))
    return sorted(ref1Elems) == sorted(ref2Elems)             

def find_reference(xml_tree, agency, identifier):
    """Find a reference to an item in an XML tree/element (e.g. a 'VariableGroup' element)"""
    matching_references = []
    for elem in xml_tree.findall(".//"):
        if (len(elem)>0):
            element_namespace = get_namespace(elem[0].tag)
        else:
            element_namespace = get_namespace(elem.tag)
        if (elem.find(f".//{{{element_namespace}}}Agency") is not None and
           elem.find(f".//{{{element_namespace}}}Agency").text == agency and
           elem.find(f".//{{{element_namespace}}}ID") is not None and
           elem.find(f".//{{{element_namespace}}}ID").text == identifier):
            matching_references.append(elem)
    return matching_references

def create_variable_reference(agency_id, item_id, version, item_type, namespace):
    """Create an XML element representing a VariableReference"""
    new_element = ET.Element(f"{{{namespace}}}VariableReference")
    agency_element = ET.Element(f"{{{namespace}}}Agency")
    id_element = ET.Element(f"{{{namespace}}}ID")
    version_element = ET.Element(f"{{{namespace}}}Version")
    type_of_object_element = ET.Element(f"{{{namespace}}}TypeOfObject")
    id_element.text = item_id
    agency_element.text = agency_id
    version_element.text = str(version)
    type_of_object_element.text = item_type
    new_element.append(agency_element)
    new_element.append(id_element)
    new_element.append(version_element)
    new_element.append(type_of_object_element)
    return new_element

def create_question_reference(agency_id, item_id, version, item_type, namespace, namespace2):
    newElement = ET.Element(f"{{{namespace2}}}QuestionItemReference")
    agencyElement=ET.Element(f"{{{namespace}}}Agency")
    idElement=ET.Element(f"{{{namespace}}}ID")
    versionElement= ET.Element(f"{{{namespace}}}Version")
    typeOfObjectElement = ET.Element(f"{{{namespace}}}TypeOfObject")
    idElement.text=item_id
    agencyElement.text=agency_id
    versionElement.text=str(version)
    typeOfObjectElement.text=item_type
    newElement.append(agencyElement)
    newElement.append(idElement)
    newElement.append(versionElement)
    newElement.append(typeOfObjectElement)
    return newElement    

def convert_xml_element_to_json(xml_element):
    """Convert an XML element to a JSON representation."""
    json_object = {}
    for elem in xml_element.findall(".//"):
        start_of_tag_name = elem.tag.index("}")+1
        json_object[elem.tag[start_of_tag_name:]] = elem.text
    return json_object

def get_urn_from_item(item):
   return "urn:ddi:" + item['AgencyId'] + ":" + item['Identifier'] + ":" + str(item['Version'])

def get_current_state_of_topic_group(agency_id, identifier, updated_groups, C, version=None):
    """We may be performing multiple updates to the topic variable groups, so instead of 
    retrieving/updating/writing data using the Colectica REST API every time we need to update 
    a variable group, we will retrieve the most recent version of it from the Colectica repository
    using the Colectica REST API for the first update, and on subsequent updates we will modify the
    in-memory version which is stored in the updated_groups array."""
    updated_referencing_item = [x for x in updated_groups if x[0] == identifier]
    if len(updated_referencing_item) > 0:
        referencing_item = updated_referencing_item[0][4]
    else:
        fragment_xml = C.get_item_xml(
            agency_id, identifier, version=version)['Item']
        referencing_item = defusedxml.ElementTree.fromstring(fragment_xml)
    return referencing_item

def update_list_of_topic_groups(updated_group, agency, identifier, version,
                                      item_type, updated_groups_list):
    """Update the in-memory list of variable groups representing topics. If the topic group we have
    updated is not in already in the list, we append it to the list."""
    if ([x[0] for x in updated_groups_list].count(identifier) > 0):
        index_of_updated_ref = [x[0] for x in updated_groups_list].index(identifier)
        updated_groups_list[index_of_updated_ref] = (
            identifier, agency, version, item_type, updated_group)
    else:
        updated_groups_list.append(
            (identifier, agency, version, item_type, updated_group))
 
def get_topic_of_item(topic_name, topic_type, containing_item_name, containing_item_type, C):
    "Method for getting the topic that an item is assigned to."
    containing_item = C.search_items(
            [containing_item_type],
            SearchTerms=containing_item_name,
            SearchLatestVersion=True)['Results']
    if len(containing_item) == 1:
            # We create a JSON object representing the containing item.
            search_sets = [{
                "agencyId": containing_item[0]['AgencyId'],
                "identifier": containing_item[0]['Identifier'],
                "version": containing_item[0]['Version']
            }]
            topic_group_identifiers = C.search_items(topic_type,
                     SearchSets=search_sets,
                     SearchTerms=[str(topic_name)])['Results']
    else:
            topic_group_identifiers = []
    return topic_group_identifiers

def get_topic_for_item(agency_id, identifier, version, topic_name):
    related_groups = C.search_relationship_byobject(agency_id, identifier, Version=version, item_types=[C.item_code("Question Group")])
    for related_group in related_groups:
        relatedQuestionGroupMostRecentVersion=C.get_item_xml(relatedQuestionGroup['AgencyId'], relatedQuestionGroup['Identifier'])
        questionGroupName=getElementByName(defusedxml.ElementTree.fromstring(relatedQuestionGroupMostRecentVersion['Item']), 'QuestionGroupName')['String']
        if identifier in relatedQuestionGroupMostRecentVersion['Item'] and topic_name == questionGroupName:
            return relatedQuestionGroupMostRecentVersion

def get_url_from_item(item, hostname):
   return f"http://{hostname}/item/" + item['AgencyId'] + "/" + item['Identifier'] + "/" + str(item['Version'])

def get_urn_from_item(item):
   return "urn:ddi:" + item['AgencyId'] + ":" + item['Identifier'] + ":" + str(item['Version'])

def createColecticaRepositoryConnection(hostname, username, password, verify_ssl=False):
    return ColecticaObject(hostname, username, password,verify_ssl=False)

def map_between_questions_and_variables(items, C):
    """Method for mapping between questions and variables.
    """
    related_items=[]
    # Iterate through the items...
    for item in items:
        agency_id = item.split(":")[2]
        identifier = item.split(":")[3]
        version = item.split(":")[4]
        itemJson = C.get_item_json(agency_id, identifier, version=version)
        item_type = C.item_code_inv(itemJson['ItemType'])
        if item_type == 'Variable':
            all_related_items= C.search_relationship_bysubject(agency_id, identifier, Version=version, item_types=[C.item_code("Question")])
        elif item_type == 'Question':
            all_related_items= C.search_relationship_byobject(agency_id, identifier, Version=version, item_types=[C.item_code("Variable")])
        for related_item in all_related_items:
            related_item_json=C.get_item_json(related_item['Item1']['Item3'], related_item['Item1']['Item1'], version=related_item['Item1']['Item2'])
            agency_id = related_item_json['AgencyId']
            identifier = related_item_json['Identifier']
            version = related_item_json['Version']
            item_urn = "urn:ddi:" + agency_id + ":" + identifier + ":" + str(version)
            related_items.append(item_urn)
    return related_items
