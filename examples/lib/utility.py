"""Utility functions for processing XML and DDI data."""
import re
from xml.etree import ElementTree as ET
from colectica_api import ColecticaObject
import defusedxml
from collections import Counter

def get_namespace(tag):
    """Get the namespace for an XML element."""
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)

def references_are_equal(reference1, reference2):
    """Determine if two references are equal by comparing their elements."""
    ref_1_elems=[]
    ref_2_elems=[]
    for elem in reference1.findall(".//"):
        ref_1_elems.append(elem.tag + ": " + elem.text)
    for elem in reference2.findall(".//"):
        ref_2_elems.append(elem.tag + ": " + elem.text)
    return sorted(ref_1_elems) == sorted(ref_2_elems)

def find_all_references(xml_tree, agency, identifier):
    """Find all references to another item in an XML tree/element"""
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

def create_concept_reference(agency_id, item_id, version, namespace):
    """Create an XML element representing a ConceptReference"""
    new_element = ET.Element(f"{{{namespace}}}ConceptReference")
    agency_element = ET.Element(f"{{{namespace}}}Agency")
    id_element = ET.Element(f"{{{namespace}}}ID")
    version_element = ET.Element(f"{{{namespace}}}Version")
    type_of_object_element = ET.Element(f"{{{namespace}}}TypeOfObject")
    id_element.text = item_id
    agency_element.text = agency_id
    version_element.text = str(version)
    type_of_object_element.text = "Concept"
    new_element.append(agency_element)
    new_element.append(id_element)
    new_element.append(version_element)
    new_element.append(type_of_object_element)
    return new_element

def create_variable_reference(agency_id, item_id, version, namespace):
    """Create an XML element representing a VariableReference"""
    new_element = ET.Element(f"{{{namespace}}}VariableReference")
    agency_element = ET.Element(f"{{{namespace}}}Agency")
    id_element = ET.Element(f"{{{namespace}}}ID")
    version_element = ET.Element(f"{{{namespace}}}Version")
    type_of_object_element = ET.Element(f"{{{namespace}}}TypeOfObject")
    id_element.text = item_id
    agency_element.text = agency_id
    version_element.text = str(version)
    type_of_object_element.text = "Variable"
    new_element.append(agency_element)
    new_element.append(id_element)
    new_element.append(version_element)
    new_element.append(type_of_object_element)
    return new_element

def create_question_reference(agency_id, item_id, version, namespace, namespace2):
    """Create an XML element representing a QuestionItemReference"""
    new_element = ET.Element(f"{{{namespace2}}}QuestionItemReference")
    agency_element=ET.Element(f"{{{namespace}}}Agency")
    id_element=ET.Element(f"{{{namespace}}}ID")
    version_element= ET.Element(f"{{{namespace}}}Version")
    type_of_object_element = ET.Element(f"{{{namespace}}}TypeOfObject")
    id_element.text=item_id
    agency_element.text=agency_id
    version_element.text=str(version)
    type_of_object_element.text="QuestionItem"
    new_element.append(agency_element)
    new_element.append(id_element)
    new_element.append(version_element)
    new_element.append(type_of_object_element)
    return new_element

def create_group_reference(agency_id, item_id, version, namespace_version, topic_type, C):
    """Create an XML element representing a Variable/QuestionGroup.
    
    Arguments:
        agency_id (str): Agency to which the item that we are creating a reference for belongs. 
            For example, ``"uk.cls.nextsteps"``.
        item_id (str): Identifier for the item that we are creating a reference for.
            For example, ``"a6f96245-5c00-4ad3-89e9-79afaefa0c28"``.
        version (str): The number indicating the version of the item we are creating/
        namespace_version (str): the version of the namespaces to which various elements belong in the
            reference we are creating.
        topic_type (uuid): the type of topic/variable we are creating a reference to.
        C (ColecticaObject): an authenticated ColecticaObject instance.
    Returns:
        ElementTree.Element: An ElementTree.Element representing the group reference.
    """
    type_of_object_element = ET.Element(f"{{ddi:reusable:{namespace_version}}}TypeOfObject")
    if topic_type==C.item_code('Variable Group'):
        new_element = ET.Element(f"{{ddi:logicalproduct:{namespace_version}}}VariableGroupReference")
        type_of_object_element.text = "VariableGroup"
    elif topic_type==C.item_code('Question Group'):
        new_element = ET.Element(f"{{ddi:datacollection:{namespace_version}}}QuestionGroupReference")
        type_of_object_element.text = "QuestionGroup"
    agency_element = ET.Element(f"{{ddi:reusable:{namespace_version}}}Agency")
    id_element = ET.Element(f"{{ddi:reusable:{namespace_version}}}ID")
    version_element = ET.Element(f"{{ddi:reusable:{namespace_version}}}Version")
    id_element.text = item_id
    agency_element.text = agency_id
    version_element.text = str(version)
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

def get_current_state_of_topic_group(agency_id, identifier, updated_groups, C, version=None):
    """We may be performing multiple updates to the topic groups, so instead of 
    retrieving/updating/writing data using the Colectica REST API every time we need to update 
    a group, we will retrieve the most recent version of it from the Colectica repository
    using the Colectica REST API for the first update, and on subsequent updates we will modify the
    in-memory version which is stored in the updated_groups array.
    
    Arguments:
        agency_id (str): Agency to which the group that we are getting the current state for belongs. 
            For example, ``"uk.cls.nextsteps"``.
        item_id (str): Identifier for the group that we are getting the current state for.
            For example, ``"a6f96245-5c00-4ad3-89e9-79afaefa0c28"``.
        updated_groups: list of groups within which we search for the group specified by the
            agency_id and identifier and arguments, and the version keyword argument (if specified).
        C (ColecticaObject): an authenticated ColecticaObject instance.
        
    Keyword arguments:
        version (int): The number indicating the version of the group we are searching for.

    Returns:
        ElementTree.Element: An ElementTree.Element representing the topic group.     
    """
    updated_referencing_item = [x for x in updated_groups if x['AgencyId'] == agency_id 
       and x['Identifier']==identifier]
    if len(updated_referencing_item) > 0:
        referencing_item = updated_referencing_item[0]['Item']
    else:
        fragment_xml = C.get_item_xml(
            agency_id, identifier, version=version)['Item']
        referencing_item = defusedxml.ElementTree.fromstring(fragment_xml)
    return referencing_item

def update_list_of_topic_groups(updated_group, agency, identifier, version,
                                      item_type, updated_groups_list, dataset=None):
    """Update the in-memory list of groups representing topics. If the topic group we have
    updated is not in already in the list, we append it to the list.
    
    Arguments:
        updated_group: the value for a group which we are either inserting into updated_groups_list (if
            an earlier version of the group is not there), or we are updating (if an earlier version is
            in updated_groups_list)
        agency_id (str): Agency to which the group that we are updating belongs. 
            For example, ``"uk.cls.nextsteps"``.
        identifier (str): Identifier for the group that we are updating.
            For example, ``"a6f96245-5c00-4ad3-89e9-79afaefa0c28"``.
        version (int): the number indicating the version of the group we are updating.
        item_type(uuid): the type of the group we are updating (e.g. C.item_code('Variable Group'))
        updated_groups_list: list of groups within which we search for the group specified by the
            agency_id, identifier and version arguments.
    
    Keyword arguments:
        dataset (str): the name of the dataset to which the item belongs, if applicable (i.e. if the
           item_type is 'Variable Group')

    Returns:
        None: The function updates updated_groups_list in place.
    """
    if ([x['Identifier'] for x in updated_groups_list].count(identifier) > 0):
        index_of_updated_ref = [x['Identifier'] for x in updated_groups_list].index(identifier)
        updated_groups_list[index_of_updated_ref] = {
            "Identifier": identifier,
            "AgencyId": agency,
            "Version": version,
            "ItemType": item_type,
            "Item": updated_group,
            "DatasetName": dataset
        }
    else:
        updated_groups_list.append({
            "Identifier": identifier,
            "AgencyId": agency,
            "Version": version,
            "ItemType": item_type,
            "Item": updated_group,
            "DatasetName": dataset
        })
 
def get_item_from_topic_name(topic_name, 
    topic_type, 
    containing_item, 
    C, 
    groupsInDatasets=[], 
    dataset_name="", 
    datasetToZeroGroupMappings={}):
    """Method for getting a topic item given the topic's name as a string (e.g. '11609'), the topic 
    type (e.g. Question Group, Variable Group), and the item within which that topic is contained 
    (e.g. a Physical Instance/Data File or a Data Collection object).

    Note that the topic_type input argument must be provided as a UUID (as specified at
    https://docs.colectica.com/repository/technical/item-type-identifiers/). Item types can be 
    mapped to their identifiers using the C.item_code function, e.g. C.item_code("Question Group"),
    C.item_code("Data Collection").

    Arguments:
        topic_name (str): the name of the topic we are searching for (e.g. '11609').
        topic_type (str): the type of the topic we are searching for.
        containing_item (dict): A dictionary containing details of the item containing the item being reassigned.
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Keyword arguments:
        datasetToZeroGroupMappings (dict): A dictionary mapping dataset names to level zero topic groups. 

    Returns:
        list: A list containing Variable Groups/Question Groups items that represent topics.
    """
    item=[x for x in groupsInDatasets if x['DatasetName']==dataset_name 
        and x['VariableGroupName']==str(topic_name) and x['TopicType']==topic_type]
    if len(item)==1:
        if item[0]['VariableGroupUrn']=="NA":
            topic_group_identifiers=[]
        else:
            topic_group_identifiers=[C.get_item_json(
            item[0]['VariableGroupUrn'].split(":")[2],
            item[0]['VariableGroupUrn'].split(":")[3],
            version=item[0]['VariableGroupUrn'].split(":")[4]
        )]
    else:
        topic_group_identifiers = C.search_items(topic_type,
                     SearchSets=containing_item,
                     SearchTerms=[str(topic_name)],
                     SearchTargets="Name",
                     UsePrefixSearch=False)['Results']
        print(datasetToZeroGroupMappings)
        print(containing_item)
        if len(topic_group_identifiers)==0:
            if not get_urn_from_item(containing_item) in datasetToZeroGroupMappings.keys():
                # If we cannot determine the level zero group for the dataset (i.e. topic_group_identifiers is
                # empty) we must try to determine the level zero group by inspecting the variables in the dataset...
                print((f"Cannot determine level zero group for dataset {get_urn_from_item(containing_item)}, " 
                    "inspecting variables..."))
                datasetVars=C.query_set(containing_item['AgencyId'], 
                    containing_item['Identifier'],item_types=[C.item_code('Variable')])
                level_zero_groups=[]
                count=0
                print(f"Verifying the level zero group for {len(datasetVars)} variables in dataset {get_urn_from_item(containing_item)}...")
                for var in datasetVars[0:4]:
                    varGroups=C.search_relationship_byobject(var['Item1']['Item3'], var['Item1']['Item1'], 
                        Version=var['Item1']['Item2'], item_types=[topic_type]) 
                    for varGroup in varGroups:
                        count=count+1
                        var_group_item=C.get_item_json(varGroup['Item1']['Item3'], varGroup['Item1']['Item1'], 
                            version=varGroup['Item1']['Item2'])
                        level_zero_group=get_level_zero_group_for_topic(var_group_item, C)
                        if level_zero_group is not None:
                            level_zero_groups.append(level_zero_group)            
                containing_level_zero_group = []
                if len(set([x[0][2].text for x in level_zero_groups]))==1:
                    containing_level_zero_group = [{
                    "AgencyId": level_zero_groups[0][0][1].text,
                    "Identifier": level_zero_groups[0][0][2].text,
                    "Version": level_zero_groups[0][0][3].text,
                    }]
                    datasetToZeroGroupMappings[get_urn_from_item(containing_item)]=containing_level_zero_group
                else:
                    containing_level_zero_group = []
                # Do a search for the first three numbers of the topic group, and then filter
                # the results in a list comprehension to find the exact match, because it's
                # quicker than just searching for the exact match directly.
                topic_group_identifiers = [x for x in C.search_items(topic_type,
                     SearchSets=containing_level_zero_group,
                     SearchTerms=[str(topic_name)[0:3]],
                     UsePrefixSearch=False,
                     SearchTargets="Name")['Results'] if x['ItemName']['en-GB']==str(topic_name)]
            else:
                containing_level_zero_group=datasetToZeroGroupMappings[get_urn_from_item(containing_item)]
                # Do a search for the first three numbers of the topic group, and then filter
                # the results in a list comprehension to find the exact match, because it's
                # quicker than just searching for the exact match directly.
                topic_group_identifiers = [x for x in C.search_items(topic_type,
                     SearchSets=containing_level_zero_group,
                     SearchTerms=[str(topic_name)[0:3]],
                     UsePrefixSearch=True,
                     SearchTargets="Name")['Results'] if x['ItemName']['en-GB']==str(topic_name)]
        else:
            containing_level_zero_group=C.search_relationship_bysubject(containing_item['AgencyId'],
                containing_item['Identifier'], item_types=C.item_code('Variable Group'), 
                Version=containing_item['Version'], Descriptions=True)
            if len(containing_level_zero_group)==1:
                containing_level_zero_group_item=C.get_item_json(containing_level_zero_group[0]['AgencyId'],
                containing_level_zero_group[0]['Identifier'], version=containing_level_zero_group[0]['Version'])
                if containing_level_zero_group_item['Concept']==None:
                    datasetToZeroGroupMappings[get_urn_from_item(containing_item)]=[{
                        "AgencyId": containing_level_zero_group[0]['AgencyId'],
                        "Identifier": containing_level_zero_group[0]['Identifier'],
                        "Version": containing_level_zero_group[0]['Version'],
                        }]
    for topic_group_identifier in topic_group_identifiers:
        if topic_group_identifier['ItemName']['en-GB']==str(topic_name) and len(item)==0:
                groupsInDatasets.append({
                    "DatasetName": dataset_name,
                    "VariableGroupName": str(topic_name),
                    "VariableGroupUrn": "urn:ddi:" + topic_group_identifier['AgencyId'] + ":" + topic_group_identifier['Identifier'] + ":" + str(topic_group_identifier['Version']),
                    "TopicType": topic_type
                })
    if len(item)==0:
        groupsInDatasets.append({
                    "DatasetName": dataset_name,
                    "VariableGroupName": str(topic_name),
                    "VariableGroupUrn": "NA",
                    "TopicType": topic_type
                })
    return [x for x in topic_group_identifiers if x['ItemName']['en-GB']==str(topic_name)]

def get_topic_for_item(agency_id, identifier, version, item_type, C):
    """This function gets the topic item(s) for an item (i.e. question/variable).

    Arguments:
        agency_id(str): the agency for the question/variable we are trying to get the topic for.
        identifier(str): the identifier for the question/variable we are trying to get the topic for.
        version(str): the version for the question/variable we are trying to get the topic for.
        item_type(uuid): the UUID code representing the topic's type (e.g. C.item_code("Variable Group")).

    Returns:
        list: a list of variable/question groups representing topics.
    """
    topics_assigned_to_item=[]
    related_groups = C.search_relationship_byobject(agency_id, identifier, Version=version, item_types=[item_type])
    for related_group in related_groups:
        related_question_group_most_recent_version=C.get_item_xml(related_group['Item1']['Item3'], 
            related_group['Item1']['Item1'])
        if identifier in related_question_group_most_recent_version['Item']:
            topics_assigned_to_item.append(related_question_group_most_recent_version)
    return topics_assigned_to_item

def get_url_from_item(item, hostname):
   return f"http://{hostname}/item/{item['AgencyId']}/{item['Identifier']}/{str(item['Version'])}"

def get_urn_from_item(item):
   return f"urn:ddi:{item['AgencyId']}:{item['Identifier']}:{str(item['Version'])}"

def get_urn_from_fragment(fragment_xml):
   urnElement=get_elements_of_type(fragment_xml, "URN")
   if len(urnElement)==1:
      return urnElement[0].text
   else:
      return None

def map_between_questions_and_variables(items, C):
    """Method for mapping between lists of questions and variables. The 'items' input parameter
    contains a list of urns for questions/variables, this function returns a list containing the 
    urns for variables associated with the questions in the list, or urns for the questions 
    associated with the variables in the list.
    """
    related_items=[]
    # Iterate through the items...
    for item in items:
        agency_id = item.split(":")[2]
        identifier = item.split(":")[3]
        version = item.split(":")[4]
        item_json = C.get_item_json(agency_id, identifier, version=version)
        item_type = C.item_code_inv(item_json['ItemType'])
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

def update_repository(updated_items, transaction_message, C):
    """Update a set of items in the repository. For example, once we have made updates to 
    question/variable groups we can use this function to create a transaction using the Colectica 
    REST API, add all the items in this array to that transaction, and finally commit the 
    transaction.
    """
    transaction_response = C.create_transaction()
    transaction_id = transaction_response['TransactionId']
    for item in updated_items:
        fragment_string = defusedxml.ElementTree.tostring(item['Item'], encoding='unicode')
        C.add_items_to_transaction(item['AgencyId'], item['Identifier'], item['Version'], fragment_string, 
                                   item['ItemType'], transaction_id)
    commit_response = C.commit_transaction(transaction_id, transaction_message, 3)
    return commit_response

def getTriple(tripleElem):
    triple = {}
    for elem in tripleElem.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        triple[elem.tag[startOfTagName:]] = elem.text
    return(triple)

def get_element_fragment_by_name(xmlTree, elementName):
    retElem=None
    for elem in xmlTree.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementName:
            retElem = elem
    return retElem

def get_element_by_name(xmlTree, elementName):
    retElem=None
    for elem in xmlTree.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementName:
            retElem = getTriple(elem)
    return retElem

def get_elements_of_type(xmlTree, elementName):
    retElem=None
    elems=[]
    for elem in xmlTree.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementName:
            elems.append(elem)            	
    return elems

def remove_elements_from_item(item, element_name, C):
    elementRefs=get_elements_of_type(item, element_name)
    if len(elementRefs) > 0:
        print(f"Removing {len(elementRefs)} occurrence(s) of {element_name}...")
    for y in elementRefs:
        item[0].remove(y)
    return item
 
def create_input_file(input_file_name, output_file_name, C):
    """This is a utility function that creates an input file for the find_topics_to_create method by 
        extracting information from an existing file that is not in the required format.
    
    Arguments:
        input_file_name (str): the name for a file that we want to extract information from.
        output_file_name (str): the name for the output file to create.

    Returns:
        None: the output file that is in the format required by the find_topics_to_create method is created
            in the current working directory. 
    """
    data = pd.read_excel(input_file_name).drop_duplicates()
    new_input_df = pd.DataFrame(columns=["Container", "ItemName", "URL", "Label", "CurrentTopic", "NewTopic"])
    newRow={}
    for topic_reassignment_details in data.iloc:
        physical_instance_containing_variable = C.search_items(
            C.item_code('Data File'),
            SearchTerms=str(topic_reassignment_details.iloc[0]).strip(),
            SearchLatestVersion=True)['Results']
        if len(physical_instance_containing_variable) == 1:
            # We need to search within the physical instance/dataset for the variable named in the
            # current row. We create a JSON object representing the physical instance/dataset.
            search_sets = [{
                "agencyId": physical_instance_containing_variable[0]['AgencyId'],
                "identifier": physical_instance_containing_variable[0]['Identifier'],
                "version": physical_instance_containing_variable[0]['Version']
            }]
            # For this search, the 'SearchTerms' keyword argument represents the name of the
            # variable we are reassigning to a new topic. The 'SearchSets' keyword argument
            # represents the physical instance/dataset we are searching for that variable in.
            variable_metadata = C.search_items(C.item_code('Variable'), SearchSets=search_sets,
               SearchTerms=[str(topic_reassignment_details.iloc[2]).strip()])['Results']
            if len(variable_metadata) == 1:
                url=get_url_from_item(variable_metadata[0], 'discovery.closer.ac.uk')
                new_row={"Container": topic_reassignment_details.iloc[0],
                    "ItemName": topic_reassignment_details.iloc[2],
                    "URL": url,
                    "Label": topic_reassignment_details.iloc[3],
                    "CurrentTopic": topic_reassignment_details.iloc[4],
                    "NewTopic": topic_reassignment_details.iloc[6]}
                if str(topic_reassignment_details.iloc[6])!='nan':        
                    new_input_df.loc[len(new_input_df)] = new_row
    new_input_df.to_excel(output_file_name, index=False)

def create_variable_group(group_name, 
    group_label, 
    item_id, 
    namespace_version, 
    concept_agency_id, 
    concept_identifier, 
    concept_version):
    """Create a variable group representing a topic.

    Arguments:
        group_name: the name of the topic/variable group.
        group_label: the label for the topic/variable group.
        item_id: the identifier for the topic/variable group.
        namespace_version: the version for the namespaces for various elements.
        concept_agency_id: the agency for the concept which this topic/variable group represents.
        concept_identifier: the identifier for the concept which this topic/variable group represents.   
        concept_version: the version for the concept which this topic/variable group represents.

    Returns:
        ElementTree.Element: An ElementTree.Element representing the variable group.
    """
    fragmentString = f"""<Fragment xmlns:r="ddi:reusable:{namespace_version}" xmlns="ddi:instance:{namespace_version}">
      <VariableGroup xmlns="ddi:logicalproduct:{namespace_version}" isUniversallyUnique="true" versionDate="2020-11-04T10:22:01.0748816Z">
      <r:URN>urn:ddi:uk.closer:{item_id}:1</r:URN>
      <r:Agency>uk.closer</r:Agency>
      <r:ID>{item_id}</r:ID>
      <r:Version>1</r:Version>
      <VariableGroupName>
      <r:String xml:lang="en-GB">{group_name}</r:String>
      </VariableGroupName>
      <r:Label>
      <r:Content xml:lang="en-GB">{group_label}</r:Content>
      </r:Label>
      <r:ConceptReference>
      <r:Agency>{concept_agency_id}</r:Agency>
      <r:ID>{concept_identifier}</r:ID>
      <r:Version>{concept_version}</r:Version>
      <r:TypeOfObject>Concept</r:TypeOfObject>
      </r:ConceptReference>
      </VariableGroup>
      </Fragment>""".replace("\n", "").replace("      ", "")
    return defusedxml.ElementTree.fromstring(fragmentString)

def get_group_label(topic_name, topic_type, C, language="en-GB"):
    """Retrieves the label for a topic/group by retrieving all instances of items with the topic name and
    choosing the label that is the most common for all those items (in case not all the items have the
    same labels).

    Arguments:
        topic_name (str): the name of the topic/group we want a label for.
        topic_type (uuid): the type of the topic/group (e.g. C.item_code('Variable Group')).
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Keyword arguments:
        language (str): the language the label is in.

    Returns:
        str: the label for the specified topic/group.
    """
    from collections import Counter
    groups_with_topic=C.search_items(topic_type, 
                                 SearchTerms=[topic_name], 
                                 SearchTargets=["Name"])
    group_label=Counter([x['Label'][language] for x in groups_with_topic['Results']]).most_common(1)[0][0]
    return group_label

def get_level_zero_group_for_topic(group, C, language="en-GB"):
    """Get the level zero group for a specified group.

    Arguments:
        group (dict): A dictionary representing the group for which we want to get the level zero group.
        C (ColecticaObject): an authenticated ColecticaObject instance.
    
    Keyword arguments:
        language (str): the language the topic name is in.
    
    Returns:
        ElementTree.Element: An ElementTree.Element representing the level zero group.
    """
    item_element=None
    topic_name=""
    if group['ItemName']!={}:
        if language in group['ItemName'].keys():
            topic_name = group['ItemName'][language]
        elif isinstance(group['ItemName'], str):
            topic_name = group['ItemName']   
        parent_group = C.search_relationship_byobject(group['AgencyId'], 
           group['Identifier'], Version=group['Version'], item_types=[group['ItemType']], Descriptions=True)
        if len(parent_group)==1:
            if len(topic_name)==3:
                level_zero_group = parent_group[0]
            elif len(topic_name)==5:
                level_zero_group = C.search_relationship_byobject(parent_group[0]['AgencyId'], 
                    parent_group[0]['Identifier'], Version=parent_group[0]['Version'], 
                    item_types=[C.item_code('Variable Group')], Descriptions=True)
                if len(level_zero_group)==1:    
                    item=C.get_item_xml(level_zero_group[0]['AgencyId'], level_zero_group[0]['Identifier'],
                    version=level_zero_group[0]['Version'])
                    item_element = defusedxml.ElementTree.fromstring(item['Item'])        
    return item_element

def create_group_lookup_dict(datasetToZeroGroupMappings, C):
    """Create a tuple thats used to map the datasets specified in datasetsToZeroGroupMappings to the 
    topic groups they contain.

    Arguments:
        datasetToZeroGroupMappings (dict): A dictionary mapping dataset names to level zero topic groups. 
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Returns:
        list: A list of tuples representing groups in datasets.
    """
    groupsInDatasets=[]
    count=0
    for dataset in datasetToZeroGroupMappings.keys():
        count=count+1
        print(f"Processing dataset {count} of {len(datasetToZeroGroupMappings.keys())}...")
        level_zero_group=datasetToZeroGroupMappings[dataset]
        dataset_agency=dataset.split(":")[2]
        dataset_identifier=dataset.split(":")[3]
        if len(level_zero_group)==1:
            varGroups=C.query_set(level_zero_group[0]['AgencyId'], level_zero_group[0]['Identifier'], 
                item_types=[C.item_code('Variable Group')])
            dataset_item=C.get_item_json(dataset_agency, dataset_identifier)
            # We iterate through varGroups, but exclude the level zero group...
            for varGroup in [group for group in varGroups if group['Item1']['Item1']!=level_zero_group[0]['Identifier']]:
                var_group_item=C.get_item_json(varGroup['Item1']['Item3'], varGroup['Item1']['Item1'], version=varGroup['Item1']['Item2'])
                groupsInDatasets.append({"DatasetName": dataset_item['DublinCoreMetadata']['AlternateTitle']['en-GB'],
                    "VariableGroupName": var_group_item['ItemName']['en-GB'],
                    "VariableGroupUrn": "urn:ddi:" + var_group_item['AgencyId'] + ":" + var_group_item['Identifier'] + ":" + str(var_group_item['Version']),
                    "TopicType": C.item_code('Variable Group')
                })
    return groupsInDatasets
