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

def references_are_equal(reference1, reference2):
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
    """Create an XML element representing a Variable/QuestionGroup"""
    type_of_object_element = ET.Element(f"{{ddi:reusable:{namespace_version}}}TypeOfObject")
    if topic_type==C.item_code('Variable Group'):
        new_element = ET.Element(f"{{ddi:datacollection:{namespace_version}}}VariableGroupReference")
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
    in-memory version which is stored in the updated_groups array."""
    #print("IN FUNC")
    #print(agency_id)
    #print(identifier)
    updated_referencing_item = [x for x in updated_groups if x['AgencyId'] == agency_id 
       and x['Identifier']==identifier]
    #print(updated_groups)   
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
    updated is not in already in the list, we append it to the list."""
    if ([x['Identifier'] for x in updated_groups_list].count(identifier) > 0):
        index_of_updated_ref = [x['Identifier'] for x in updated_groups_list].index(identifier)
        updated_groups_list[index_of_updated_ref] = {
            "Identifier": identifier,
            "AgencyId": agency,
            "Version": version,
            "ItemType": item_type,
            "Item": updated_group,
            "Dataset": dataset
        }
    else:
        updated_groups_list.append({
            "Identifier": identifier,
            "AgencyId": agency,
            "Version": version,
            "ItemType": item_type,
            "Item": updated_group,
            "Dataset": dataset
        })
 
def get_item_from_topic_name(topic_name, topic_type, containing_item, C, datasetToZeroGroupMappings={}):
    """Method for getting a topic item given the topic's name as a string (e.g. '11609'), the topic 
    type (e.g. Question Group, Variable Group), and the item within which that topic is contained 
    (e.g. a Physical Instance/Data File or a Data Collection object).

    Note that the item type input arguments must be provided as UUIDs (as specified at
    https://docs.colectica.com/repository/technical/item-type-identifiers/). Item types can be 
    mapped to their identifiers using the C.item_code function, e.g. C.item_code("Question Group"),
    C.item_code("Data Collection").
    """
    # We create a JSON object representing the containing item.
    topic_group_identifiers = C.search_items(topic_type,
                     SearchSets=containing_item,
                     SearchTerms=[str(topic_name)])['Results']
    if len(topic_group_identifiers)==0:
        print(containing_item)
        if not containing_item[0]['identifier'] in datasetToZeroGroupMappings.keys():
            datasetVars=C.query_set(containing_item[0]['agencyId'], containing_item[0]['identifier'],item_types=[C.item_code('Variable')])
            c=[]
            count=0
            for y in datasetVars:
                varGroups=C.search_relationship_byobject(y['Item1']['Item3'], y['Item1']['Item1'], 
                   Version=y['Item1']['Item2'], item_types=[topic_type]) 
                for varGroup in varGroups:
                    print(f"{count} of {len(datasetVars)}")
                    count=count+1
                    var_group_item=C.get_item_json(varGroup['Item1']['Item3'], varGroup['Item1']['Item1'], version=varGroup['Item1']['Item2'])
                    level_zero_group=get_level_zero_group(var_group_item, topic_type, C)
                    c.append(level_zero_group)
            if len(set([x[0][2].text for x in c]))==1:
                containing_level_zero_group = [{
                "agencyId": level_zero_group[0][1].text,
                "identifier": level_zero_group[0][2].text,
                "version": level_zero_group[0][3].text,
                }]
                datasetToZeroGroupMappings[containing_item[0]['identifier']]=containing_level_zero_group
            topic_group_identifiers = C.search_items(topic_type,
                     SearchSets=containing_level_zero_group,
                     SearchTerms=[str(topic_name)])['Results']
        else:
            containing_level_zero_group=datasetToZeroGroupMappings[containing_item[0]['identifier']]
            topic_group_identifiers = C.search_items(topic_type,
                     SearchSets=containing_level_zero_group,
                     SearchTerms=[str(topic_name)])['Results']            
    return topic_group_identifiers

def get_topic_for_item(agency_id, identifier, version, item_type, C):
    """This function gets the topic item(s) for an item (i.e. question/variable), given the
    question/variable's agency id, identifier, version, and the UUID code representing the topic's
    type (e.g. C.item_code("Variable Group")).
    """
    topics_assigned_to_item=[]
    related_groups = C.search_relationship_byobject(agency_id, identifier, Version=version, item_types=[item_type])
    for related_group in related_groups:
        related_question_group_most_recent_version=C.get_item_xml(related_group['Item1']['Item3'], related_group['Item1']['Item1'])
        if identifier in related_question_group_most_recent_version['Item']:
            topics_assigned_to_item.append(related_question_group_most_recent_version)
    return topics_assigned_to_item

def get_url_from_item(item, hostname):
   return f"http://{hostname}/item/{item['AgencyId']}/{item['Identifier']}/{str(item['Version'])}"

def get_urn_from_item(item):
   return f"urn:ddi:{item['AgencyId']}:{item['Identifier']}:{str(item['Version'])}"

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
 
def get_url_for_item(input_file_name, C):
    """When given a question/variable name and the name of the dataset/questionnaire object
    containing it, this function returns the URL where that item can be accessed on the 
    discovery portal."""
    data = pd.read_excel(input_file_name)
    for topic_reassignment_details in data.iloc:
        print("Performing the following topic reassignment...")
        # Search for the physical instance/dataset item which contains the variable in the current
        # input file row....
        #print(topic_reassignment_details)
        physical_instance_containing_variable = C.search_items(
            'a51e85bb-6259-4488-8df2-f08cb43485f8',
            SearchTerms=str(topic_reassignment_details.iloc[0]).strip(),
            SearchLatestVersion=True)['Results']
        #print(topic_reassignment_details.iloc[0])
        print(len(physical_instance_containing_variable))
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
            variables_metadata = C.search_items(C.item_code('Variable'), SearchSets=search_sets,
               SearchTerms=[str(topic_reassignment_details.iloc[2]).strip()])['Results']
            if len(variables_metadata) == 1:
                variable_agency_id = variables_metadata[0]['AgencyId']
                variable_identifier = variables_metadata[0]['Identifier']
                variable_version = variables_metadata[0]['Version']
                print(f"https://discovery.closer.ac.uk/item/{variable_agency_id}/{variable_identifier}/{variable_version}")

def create_input_file(input_file_name, C):
    """When given a question/variable name and the name of the dataset/questionnaire object
    containing it, this function returns the URL where that item can be accessed on the 
    discovery portal."""
    data = pd.read_excel(input_file_name).drop_duplicates()
    new_input_df = pd.DataFrame(columns=["Container", "ItemName", "URL", "Label", "CurrentTopic", "NewTopic"])
    newRow={}
    count=1
    for topic_reassignment_details in data.iloc:
        print(f"Count: {count}")
        count=count+1
        url=(get_url_for_item(C.item_code('Data File'), topic_reassignment_details.iloc[0], topic_reassignment_details.iloc[2], C))
        new_row={"Container": topic_reassignment_details.iloc[0],
                "ItemName": topic_reassignment_details.iloc[2],
                "URL": url,
                "Label": topic_reassignment_details.iloc[3],
                "CurrentTopic": topic_reassignment_details.iloc[4],
                "NewTopic": topic_reassignment_details.iloc[6]}
        if str(topic_reassignment_details.iloc[6])!='nan':        
            new_input_df.loc[len(new_input_df)] = new_row
    new_input_df.to_excel('test.xlsx', index=False)

def get_url_for_item(container_type, container_name, item_name, C):
        """When given a question/variable name and the name of the dataset/questionnaire object
        containing it, this function returns the URL where that item can be accessed on the 
        discovery portal."""
        print("Performing the following topic reassignment...")
        # Search for the physical instance/dataset item which contains the variable in the current
        # input file row....
        print(topic_reassignment_details)
        physical_instance_containing_variable = C.search_items(
            container_type,
            SearchTerms=str(container_name).strip(),
            SearchLatestVersion=True)['Results']
        #print(topic_reassignment_details.iloc[0])
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
            variables_metadata = C.search_items(C.item_code('Variable'), SearchSets=search_sets,
               SearchTerms=[str(item_name).strip()])['Results']
            if len(variables_metadata) == 1:
                variable_agency_id = variables_metadata[0]['AgencyId']
                variable_identifier = variables_metadata[0]['Identifier']
                variable_version = variables_metadata[0]['Version']
                return(f"https://discovery.closer.ac.uk/item/{variable_agency_id}/{variable_identifier}/{variable_version}")

def create_group(group_name, 
group_label, 
item_id, 
namespace, 
concept_agency_id, 
concept_identifier, 
concept_version):
   fragmentString = f"""<Fragment xmlns:r="ddi:reusable:{namespace}" xmlns="ddi:instance:{namespace}">
      <VariableGroup xmlns="ddi:logicalproduct:{namespace}" isUniversallyUnique="true" versionDate="2020-11-04T10:22:01.0748816Z">
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

def get_group_label(topic_name, topic_type, C):
    groups_with_topic=C.search_items(topic_type, 
                                 SearchTerms=[topic_name], 
                                 SearchTargets=["Name"])
    group_label=Counter([x['Label'][language] for x in groups_with_topic['Results']]).most_common(1)[0][0]
    return group_label

def get_level_zero_group(group, item_type, C):
    if group['ItemName']!={}:
        if language in group['ItemName'].keys():
            topic_name = group['ItemName'][language]
        if isinstance(group['ItemName'], str):
            topic_name = group['ItemName']
        parent_group = C.search_relationship_byobject(group['AgencyId'], 
           group['Identifier'], Version=group['Version'], item_types=[item_type])[0]  
        if len(topic_name)==3:
            level_zero_group = parent_group
        elif len(topic_name)==5:
            level_zero_group = C.search_relationship_byobject(parent_group['Item1']['Item3'], 
               parent_group['Item1']['Item1'], Version=parent_group['Item1']['Item2'], 
               item_types=[item_type])[0]
        item=C.get_item_xml(level_zero_group['Item1']['Item3'], level_zero_group['Item1']['Item1'],
           version=level_zero_group['Item1']['Item2'])
        item_element = defusedxml.ElementTree.fromstring(item['Item'])    
    return item_element

def get_level_zero_group_2(agencyId, identifier, version, item_type, C):
    level_zero_group = C.search_relationship_byobject(agencyId, identifier, Version=version, 
               item_types=[item_type])[0] 
    level_zero_group_item=C.get_item_xml(level_zero_group['Item1']['Item3'], level_zero_group['Item1']['Item1'],
           version=level_zero_group['Item1']['Item2'])           
    item_element = defusedxml.ElementTree.fromstring(level_zero_group_item['Item'])
    return item_element


def create_group_lookup_dict(C):
    allLevelZeroes=C.search_relationship_bysubject(
              'uk.closer', 
              '5c669cb3-a633-4324-93fb-ed2695b44072', 
              item_types=[C.item_code('Variable Group')])       
    groupsWithoutDatasets=[]
    groupsWithDatasets=[]
    groupsWithoutDatasetsVarsInMultiple=[]
    groupsWithoutDatasetsVarsInNone=[]
    groupsInDatasets=[]
    count=0
    investigateThese=[]
    for x in allLevelZeroes:
        print(count)
        count=count+1
        dataset=C.query_set(x['Item1']['Item3'], x['Item1']['Item1'],item_types=[C.item_code('Data File')], reverseTraversal=True)
        varGroups=C.query_set(x['Item1']['Item3'], x['Item1']['Item1'],item_types=[C.item_code('Variable Group')])
        if len(dataset)==0:
            datasetVars=C.query_set(x['Item1']['Item3'], x['Item1']['Item1'],item_types=[C.item_code('Variable')])
            c=[]
            for y in datasetVars:
                b=C.query_set(y['Item1']['Item3'], y['Item1']['Item1'],item_types=[C.item_code('Data File')], reverseTraversal=True)
                for z in b:
                    c.append(z['Item1']['Item3'] + ":" + z['Item1']['Item1'] + ":" + str(z['Item1']['Item2']))
            if len(set(c))==1:
               #groupsWithoutDatasets.append(c[0])
               print("STEP1")
               dataset_item=C.get_item_json(z['Item1']['Item3'], z['Item1']['Item1'], version=z['Item1']['Item2'])
               print("STEP2")
               for varGroup in varGroups[1:]:
                   var_group_item=C.get_item_json(varGroup['Item1']['Item3'], varGroup['Item1']['Item1'], version=varGroup['Item1']['Item2'])
                   groupsInDatasets.append((dataset_item['DublinCoreMetadata']['AlternateTitle']['en-GB'], var_group_item['ItemName']['en-GB'], 
                        var_group_item['Identifier']+ ":" + var_group_item['AgencyId'] + ":" + str(var_group_item['Version']), x))
            else:
                investigateThese.append(x) 
        else:
            dataset_item=C.get_item_json(dataset[0]['Item1']['Item3'], dataset[0]['Item1']['Item1'], version=dataset[0]['Item1']['Item2'])
            for varGroup in varGroups[1:]:
                 var_group_item=C.get_item_json(varGroup['Item1']['Item3'], varGroup['Item1']['Item1'], version=varGroup['Item1']['Item2'])
                 groupsInDatasets.append((dataset_item['DublinCoreMetadata']['AlternateTitle']['en-GB'], var_group_item['ItemName']['en-GB'], 
                    var_group_item['Identifier']+ ":" + var_group_item['AgencyId'] + ":" + str(var_group_item['Version'])))
        return groupsInDatasets




 #  print(fragmentString)
 #  transactionResponse = C.create_transaction()
 #  print(transactionResponse)
 #  transactionId w= transactionResponse['TransactionId']
 #  print("TRANSACTION ID: ")
 #  print(transactionId)
   #addItemToTransaction('uk.closer', item_id, 1, transactionId, fragmentString, C.item_code('Variable Group'))
 #  C.add_items_to_transaction('uk.closer', item_id, 1,fragmentString, C.item_code('Variable Group'), transactionId)
 #  C.commit_transaction(transactionId, "Create beliefs topic", 3)
 