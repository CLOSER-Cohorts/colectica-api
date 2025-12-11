"""
A set of functions that reassign items to new topics. The item topic reassignments
are defined in an Excel spreadsheet, the name of which is passed as an input argument to a
function. An example of this spreadsheet ('topic_reassignments.xlsx') is provided in the
'examples' directory of this repository. The set of commands that need to be executed from
within a Python shell for changing item topics is:

from colectica_api import ColecticaObject
from examples.lib.utility import update_repository
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)
import examples.change_item_topics

validationResults=examples.change_item_topics.move_topics(C)


datasetToZeroGroupMappings={}
topics_to_create=examples.change_item_topics.find_topics_to_create('../test.xlsx', C, datasetToZeroGroupMappings=datasetToZeroGroupMappings)
items_with_new_level_one_topics=examples.change_item_topics.create_ddi_objects_for_new_level_one_topics(topics_to_create, C)
items_with_modified_level_one_topics=examples.change_item_topics.create_ddi_objects_for_modified_level_one_topics(topics_to_create[2], C)
a1=examples.change_item_topics.validateLevelTwoTopics(items_with_new_level_one_topics[0], items_with_new_level_one_topics[1], items_with_new_level_one_topics[2])
b1=examples.change_item_topics.validateLevelOneTopics(items_with_new_level_one_topics[0], items_with_new_level_one_topics[1])
a1=examples.change_item_topics.validateLevelTwoTopics(items_with_modified_level_one_topics[0], items_with_modified_level_one_topics[1], items_with_modified_level_one_topics[2])
b1=validateLevelOneTopics(items_with_modified_level_one_topics[0], items_with_modified_level_one_topics[1])


updated_groups = examples.change_item_topics.update_topics('examples/topic_reassignments.xlsx', C)
examples.lib.utility.update_repository(updated_groups, 'Repository commit message - update topics', C)
"""
from examples.lib.utility import (
    get_namespace,
    find_all_references,
    create_variable_reference,
    create_question_reference,
    update_list_of_topic_groups,
    get_urn_from_item,
    get_item_from_topic_name,
    create_variable_group,
    create_group_reference,
    create_group_lookup_dict,
    get_current_state_of_topic_group,
    get_level_zero_group_for_topic,
    get_group_label,
    get_elements_of_type,
    get_element_by_name,
    get_element_fragment_by_name,
    get_urn_from_fragment  
)
import defusedxml
#pip install openpyxl #might need to install openpyxl, a dependency for read-excel
import pandas as pd
import uuid
from collections import Counter

language = "en-GB"

def move_topics(input_file, C):
    datasetToZeroGroupMappings={}
    groupsInDatasets=create_group_lookup_dict(datasetToZeroGroupMappings, C)
    topics_to_create=find_topics_to_create(input_file, 
        C, 
        datasetToZeroGroupMappings=datasetToZeroGroupMappings,
        groupsInDatasets=groupsInDatasets)
    items_with_new_level_one_topics=create_ddi_objects_for_new_level_one_topics(
        topics_to_create['levelOneGroupsToCreate'], topics_to_create['levelTwoGroupsToCreate'], C)
    items_with_modified_level_one_topics=create_ddi_objects_for_modified_level_one_topics(
        topics_to_create["levelOneGroupsToModify"], C)
    print("""Validating the DDI objects that have been created for the new level two topics that needed 
    to be created, and for which level one topics also need to be created...""")    
    validationResultsNewLevelTwoTopics=validateLevelTwoTopics(items_with_new_level_one_topics["LevelZero"], 
        items_with_new_level_one_topics["LevelOne"], 
        items_with_new_level_one_topics["LevelTwo"],
        C)
    print("""Validating the DDI objects that have been created for the new level one topics that needed 
    to be created...""")    
    validationResultsNewLevelOneTopics=validateLevelOneTopics(items_with_new_level_one_topics["LevelZero"], 
        items_with_new_level_one_topics["LevelOne"],
        C)
    print("""Validating the DDI objects that have been created for the new level two topics that needed 
    to be created, but for which level one topics already existed...""")    
    validationResultsNewLevelTwoTopicsWithModifiedLevelOneTopics=validateLevelTwoTopics(items_with_modified_level_one_topics["LevelZero"], 
        items_with_modified_level_one_topics["LevelOne"], 
        items_with_modified_level_one_topics["LevelTwo"],
        C)
    print("""Validating the DDI objects that have been created for the existing level one topics that needed 
    to be modified to include references to new level two topics...""")    
    validationResultsModifiedLevelOneTopics=validateLevelOneTopics(items_with_modified_level_one_topics["LevelZero"], 
        items_with_modified_level_one_topics["LevelOne"],
        C)
    """
    In summary, the below tests verify the following:
    1. If we're creating a topic, it doesn't already exist. If we're modifying a topic,
    it does already exist.
    2+3. We're creating/modifying all the topics we need to; we're not missing anything
    """    
    # 1. We need to verify that all the groups in topics_to_create[0 and 1] do not currently exist.
    for topic_to_create in topics_to_create["levelOneGroupsToCreate"]:
        if len([(existing_group['DatasetName'], existing_group['VariableGroupName']) 
            for existing_group in groupsInDatasets 
            if existing_group['DatasetName']==topic_to_create['DatasetName'] 
            and existing_group['VariableGroupName']==topic_to_create['LevelOneGroupName']])!=0:
                print("ERROR - LEVEL ONE TOPIC LISTED FOR CREATION ALREADY EXISTS")
    for topic_to_create in topics_to_create["levelTwoGroupsToCreate"]:
        if len([(existing_group['DatasetName'], existing_group['VariableGroupName']) 
            for existing_group in groupsInDatasets 
            if existing_group['DatasetName']==topic_to_create['DatasetName'] 
            and existing_group['VariableGroupName']==topic_to_create['LevelTwoGroupName']])!=0:
                print(topic_to_create)
                print("ERROR - LEVEL TWO TOPIC LISTED FOR CREATION ALREADY EXISTS") 
    # We also need to check that the level one topics in topics_to_create[2] do exist, and 
    # that the level two topics they refer to do not exist.
    for topic_to_create in topics_to_create["levelOneGroupsToModify"]:
        if len([(existing_group['DatasetName'], existing_group['VariableGroupName']) 
            for existing_group in groupsInDatasets 
            if existing_group['VariableGroupName']==topic_to_create['LevelTwoGroupName'][0:3] 
            and existing_group['DatasetName']==topic_to_create['DatasetName']])==0:
                print(topic_to_create)
                print("ERROR - LEVEL ONE TOPIC LISTED FOR MODIFICATION DOES NOT EXIST")
        if len([(existing_group['VariableGroupName'], existing_group['VariableGroupName']) 
            for existing_group in groupsInDatasets 
            if existing_group['VariableGroupName']==topic_to_create['LevelTwoGroupName'] 
            and existing_group['DatasetName']==topic_to_create['DatasetName']])!=0:
                print(topic_to_create)
                print("ERROR - LEVEL TWO TOPIC LISTED FOR CREATION ALREADY EXISTS")
    # 2. We need to verify that the set of groups in items_with_new_level_one_topics is the same as in
    # topics_to_create["LevelOneGroupsToCreate"].
    sortedLevelOneGroupsInTopicsToCreate=sorted(list(set([(topic_to_create['DatasetName'], topic_to_create['LevelOneGroupName']) 
        for topic_to_create in topics_to_create["levelOneGroupsToCreate"]])))
    sortedDdiItemsForNewLevelOneTopics=sorted(list(set([(data_for_creating_new_topic['DatasetName'], 
        get_element_by_name(data_for_creating_new_topic['Item'], 'VariableGroupName')['String']) 
        for data_for_creating_new_topic in items_with_new_level_one_topics["LevelOne"]])))
    if sortedLevelOneGroupsInTopicsToCreate==sortedDdiItemsForNewLevelOneTopics:
        print("We have successfully created all necessary DDI items for the new level one topics.")
    else:
        print("Error: we have not created all necessary DDI items for the new level one topics.")
    # 3. We need to verify that the total set of groups in items_with_new_level_one_topics['LevelTwo'] and 
    # items_with_modified_level_one_topics['LevelTwo'] is the same as in topics_to_create['LevelTwoGroupsToCreate'].
    sortedLevelTwoGroupsInTopicsToCreate==sorted(list(set([(topic_to_create['DatasetName'], topic_to_create['LevelTwoGroupName']) 
        for topic_to_create in topics_to_create["levelTwoGroupsToCreate"]])))
    sortedDdiItemsForNewLevelTwoTopics=sorted(list(set([(data_for_creating_new_topic['DatasetName'], 
        get_element_by_name(data_for_creating_new_topic['Item'], 'VariableGroupName')['String']) 
        for data_for_creating_new_topic in items_with_new_level_one_topics["LevelTwo"]])))
    sortedDdiItemsForNewLevelTwoTopicsWithExistingLevelOneTopics=sorted(list(set([(data_for_creating_new_topic['DatasetName'], 
        get_element_by_name(data_for_creating_new_topic['Item'], 'VariableGroupName')['String']) 
        for data_for_creating_new_topic in items_with_modified_level_one_topics["LevelTwo"]])))
    if sortedLevelTwoGroupsInTopicsToCreate==sorted(sortedDdiItemsForNewLevelTwoTopicsWithoutExistingLevelOneTopics+
        sortedDdiItemsForNewLevelTwoTopicsWithExistingLevelOneTopics):
        print("We have successfully created all necessary DDI items for the new level two topics.")
    else:
        print("Error: we have not created all necessary DDI items for the new level two topics.")
    # We need to verify that the set of level one groups in items_with_modified_level_one_topics is the same
    # as in topics_to_create['levelOneGroupsToModify']
    sortedLevelOneGroupsInTopicsToModify=sorted(list(set([(x['DatasetName'], x['Item']['ItemName']['en-GB']) 
        for x in topics_to_create['levelOneGroupsToModify']])))
    sortedDdiItemsForModifiedLevelOneTopics=sorted(list(set([(x['DatasetName'], get_element_by_name(x['Item'], 'VariableGroupName')['String'])
        for x in items_with_modified_level_one_topics["LevelOne"]])))
    if sortedLevelOneGroupsInTopicsToModify==sortedDdiItemsForModifiedLevelOneTopics:
        print("We have successfully created all necessary DDI items for the modified level one topics.")
    else:
        print("Error: we have not created all necessary DDI items for the modified level one topics.")
    # Create an array which contains the new/modified topic groups...
    updated_topic_groups=[]
    for x in items_with_new_level_one_topics["LevelZero"] + items_with_new_level_one_topics["LevelOne"] + \
        items_with_new_level_one_topics["LevelTwo"] + items_with_modified_level_one_topics["LevelZero"] + \
        items_with_modified_level_one_topics["LevelOne"] + items_with_modified_level_one_topics["LevelTwo"]:
        item_agency_id = x['Item'][0][0].text.split(":")[2]
        item_identifier = x['Item'][0][0].text.split(":")[3]
        item_version = x['Item'][0][0].text.split(":")[4]            
        update_list_of_topic_groups(x['Item'],
            item_agency_id,
            item_identifier,
            item_version,            
            C.item_code('Variable Group'),
            updated_topic_groups,
            dataset=x['DatasetName'])
    # Now that we have verified that the topics to create/modify are correct, we can proceed to
    # creating the urn dataframe which specifies which items should be moved to which topics
    topic_reassignments_data_frame=generate_urn_dataframe_for_questions_and_variables('../test.xlsx', 
      C, updated_topic_groups, 0, datasetToZeroGroupMappings=datasetToZeroGroupMappings, 
      groupsInDatasets=groupsInDatasets)
    # Run the update_topics method that creates DDI objects that reassigns items to topics. Note that it uses
    # the updated_topic_groups array as an input argument, this array contains the DDI items representing topics
    updated_topics=update_topics(topic_reassignments_data_frame, C, updated_topic_groups=updated_topic_groups)
    final_validation_results=validate_ddi_implementing_topic_reassignments('../test.xlsx', updated_topic_groups, C)
    return final_validation_results

def update_urns_list(urns, 
    item, 
    containing_item,
    topic_type,
    target_topic, 
    topic_groups,
    C, 
    groupsInDatasets=[], 
    datasetToZeroGroupMappings={}, 
    dataset_name=""):
    """Updates a dictionary containing lists of URNs used for topic reassignment.

    Arguments: urns (dict): A dictionary containing lists of URNs used for topic reassignment.
        item (dict): A dictionary containing details of the item being reassigned to a new topic.
        containing_item (dict): A dictionary containing details of the item containing the item being 
            reassigned.
        topic_type (str): The item type code for the topic groups (e.g. variable group or question group).
        target_topic (str): The name of the destination topic group.
        topic_groups (str): A list of DDI items that are the groups representing topics that we
            are updating (e.g. by adding/removing references to variables/questions, in order to reassign
            these items to new topics).
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Keyword arguments:
        groupsInDatasets: A list of dict objects that map the datasets to topic groups they contain.
        datasetToZeroGroupMappings (dict): A dictionary mapping dataset names to level zero topic groups.
        dataset_name (str): The name of the dataset containing the item being reassigned.

    Returns:
        None: The function updates the urns dictionary in place.
    """
    destination_topic_urn=""
    containing_item_details = {"AgencyId": containing_item['AgencyId'],
                      "Identifier": containing_item['Identifier'],
                      "Version": containing_item['Version'],
                }
    item_urn = get_urn_from_item(item)
    source_groups = C.search_relationship_byobject(item['AgencyId'], 
                   item['Identifier'], Version=item['Version'], 
                   item_types=topic_type, Descriptions=True)
    for source_group in source_groups:
        source_topic_urn = get_urn_from_item(source_group)
    if len(source_groups)==0:
        source_topic_urn = ""
    destination_group=get_item_from_topic_name(str(target_topic), 
            topic_type, 
            containing_item_details, 
            C,
            dataset_name=dataset_name,
            groupsInDatasets=groupsInDatasets,
            datasetToZeroGroupMappings=datasetToZeroGroupMappings)
    if len(destination_group)==1:
            destination_topic_urn = get_urn_from_item(destination_group[0])
    elif topic_type==C.item_code('Variable Group'):
            # the topic groups all exist for questions which is why we only do the below for variable groups
            destination_group_details=[x for x in topic_groups if x['DatasetName']==dataset_name 
                and get_elements_of_type(x['Item'], "VariableGroupName")!=[]
                and get_elements_of_type(x['Item'], "VariableGroupName")[0][0].text==str(target_topic)]
            if len(destination_group_details)==1:
                destination_topic_urn=get_urn_from_fragment(destination_group_details[0]['Item'])   
    if item_urn not in urns['itemUrns'] and destination_topic_urn != "" and source_topic_urn != destination_topic_urn:
            urns['itemUrns'].append(item_urn)
            urns['sourceTopicGroups'].append(source_topic_urn)
            urns['destinationTopicGroups'].append(destination_topic_urn)
            urns['datasets'].append(dataset_name)  

def generate_urn_dataframe_for_questions_and_variables(input_file_name, 
    topic_groups,
    C, 
    groupsInDatasets=[],
    datasetToZeroGroupMappings={}):  
    """Generates a dataframe containing URNs used for topic reassignment.

    Arguments:
        input_file_name (str): the name of the Excel spreadsheet containing details of topic reassignments.
        topic_groups (str): A list of DDI items that are the groups representing topics that we
            are updating (e.g. by adding/removing references to variables/questions, in order to reassign
            these items to new topics).
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Keyword arguments:
        groupsInDatasets: Create a list of dict objects that map the datasets to topic groups they contain.
        datasetToZeroGroupMappings (dict): a dictionary mapping dataset names to level zero topic groups.

    Returns:
        pd.DataFrame: A dataframe containing URNs used for topic reassignment.
    """
    print(f"Reading topic reassignments from {input_file_name}")
    data = pd.read_excel(input_file_name)
    urns={
        "itemUrns": [],
        "sourceTopicGroups": [],
        "destinationTopicGroups": [],
        "datasets": []
    }
    count=1
    # Iterate through the rows in the spreadsheet. Each row contains details of a topic
    # reassignment for an item...
    print("Creating dataframe containing URNs used for topic reassignment...")
    for topic_reassignment_details in data.iloc: 
        print(f"Creating dataframe row {count} of {data.shape[0]}...")
        count+=1
        topic_dict = create_topic_reassignment_dict(topic_reassignment_details, C)
        physical_instance_containing_variable = C.search_items(
                    C.item_code('Data File'),
                    SearchTerms=str(topic_dict['dataset_name']).strip(),
                    SearchLatestVersion=True)['Results']
        if len(physical_instance_containing_variable)==1:
            update_urns_list(urns, topic_dict['item'], physical_instance_containing_variable[0],
               C.item_code('Variable Group'), topic_dict['destination_topic_name'],
               topic_groups, C, datasetToZeroGroupMappings=datasetToZeroGroupMappings,
               groupsInDatasets=groupsInDatasets,
               dataset_name=topic_dict['dataset_name'])       
        allRelatedQuestions= C.search_relationship_bysubject(topic_dict['item']['AgencyId'], 
            topic_dict['item']['Identifier'], 
            Version=topic_dict['item']['Version'], item_types=C.item_code("Question"), Descriptions=True)
        for relatedQuestion in allRelatedQuestions:
            question_sets=C.query_set(relatedQuestion['AgencyId'], 
               relatedQuestion['Identifier'], 
               version=relatedQuestion['Version'], 
               reverseTraversal=True, 
               item_types=[C.item_code('Data Collection')])
            if len(question_sets)>0 and len(set([(x['Item1']['Item3'], x['Item1']['Item1']) for x in question_sets] ))==1:
                latest_version_of_question_set = max([x['Item1']['Item2'] for x in question_sets])
                containing_item=C.get_item_xml(question_sets[0]['Item1']['Item3'], 
                    question_sets[0]['Item1']['Item1'],
                    version=latest_version_of_question_set)
                update_urns_list(urns, relatedQuestion, containing_item, 
                    C.item_code('Question Group'), 
                    topic_dict['destination_topic_name'], 
                    topic_groups,
                    C,
                    groupsInDatasets=groupsInDatasets,
                    dataset_name=topic_dict['dataset_name'],
                    datasetToZeroGroupMappings=datasetToZeroGroupMappings)           
    return (pd.DataFrame(urns))

def get_level_zero_group_from_dataset(physical_instance_containing_variable, all_variable_groups, C):
    """Gets the level zero topic group for a dataset.

    Arguments:
        physical_instance_containing_variable (dict): A dictionary containing details of a 
            physical instance.
        all_variable_groups (list): A list of all variable groups in the repository.
        C (ColecticaObject): an authenticated ColecticaObject instance.
    Returns:
        ElementTree.Element: An ElementTree.Element representing the level zero topic group.
    """
    level_zero_group_details=C.search_relationship_byobject(
              physical_instance_containing_variable['AgencyId'], 
              physical_instance_containing_variable['Identifier'], 
              Version=physical_instance_containing_variable['Version'], 
              item_types=[C.item_code('Variable Group')])
    level_zero_group_item=None
    if len(level_zero_group_details)==0:
               level_zero_group_details=[x for x in all_variable_groups if x['Label']['en-GB']==
                   physical_instance_containing_variable['Label']['en-GB']]
               if len(level_zero_group_details)==1:
                   level_zero_group_item=C.get_item_xml(level_zero_group_details[0]['AgencyId'],
                     level_zero_group_details[0]['Identifier'],
                     version=level_zero_group_details[0]['Version'])['Item']     
               else:
                   print("CANNOT FIND LEVEL ZERO GROUP")      
    else:
               level_zero_group_item=C.get_item_xml(level_zero_group_details[0]['Item1']['Item3'],
                 level_zero_group_details[0]['Item1']['Item1'],
                 version=level_zero_group_details[0]['Item1']['Item2'])['Item']
    if level_zero_group_item is None:
        return None
    else:
        return(defusedxml.ElementTree.fromstring(level_zero_group_item))   
           
def create_topic_reassignment_dict(topic_reassignment_details, C):
    """Creates a dictionary containing details of a topic reassignment, for convenient
    reuse later in the code and to avoid code in multiple places which re-parses the same details.

    Arguments: 
        topic_reassignment_details (pd.Series): A pandas Series containing details of a topic reassignment.
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Returns:
        dict: A dictionary containing details of a topic reassignment.
    """
    topic_reassignment_dict={}
    dataset_name = topic_reassignment_details.iloc[0]
    topic_reassignment_dict['dataset_name']=dataset_name    
    url = topic_reassignment_details.iloc[2]
    topic_reassignment_dict['source_topic_name'] = str(topic_reassignment_details.iloc[4])
    topic_reassignment_dict['destination_topic_name'] = str(topic_reassignment_details.iloc[5])
    agency_id = url.split("/")[4]
    identifier = url.split("/")[5]
    item = C.get_item_xml(agency_id, identifier)
    item_element = defusedxml.ElementTree.fromstring(item['Item'])
    topic_reassignment_dict['namespace_version'] = get_namespace(item_element.tag).split(':')[2]
    topic_reassignment_dict['item'] = item        
    physical_instance_containing_variable = C.search_items(
                    C.item_code('Data File'),
                    SearchTerms=str(dataset_name).strip(),
                    SearchLatestVersion=True,
                    UsePrefixSearch=True )['Results']
    if len(physical_instance_containing_variable)==1:
        topic_reassignment_dict['physical_instance_containing_variable'] = physical_instance_containing_variable[0]
        topic_reassignment_dict['physical_instance_search_set'] = {
                "AgencyId": physical_instance_containing_variable[0]['AgencyId'],
                "Identifier": physical_instance_containing_variable[0]['Identifier'],
                "Version": physical_instance_containing_variable[0]['Version']
            }
    else:
        topic_reassignment_dict['physical_instance_search_set'] = None
    return topic_reassignment_dict    
                   
def find_topics_to_create(input_file_name, C, datasetToZeroGroupMappings={}, groupsInDatasets=[]):
    """This code iterates through an Excel input file containing details of new item topic 
    assignments, and finds variable groups representing topics that don't already exist and 
    will need to be created in order to perform the topic reassignments.

    Arguments:
        input_file_name (str): the name of the Excel spreadsheet containing details of new 
        item topic assignments.
        C (ColecticaObject): an authenticated ColecticaObject instance.

    Keyword arguments:
        datasetToZeroGroupMappings (dict): a dictionary mapping dataset names to level zero 
        topic groups.
        groupsInDatasets: A list of dict objects that map the datasets to topic groups they contain.
        
    Returns:
        dict: A dictionary containing three lists of objects: 
            1. The level one groups that need to be created because a level two group is being created 
               that requires it (e.g. if we are creating a level two group in a dataset representing the
               10320 topic, but the 103 topic is not already present in that dataset).
            2. The level two groups that need to be created.
            3. The level one groups that need to be modified because a level two group is being created 
               in a dataset where the associated level one group already exists (e.g. if we are creating 
               a level two group in a dataset representing the 10320 topic, and the 103 topic already 
               exists in that dataset).
    """
    print(f"Reading topic reassignments from {input_file_name}")
    data = pd.read_excel(input_file_name)
    levelOneGroupsToCreate=[]
    levelOneGroupsToModify=[]
    levelTwoGroupsToCreate=[]
    all_variable_groups=C.search_items(C.item_code('Variable Group'), SearchLatestVersion=True)['Results']
    count=0
    for topic_reassignment_details in data.iloc:
        topic_dict = create_topic_reassignment_dict(topic_reassignment_details, C)
        topic_type=C.item_code('Variable Group')
        print(topic_dict['physical_instance_containing_variable'])
        level_zero_group=get_level_zero_group_from_dataset(topic_dict['physical_instance_containing_variable'],
                all_variable_groups, C)
        destination_topic = get_item_from_topic_name(topic_dict['destination_topic_name'], 
            topic_type, 
            topic_dict['physical_instance_search_set'], C, 
            groupsInDatasets=groupsInDatasets,
            dataset_name=topic_dict['dataset_name'], datasetToZeroGroupMappings=datasetToZeroGroupMappings)
        if len(destination_topic)==0:
                level_one_group_name = str(topic_dict['destination_topic_name'])[0:3]
                if len(topic_dict['destination_topic_name'])==5:
                       level_two_group_name = str(topic_dict['destination_topic_name'])
                       if ((topic_dict['dataset_name'], topic_dict['destination_topic_name']) 
                            not in [(x['DatasetName'], x['LevelTwoGroupName']) for x in levelTwoGroupsToCreate]):
                                levelTwoGroupsToCreate.append({'DatasetName': topic_dict['dataset_name'], 
                                    'LevelTwoGroupName': topic_dict['destination_topic_name'], 
                                    'NamespaceVersion': topic_dict['namespace_version']})                   
                levelOneGroups=get_item_from_topic_name(level_one_group_name, 
                    topic_type, 
                    topic_dict['physical_instance_search_set'], 
                    C,
                    dataset_name=topic_dict['dataset_name'],
                    groupsInDatasets=groupsInDatasets, 
                    datasetToZeroGroupMappings=datasetToZeroGroupMappings)
                if len(levelOneGroups)==0:
                    print(levelOneGroupsToCreate)
                    if ((topic_dict['dataset_name'], level_one_group_name) not in 
                        [(x['DatasetName'], x['LevelOneGroupName']) for x in levelOneGroupsToCreate]):
                          levelOneGroupsToCreate.append({'DatasetName': topic_dict['dataset_name'], 
                        'LevelOneGroupName': level_one_group_name, 
                        'LevelZeroGroup': level_zero_group, 
                        'NamespaceVersion': topic_dict['namespace_version']})       
                else:
                    if ((topic_dict['dataset_name'], level_two_group_name) not in 
                          [(x['DatasetName'], x['LevelTwoGroupName']) for x in levelOneGroupsToModify]):
                              for group in levelOneGroups:
                                 levelOneGroupsToModify.append({
                                              'DatasetName': topic_dict['dataset_name'],
                                              'LevelTwoGroupName': level_two_group_name, 
                                              'NamespaceVersion': topic_dict['namespace_version'],
                                              'Item': group
                                              }) 
    return ({"levelOneGroupsToCreate": levelOneGroupsToCreate, 
        "levelTwoGroupsToCreate": levelTwoGroupsToCreate, 
        "levelOneGroupsToModify": levelOneGroupsToModify})

def create_ddi_objects_for_new_level_one_topics(level_one_groups_to_create, level_two_groups_to_create, C):
   """Creates ddi objects that represent variable groups which are level one topics.

   Arguments:
        level_one_groups_to_create: the level one groups that need to be created either because an item is being 
               reassigned to a level one topic group that does not yet exist, or because a level 
               two group is being created that requires it (e.g. if we are creating a level two 
               group in a dataset representing the 10320 topic, but the 103 topic is not already 
               present in that dataset).
        level_two_groups_to_create: the level two groups that need to be created
        C (ColecticaObject): an authenticated ColecticaObject instance.
   
   Returns:
        dict: A dictionary containing three lists of objects: 
            1. Objects containing information about the DDI level zero topic groups that have 
               been modified to include references to the new level one groups.
            2. Objects containing information about the DDI level one topic groups that have been 
            created.
            3. Objects containing information about the DDI level two topic groups that have been 
            created.
   """  
   allConcepts=C.search_items(C.item_code('Concept'))['Results']
   # get rid of concepts that don't properly define an itemname
   concepts=[x for x in allConcepts if list(x['ItemName'].keys())==['en-GB']]
   ddiObjectsLevelZero = []
   ddiObjectsLevelOne = []
   ddiObjectsLevelTwo = []
   for level_one_group_to_create in level_one_groups_to_create:
      level_one_group_uuid=str(uuid.uuid4())
      level_one_group_name=level_one_group_to_create['LevelOneGroupName']
      topic_type=C.item_code('Variable Group')
      namespace_version=level_one_group_to_create['NamespaceVersion']  
      level_zero_group_urn=level_one_group_to_create['LevelZeroGroup'][0][0].text
      zero_group_agency_id = level_zero_group_urn.split(":")[2]
      zero_group_identifier = level_zero_group_urn.split(":")[3]
      zero_group_version = level_zero_group_urn.split(":")[4]
      level_zero_group_object = get_current_state_of_topic_group(zero_group_agency_id, 
          zero_group_identifier, ddiObjectsLevelZero, C, version=zero_group_version)   
      level_one_group_label=get_group_label(level_one_group_name, topic_type, C)
      levelOneConcept=[x for x in concepts if x['ItemName']['en-GB']==level_one_group_name]
      if len(levelOneConcept)==1:
        level_one_group_object = create_variable_group(level_one_group_name, 
            level_one_group_label, 
            level_one_group_uuid, 
            namespace_version,
            levelOneConcept[0]['AgencyId'], 
            levelOneConcept[0]['Identifier'], 
            levelOneConcept[0]['Version'])
        level_one_group_reference=create_group_reference('uk.closer', 
            level_one_group_uuid, 1, namespace_version, topic_type, C)
        get_element_fragment_by_name(level_zero_group_object, "VariableGroup").append(level_one_group_reference)
        update_list_of_topic_groups(level_zero_group_object,
                               zero_group_agency_id,
                               zero_group_identifier,
                               zero_group_version,
                               topic_type,
                               ddiObjectsLevelZero,
                               dataset=level_one_group_to_create['DatasetName'])                           
        level_two_groups=[x for x in level_two_groups_to_create 
                if x['DatasetName']==level_one_group_to_create['DatasetName'] and x['LevelTwoGroupName'][0:3]==level_one_group_to_create['LevelOneGroupName']]
        for level_two_group in level_two_groups:
            level_two_group_uuid=str(uuid.uuid4())
            level_two_group_name=level_two_group['LevelTwoGroupName']
            level_two_group_label=get_group_label(level_two_group_name, 
                topic_type, C)
            levelTwoConcept=[x for x in concepts if x['ItemName']['en-GB']==level_two_group_name]
            if len(levelTwoConcept)==1:
                level_two_group_object=create_variable_group(level_two_group_name, 
                    level_two_group_label, level_two_group_uuid, namespace_version,
                    levelTwoConcept[0]['AgencyId'], 
                    levelTwoConcept[0]['Identifier'], 
                    levelTwoConcept[0]['Version'])
                reference_to_level_two_group=create_group_reference('uk.closer', level_two_group_uuid, 1, 
                    namespace_version, topic_type, C)
                level_one_group_object[0].append(reference_to_level_two_group)
                ddiObjectsLevelTwo.append({'Item': level_two_group_object, 
                    'DatasetName': level_two_group['DatasetName']})
        ddiObjectsLevelOne.append({'Item': level_one_group_object, 
                    'DatasetName': level_one_group_to_create['DatasetName']})
   return({"LevelZero": ddiObjectsLevelZero, "LevelOne": ddiObjectsLevelOne, "LevelTwo": ddiObjectsLevelTwo})

def create_ddi_objects_for_modified_level_one_topics(level_one_objects_to_modify, C):
   """Creates ddi objects that represent variable groups which are modified level one topics that
   already exist in the repository.

   Arguments:
        level_one_objects_to_modify (list):  A list of items containing information about the 
                level one groups that need to be modified because a level two group is being 
                created in a dataset where the associated level one group already exists 
                (e.g. when we are creating a level two group in a dataset representing 
                the 10320 topic, and the 103 topic already exists in that dataset).          

        C (ColecticaObject): an authenticated ColecticaObject instance.

   Returns:
        dict: A dictionary containing three lists of objects: 
            1. Objects containing information about the DDI level zero topic groups that include 
            references to the modified level one groups. These level zero topics aren't modified
            by this method, but are included for convenience when validating the topic group
            modifications/creations performed by this group.
            2. Objects containing information about the DDI level one topic groups that have been 
            modified.
            3. Objects containing information about the DDI level two topic groups that have been 
            created.
   """   
   allConcepts=C.search_items(C.item_code('Concept'))['Results']
   # get rid of concepts that don't properly define an itemname
   concepts=[x for x in allConcepts if list(x['ItemName'].keys())==['en-GB']]
   uniqueL1GroupsToModify=list([{"LevelOneTopicName": level_one_object['Item']['ItemName'][language], 
        "LevelTwoGroupName": level_one_object['LevelTwoGroupName'], 
        "Item": level_one_object['Item'], 
        "NamespaceVersion": level_one_object['NamespaceVersion'], 
        "DatasetName": level_one_object['DatasetName']} for level_one_object in level_one_objects_to_modify])
   ddiObjectsLevelZero = []
   modifiedDdiObjectsLevelOne = []
   newDdiObjectsLevelTwo = []
   for level_one_group in uniqueL1GroupsToModify:
        level_one_group_agency_id=level_one_group['Item']['AgencyId']
        level_one_group_identifier=level_one_group['Item']['Identifier']
        level_one_group_version=level_one_group['Item']['Version']
        level_one_group_object = get_current_state_of_topic_group(level_one_group_agency_id, 
          level_one_group_identifier, modifiedDdiObjectsLevelOne, C, version=level_one_group_version)
        level_two_group_uuid=str(uuid.uuid4())
        level_two_group_name=level_one_group['LevelTwoGroupName']
        topic_type=level_one_group['Item']['ItemType']
        namespace_version=level_one_group['NamespaceVersion']
        level_two_group_label=get_group_label(level_two_group_name, topic_type, C)
        concept=[concept for concept in concepts if concept['ItemName']['en-GB']==level_two_group_name]
        if len(concept)==1:
            level_two_group_object=create_variable_group(level_two_group_name, 
                level_two_group_label, 
                level_two_group_uuid, 
                namespace_version,
                concept[0]['AgencyId'],
                concept[0]['Identifier'], 
                concept[0]['Version'])
            reference_to_level_two_group=create_group_reference('uk.closer', 
                level_two_group_uuid, 
                1, 
                namespace_version, 
                topic_type, 
                C)
            level_zero_group_for_level_one_topic=get_level_zero_group_for_topic(level_one_group['Item'], C)
            if len([level_zero_object for level_zero_object in ddiObjectsLevelZero 
                if level_zero_object['Item'][0][2].text==level_zero_group_for_level_one_topic[0][2].text])==0:
                    ddiObjectsLevelZero.append({"Identifier": level_one_group['Item']['Identifier'],
                        "AgencyId": level_one_group['Item']['AgencyId'],
                        "Version": level_one_group['Item']['Version'],
                        "ItemType": level_one_group['Item']['ItemType'],
                        "Item": level_zero_group_for_level_one_topic,
                        "DatasetName": level_one_group['DatasetName']}) 
            get_element_fragment_by_name(level_one_group_object, "VariableGroup").append(
                reference_to_level_two_group)
            update_list_of_topic_groups(level_one_group_object,
                               level_one_group_agency_id,
                               level_one_group_identifier,
                               level_one_group_version,
                               topic_type,
                               modifiedDdiObjectsLevelOne,
                               dataset=level_one_group['DatasetName'])
            newDdiObjectsLevelTwo.append({"Item": level_two_group_object, 
                "DatasetName": level_one_group['DatasetName']})
        else:
            print(f"Could not find Concept for level two group {level_two_group_name}")   
   return({ "LevelZero": ddiObjectsLevelZero,
            "LevelOne": [{"Item": x['Item'], "DatasetName": x['DatasetName']} for x in modifiedDdiObjectsLevelOne],
            "LevelTwo": newDdiObjectsLevelTwo})

def validateLevelTwoTopics(levelZeroTopics, levelOneTopics, levelTwoTopics, C):
   """Validates level two topics by checking that:
       1. The dataset containing the level two topic exists.
       2. The level two topic is referenced from a level one topic group in the same dataset.
       3. The first three digits of the level two topic name match the level one topic name.
       4. The level one topic is referenced from a level zero topic group.
       5. The dataset label for the dataset containing the level two topic matches the label
          of the level zero topic group.

    Arguments:
        levelZeroTopics (list): A list of level zero topic groups.
        levelOneTopics (list): A list of level one topic groups.
        levelTwoTopics (list): A list of level two topic groups.
        C (ColecticaObject): an authenticated ColecticaObject instance.
    Returns:
        dict: A dictionary object containing two lists: 
            1. The validated level two topics.
            2. The invalid level two topics.
   """ 
   validatedLevelTwoTopics = []
   invalidLevelTwoTopics = [] 
   print("Validating level two topics...")
   for levelTwoTopic in levelTwoTopics:
       levelTwoTopicName=get_elements_of_type(levelTwoTopic['Item'], 
            "VariableGroupName")[0][0].text
       dataset=C.search_items(
                          C.item_code('Data File'),
                          SearchTerms=str(levelTwoTopic['DatasetName']).strip(),
                          SearchLatestVersion=True)['Results']
       found = False
       if len(dataset)==1:
            # Dataset containing level two topic found...
            datasetLabel=dataset[0]['Label']['en-GB']
            identifier = levelTwoTopic['Item'][0][2].text
            for levelOneTopic in levelOneTopics:
                levelOneTopicName=get_elements_of_type(levelOneTopic['Item'], 
                    "VariableGroupName")[0][0].text
                level_one_refs=find_all_references(levelOneTopic['Item'], 
                    'uk.closer', 
                    identifier)
                if len(level_one_refs)==1 and levelOneTopic['DatasetName']==levelTwoTopic['DatasetName']:
                    # Level two reference found in level one group, and dataset names for groups match...
                    if levelTwoTopicName[0:3]==levelOneTopicName:
                        # First three digits of level two topic name matches level one topic name...
                        level_one_identifier=levelOneTopic['Item'][0][2].text
                        for levelZeroTopic in levelZeroTopics:
                            level_zero_refs=find_all_references(levelZeroTopic['Item'], 
                                'uk.closer', 
                                level_one_identifier)
                            if len(level_zero_refs)==1:
                                # Level one reference found in level zero, now check labels match...
                                level_zero_label = get_element_by_name(
                                    levelZeroTopic['Item'], 
                                    'Label')['Content']
                                if level_zero_label==datasetLabel:
                                    # Labels for dataset containing level two group, level one group and level zero 
                                    # group all match
                                    found=True
                                    validatedLevelTwoTopics.append(levelTwoTopic)
       if not found:
                invalidLevelTwoTopics.append(levelTwoTopic)       
   if len(validatedLevelTwoTopics) == len(levelTwoTopics):
        print("""The validation has been successful. For each of the specified level two topics, the following checks have passed: 
        
        1. The dataset containing the level two topic exists.
        2. The level two topic is referenced from a level one topic group in the same dataset.
        3. The first three digits of the level two topic name match the level one topic name.
        4. The level one topic is referenced from a level zero topic group.
        5. The dataset label for the dataset containing the level two topic matches the label
          of the level zero topic group.""")                        
   return { 
            "ValidatedLevelTwoTopics": validatedLevelTwoTopics, 
            "InvalidLevelTwoTopics": invalidLevelTwoTopics
          }

def validateLevelOneTopics(ddi_objects_level_zero, level_one_topics, C):
   """Validates level one topics by checking that:
       1. The level one topic is referenced from a level zero topic group.
       2. The dataset label for the dataset containing the level one topic matches the label
          of the level zero topic group.

    Arguments:
        ddi_objects_level_zero (list): A list of level zero topic groups.
        level_one_topics (list): A list of level one topic groups.
        C (ColecticaObject): an authenticated ColecticaObject instance.
    Returns:
        dict: A dictionary object containing two lists: 
            1. The validated level one topics.
            2. The invalid level one topics.
   """ 
   validatedLevelOneTopics = [] 
   invalidLevelOneTopics = []
   found = False
   print("Validating level one topics...")
   for level_one_topic in level_one_topics:
            level_one_identifier=level_one_topic['Item'][0][2].text
            for level_zero_object in ddi_objects_level_zero:
                level_zero_refs=find_all_references(level_zero_object['Item'], 
                    'uk.closer', 
                    level_one_identifier)
                if len(level_zero_refs)==1:
                    # Level one reference found in level zero, now check dataset labels match...
                    physical_instance = C.search_items(
                        C.item_code('Data File'),
                        SearchTerms=str(level_one_topic['DatasetName']).strip(),
                        SearchLatestVersion=True)['Results']
                    if len(physical_instance)==1:
                        levelOneDatasetLabel=physical_instance[0]['Label']['en-GB']                   
                        levelZeroGroupLabel=(get_element_by_name(
                            level_zero_object['Item'], 'Label')['Content'])
                        if levelOneDatasetLabel==levelZeroGroupLabel:
                            # Dataset labels for level one and the level zero label match
                            validatedLevelOneTopics.append(level_one_topic)
                            found = True
            if not found:
                invalidLevelOneTopics.append(level_one_topic)
   if len(validatedLevelOneTopics) == len(level_one_topics):
        print("""The validation has been successful. For each of the specified level one topics, the 
        following checks have passed: 
        
        1. The level one topic is referenced from a level zero topic group.
        2. The dataset label for the dataset containing the level one topic matches the label
          of the level zero topic group.""")
   return {
           "ValidatedLevelOneTopics": validatedLevelOneTopics, 
           "InvalidLevelOneTopics": invalidLevelOneTopics
          }

def update_topics(topic_reassignments_data_frame, C, updated_topic_groups=[]):
    """Method for reassigning items to new topics. The code iterates through a data frame
    containing details of new item topic assignments and performs the reassignments, storing
    DDI objects representing the updated topics. 

    Arguments:
        topic_reassignment_details (pd.Series): A pandas Series containing details of a topic reassignment.
        C (ColecticaObject): an authenticated ColecticaObject instance.
        updated_topic_groups (list): List of dict-like entries representing topic groups.

    Returns:

    """
    # Initialise lists...
    items_not_present_in_source_topic = []
    items_present_in_destination_topic = []
    reference_from_source_ddi_version = None
    # Iterate through the rows in the data frame. Each row contains details of a topic
    # reassignment for a item...
    for topic_reassignment_details in topic_reassignments_data_frame.iloc:
        print("Performing the following topic reassignment...")
        print(f"Item {topic_reassignment_details.iloc['itemUrns']} to {topic_reassignment_details.iloc['destinationTopicGroups']}")
        item_agency_id = topic_reassignment_details.iloc['itemUrns'].split(":")[2]
        item_identifier = topic_reassignment_details.iloc['itemUrns'].split(":")[3]
        item_version = topic_reassignment_details.iloc['itemUrns'].split(":")[4]
        item = C.get_item_json(item_agency_id, item_identifier, version = item_version)
        topic_type=""
        if item['ItemType'] == C.item_code('Variable'):
            topic_type=C.item_code('Variable Group')
        elif item['ItemType'] == C.item_code('Question'):
            topic_type=C.item_code('Question Group')
        reference_to_move=None
        reference_from_source_ddi_version = None
        if topic_reassignment_details.iloc['sourceTopicGroups'] !='':      
            source_group_item_agency_id = topic_reassignment_details.iloc['sourceTopicGroups'].split(":")[2]
            source_group_item_identifier = topic_reassignment_details.iloc['sourceTopicGroups'].split(":")[3]
            source_group = C.get_item_json(source_group_item_agency_id,
                source_group_item_identifier)
            # We get the current state of the group containing a reference to the item.
            # This group represents the topic the item is currently assigned
            # to.
            source_group_item = get_current_state_of_topic_group(
                                                       source_group['AgencyId'],
                                                       source_group['Identifier'],
                                                       updated_topic_groups,
                                                       C,
                                                       version=source_group['Version']
                                                       )
            # Find and remove the reference to the item in the source group/topic.
            references_to_move = find_all_references(
                        source_group_item, item['AgencyId'], item['Identifier'])
            if len(references_to_move) > 0:
                for reference_to_move in references_to_move:
                        source_group_item[0].remove(reference_to_move)
                        # We need to take note of the namespace version for the reusable element,
                        # we use this later when determining if we need to update the version
                        # number to the version used in the destination topic group.
                        reference_from_source_ddi_version = ("ddi:reusable:"
                                f"{get_namespace(reference_to_move.tag).split(':')[2]}")
            # Finally we update the array containing the most current versions of the
            # group/topics with the updated source topic...              
            update_list_of_topic_groups(source_group_item,
                               source_group['AgencyId'],
                               source_group['Identifier'],
                               source_group['Version'],
                               source_group['ItemType'],
                               updated_topic_groups,
                               dataset=topic_reassignment_details.iloc['dataset'])     
        destination_group_item_agency_id = topic_reassignment_details.iloc['destinationTopicGroups'].split(":")[2]
        destination_group_item_identifier = topic_reassignment_details.iloc['destinationTopicGroups'].split(":")[3]
        destination_group_item_version = topic_reassignment_details.iloc['destinationTopicGroups'].split(":")[4]        
        # We get the current state of the group that we will be adding a
        # reference to the item to. This group represents the topic the
        # item will be reassigned to.
        destination_item = get_current_state_of_topic_group(
                                                            destination_group_item_agency_id,
                                                            destination_group_item_identifier,
                                                            updated_topic_groups,
                                                            C,
                                                            version=destination_group_item_version,
                                                            )
        # We check to see if a reference to the item is already present in the
        # destination group/topic. This can be used to determine if the
        # topic reassignments described in the input file have already been
        # successfully performed.
        reference_in_destination_topic = find_all_references(destination_item, 
                        item['AgencyId'], item['Identifier'])
        if len(reference_in_destination_topic)==0:
                        # We need to get the namespaces for the item reference and the
                        # group representing the topic we are re-assigning the item to. These
                        # namespaces begin with the text 'ddi:reusable:' and are followed by a
                        # version number for DDI, e.g. ddi:reusable:3_2, ddi:reusable:3_3. The DDI
                        # versions for the group/topic currently referencing a item
                        # and the DDI version for the group/topic to which we want to
                        # reassign a item to may be different. We need to ensure that when
                        # adding a new item reference to a topic, they both have the same
                        # namespace, otherwise the topic group update will not work.
                        destination_ddi_version_reusable = ("ddi:reusable:"
                                f"{get_namespace(destination_item.tag).split(':')[2]}")
                        destination_ddi_version_datacollection = ("ddi:datacollection:"
                                f"{get_namespace(destination_item[0].tag).split(':')[2]}")    
                        # If the namespace for the item reference from the group/topic
                        # that the item currently belongs to has a different DDI version than
                        # the group/topic that we want to add the reference to, we need
                        # to create a new version of the reference which has the same namespace as
                        # the group/topic we will be adding it to.
                        if (reference_from_source_ddi_version != destination_ddi_version_reusable 
                            or reference_to_move is None):
                                if topic_type == C.item_code('Variable Group'):
                                    new_reference = create_variable_reference(item_agency_id,
                                                                   item_identifier,
                                                                   item_version,
                                                                   destination_ddi_version_reusable
                                                                   )
                                else:
                                    new_reference = create_question_reference(item_agency_id,
                                                                   item_identifier,
                                                                   item_version,
                                                                   destination_ddi_version_reusable,
                                                                   destination_ddi_version_datacollection
                                                                   )
                        else:
                                new_reference = reference_to_move
                        # If the reference isn't already in the destination topic/group DDI, we add the 
                        # reference to it...
                        if reference_to_move==None or len(find_all_references(destination_item, reference_to_move[0].text, reference_to_move[1].text))==0:
                                destination_item[0].append(new_reference)
                                # ...and we update the entry for the destination topic in our array of topic groups.
                                update_list_of_topic_groups(destination_item, 
                                   destination_group_item_agency_id,
                                   destination_group_item_identifier,
                                   destination_group_item_version,
                                   topic_type,
                                   updated_topic_groups,
                                   dataset=topic_reassignment_details.iloc['datasets']
                             )
        else:
                if len(references_to_move)==0:
                    print((f"Item {topic_reassignment_details.iloc['itemUrns']} "
                            f" is not in topic "
                            f"{topic_reassignment_details.iloc['sourceTopicGroups']}"))
                    items_not_present_in_source_topic.append(
                            (topic_reassignment_details.iloc['itemUrns'], topic_reassignment_details.iloc['sourceTopicGroups']))
                if reference_in_destination_topic is not None:
                    print((f"Item {topic_reassignment_details.iloc['itemUrns']} "
                            f" is already in topic "
                            f"{topic_reassignment_details.iloc['destinationTopicGroups']}"))
                    items_present_in_destination_topic.append(
                            (topic_reassignment_details.iloc['itemUrns'], topic_reassignment_details.iloc['destinationTopicGroups']))
    number_of_topic_reassignments_already_performed = len([x for x in items_not_present_in_source_topic
                                           if x in items_present_in_destination_topic])
    number_of_topic_reassignments_to_be_performed = len(topic_reassignments_data_frame) - number_of_topic_reassignments_already_performed
    print(f"{number_of_topic_reassignments_already_performed} of {len(topic_reassignments_data_frame)} topic" 
          f" reassignments in the input file have already been performed,")
    print(f"{number_of_topic_reassignments_to_be_performed} pair(s) of DDI Fragments implementing topic"
           " reassignments specified in the input file have been created.")            
    if (len(items_not_present_in_source_topic) == len(topic_reassignments_data_frame) and
       len(items_present_in_destination_topic) == len(topic_reassignments_data_frame)):
       print("The item topic reassignments in the input data file have already all been "
             "successfully executed.")
    return ({ 
             "ItemsMovedFromSourceTopic": items_not_present_in_source_topic, 
             "ItemsMovedToDestinationTopic": items_present_in_destination_topic
             })

def validate_ddi_implementing_topic_reassignments(input_file_name, 
    updated_topic_groups, 
    C, 
    language="en-GB"):
    """Read topic reassignments from an Excel file and validate corresponding DDI items 
    and references.

    # Comment: This function reads topic-reassignment rows from the supplied Excel file, and determines 
    # if the item specified in each row is not in the appropriate source topic group in the 
    # updated_topic_groups array, and is present in the relevant destination topic group in the same array; 
    # i.e. if the topic reassignment for the item has been successful. 
    
    Arguments:
        input_file_name (str): Path to the Excel file containing topic reassignment rows.
        updated_topic_groups (list): List of dict-like entries representing topic groups;
            we search for groups by their name and the name of the dataset that contains them (in
            the case of Variable Groups) or is associated with their related variables (in the case of 
            Question Groups).
        C (ColecticaObject): an authenticated ColecticaObject instance.
        
    Returns:
        tuple: (source_topic_not_found, destination_topic_not_found, found_source_topics, found_destination_topics)
            - source_topic_not_found (list): Rows from the input file for which the item was not found in the
              source topic group.
            - destination_topic_not_found (list): Rows for which the item was not found in the destination topic 
              group.
            - found_source_topics (list): References (DDI elements) discovered in the source topic groups for 
              matched rows.
            - found_destination_topics (list): References (DDI elements) discovered in the destination topic groups
              for matched rows.
    
    All the lists in the above tuple should have a length of zero, except the last list (found_destination_topics),
    which should have a length equal to the number of rows in the input file, if the topic reassignments have been
    successfully implemented in the DDI items representing topic groups in updated_topic_groups.
    """
    print(f"Reading and validating topic reassignments from {input_file_name}...")
    data = pd.read_excel(input_file_name)
    source_topic_not_found=[]
    destination_topic_not_found=[]
    items_found_in_source_topics=[]
    items_found_in_destination_topics=[]
    for topic_reassignment_details in data.iloc:  
        url = topic_reassignment_details.iloc[2]
        agency_id = url.split("/")[4]
        identifier = url.split("/")[5]
        version = url.split("/")[6]
        item_urn = f"urn:ddi:{agency_id}:{identifier}:{str(version)}"
        updated_source_topic=[topic_group for topic_group in updated_topic_groups 
            if topic_group['DatasetName']==topic_reassignment_details.iloc[0]
            and get_elements_of_type(topic_group['Item'], "VariableGroupName")!=[]
            and get_elements_of_type(topic_group['Item'], "VariableGroupName")[0][0].text
                ==str(topic_reassignment_details.iloc[4])]
        updated_destination_topic=[topic_group for topic_group in updated_topic_groups 
            if topic_group['DatasetName']==topic_reassignment_details.iloc[0]
            and get_elements_of_type(topic_group['Item'], "VariableGroupName")!=[]
            and get_elements_of_type(topic_group['Item'], "VariableGroupName")[0][0].text
                ==str(topic_reassignment_details.iloc[5])]
        if len(updated_source_topic)==1:
            references_in_source_topic=find_all_references(updated_source_topic[0]['Item'], agency_id, identifier)
            for reference_in_source_topic in references_in_source_topic:
                items_found_in_source_topics.append(reference_in_source_topic)
        elif str(topic_reassignment_details.iloc[4]).strip()!='no_topic':
            source_topic_not_found.append(topic_reassignment_details)
        if len(updated_destination_topic)==1:
            references_in_destination_topic=find_all_references(updated_destination_topic[0]['Item'], agency_id, identifier)
            if len(references_in_destination_topic)==0:
                print("NO REFERENCES IN DESTINATION TOPIC")
                print(topic_reassignment_details)
            for reference_in_destination_topic in references_in_destination_topic:
                items_found_in_destination_topics.append(reference_in_destination_topic)
        else: 
            destination_topic_not_found.append(topic_reassignment_details)
    print(f"Number of items still in DDI representing source topic: {len(items_found_in_source_topics)}")
    print(f"Number of items found in DDI representing destination topic: {len(items_found_in_destination_topics)}")    
    print(f"Number of items not found in DDI representing destination topic: {len(data) - len(items_found_in_destination_topics)}")
    if len(items_found_in_source_topics)==0 and len(items_found_in_destination_topics)==len(data):
            print("The creation of DDI items that implement all the topic reassignments has been successful")
    else:
            print("There were issues with the creation of DDI items that implement all the topic reassignments."
                    " Please see the details of missing source or destination topics, or missing references")
    return ({"SourceTopicsNotFound": source_topic_not_found, 
            "DestinationTopicsNotFound": destination_topic_not_found, 
            "ItemsFoundInSourceTopics": items_found_in_source_topics, 
            "ItemsFoundInDestinationTopics": items_found_in_destination_topics})
