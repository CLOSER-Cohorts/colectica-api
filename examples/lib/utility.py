"""Utility functions for processing XML and DDI data."""
import re
from xml.etree import ElementTree as ET

def get_namespace(tag):
    """Get the namespace for an XML element."""
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)

def find_reference(xml_tree, agency, identifier):
    """Find a reference to an item in an XML tree/element (e.g. a 'VariableGroup' element)"""
    ret_elem = None
    for elem in xml_tree.findall(".//"):
        element_namespace = get_namespace(elem.tag)
        if (elem.find(f".//{{{element_namespace}}}Agency") is not None and
           elem.find(f".//{{{element_namespace}}}Agency").text == agency and
           elem.find(f".//{{{element_namespace}}}ID") is not None and
           elem.find(f".//{{{element_namespace}}}ID").text == identifier):
            ret_elem = elem
    return ret_elem

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

def convert_xml_element_to_json(xml_element):
    """Convert an XML element to a JSON representation."""
    json_object = {}
    for elem in xml_element.findall(".//"):
        start_of_tag_name = elem.tag.index("}")+1
        json_object[elem.tag[start_of_tag_name:]] = elem.text
    return json_object