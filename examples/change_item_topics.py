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
updated_groups = examples.change_item_topics.update_topics('examples/topic_reassignments.xlsx', C)
examples.lib.utility.update_repository(updated_groups, 'Repository commit message - update topics', C)
"""
from examples.lib.utility import (
    get_namespace,
    find_all_references,
    create_variable_reference,
    create_question_reference,
    create_concept_reference,
    get_current_state_of_topic_group,
    update_list_of_topic_groups,
    get_urn_from_item,
    get_item_from_topic_name,
    create_group,
    create_group_reference,
    create_group_lookup_dict,
    get_current_state_of_topic_group,
    get_level_zero_group_2,
    get_level_zero_group,
    get_group_label,
    get_elements_of_type,
    get_element_by_name   
)
import defusedxml
#pip install openpyxl #might need to install openpyxl, a dependency for read-excel
import pandas as pd
import uuid
from collections import Counter

language = "en-GB"


def update_urns_list(urns, item, containing_item, topic_type, variable_topic, 
    target_topic, datasetToZeroGroupMappings={}, dataset_name=""):
    destination_topic_urn=""
    containing_item_details = [{"AgencyId": containing_item['AgencyId'],
                      "Identifier": containing_item['Identifier'],
                      "Version": containing_item['Version'],
                }]
    item_urn = get_urn_from_item(item)
    source_groups = C.search_relationship_byobject(item['AgencyId'], 
                   item['Identifier'], Version=item['Version'], 
                   item_types=topic_type, Descriptions=True)
    for source_group in source_groups:
        source_topic_urn = get_urn_from_item(source_group)
    if len(source_groups)==0:
        source_topic_urn = ""
    destination_group=get_item_from_topic_name(str(target_topic), 
            topic_type, containing_item_details, C, datasetToZeroGroupMappings=datasetToZeroGroupMappings) #MAYBE NEED TO ADD LEVEL ZERO MAPPINGS HERE?
    if len(destination_group)==1:
            destination_topic_urn = get_urn_from_item(destination_group[0])
    elif topic_type==C.item_code('Variable Group'):
            # the topic groups all exist for questions which is why we only do the below for variable groups 
            destination_group_details=[x for x in updated_topic_groups if x['Dataset']==dataset_name 
                and get_elements_of_type(x['Item'], "VariableGroupName")[0][0].text==str(target_topic)]
            if len(destination_group_details)==1:
                destination_topic_urn=get_urn_from_fragment(destination_group_details[0]['Item'])
            #destination_topic_urn = get_urn_from_fragment([x[0] for x in updated_topic_groups if x['Dataset']==dataset_name 
            #    and get_elements_of_type(x['Item'], "VariableGroupName")[0][0].text==str(target_topic)]
            #)   
    if item_urn not in urns['itemUrns'] and destination_topic_urn != "":
            urns['itemUrns'].append(item_urn)
            urns['sourceTopicGroups'].append(source_topic_urn)
            urns['destinationTopicGroups'].append(destination_topic_urn)
            urns['datasets'].append(dataset_name)  
    #else:
    #        print(('Error getting destination group item: expected to find 1 item, but instead ' 
    #              f'found {len(destination_group)}'))        

def generate_urn_dataframe_for_questions_and_variables(input_file_name, C, datasetToZeroGroupMappings={}):  
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
    for topic_reassignment_details in data.iloc:
        print(count)
        count=count+1
        print(topic_reassignment_details)
        dataset_name = topic_reassignment_details.iloc[0]
        variable_topic= topic_reassignment_details.iloc[4]
        target_topic= topic_reassignment_details.iloc[5]
        url = topic_reassignment_details.iloc[2]
        agency_id = url.split("/")[4]
        identifier = url.split("/")[5]
        item = C.get_item_xml(agency_id, identifier)
        version = item['Version']
        physical_instance_containing_variable = C.search_items(
                    C.item_code('Data File'),
                    SearchTerms=str(dataset_name).strip(),
                    SearchLatestVersion=True)['Results']
        if len(physical_instance_containing_variable)==1:
            update_urns_list(urns, item, physical_instance_containing_variable[0], 
               C.item_code('Variable Group'), variable_topic, target_topic, 
               datasetToZeroGroupMappings=datasetToZeroGroupMappings, 
               dataset_name=dataset_name)
        allRelatedQuestions= C.search_relationship_bysubject(agency_id, identifier, Version=version, 
            item_types=C.item_code("Question"), Descriptions=True)
        for relatedQuestion in allRelatedQuestions:
            question_sets=C.query_set(relatedQuestion['AgencyId'], 
               relatedQuestion['Identifier'], 
               version=relatedQuestion['Version'], 
               reverseTraversal=True, 
               item_types=[C.item_code('Data Collection')])
            if len(set([(x['Item1']['Item3'], x['Item1']['Item1']) for x in question_sets] ))==1:
                latest_version_of_question_set = max([x['Item1']['Item2'] for x in question_sets])
                containing_item=C.get_item_xml(question_sets[0]['Item1']['Item3'], 
                    question_sets[0]['Item1']['Item1'],
                    version=latest_version_of_question_set)
                update_urns_list(urns, relatedQuestion, containing_item, 
                    C.item_code('Question Group'), variable_topic, target_topic, 
                    datasetToZeroGroupMappings=datasetToZeroGroupMappings)           
    return (pd.DataFrame(urns))

def get_level_zero_group_from_dataset(physical_instance_containing_variable, all_variable_groups, C):
    level_zero_group_details=C.search_relationship_byobject(
              physical_instance_containing_variable['AgencyId'], 
              physical_instance_containing_variable['Identifier'], 
              Version=physical_instance_containing_variable['Version'], 
              item_types=[C.item_code('Variable Group')])
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
    return(defusedxml.ElementTree.fromstring(level_zero_group_item))   
           
def create_topic_reassignment_dict(topic_reassignment_details)
    topic_reassignment_dict={}
    dataset_name = topic_reassignment_details.iloc[0]
    topic_reassignment_dict['dataset_name']=dataset_name    
    url = topic_reassignment_details.iloc[2]
    topic_reassignment_dict['destination_topic_name'] = str(topic_reassignment_details.iloc[5])
    agency_id = url.split("/")[4]
    identifier = url.split("/")[5]
    item = C.get_item_xml(agency_id, identifier)
    item_element = defusedxml.ElementTree.fromstring(item['Item'])
    topic_reassignment_dict['namespace_version'] = get_namespace(item_element.tag).split(':')[2]        
    #topic_type=C.item_code('Variable Group')
    #containing_item_type=C.item_code('Data File')
    physical_instance_containing_variable = C.search_items(
                    containing_item_type,
                    SearchTerms=str(dataset_name).strip(),
                    SearchLatestVersion=True,
                    UsePrefixSearch=True )['Results'][0]
    topic_reassignment_dict['physical_instance_containing_variable'] = physical_instance_containing_variable
    topic_reassignment_dict['physical_instance_search_set'] = [{
                "AgencyId": physical_instance_containing_variable['AgencyId'],
                "Identifier": physical_instance_containing_variable['Identifier'],
                "Version": physical_instance_containing_variable['Version']
            }]
    return topic_reassignment_dict    
                   
def find_topics_to_create(input_file_name, C, language="en-GB", datasetToZeroGroupMappings={}):
    """Method for generating input for code that updates topics. The code iterates through 
    a spreadsheet containing details of new item topic assignments and generates a dataframe
    of URNs that can be used as input to a method that reassigns items to new topics. 
    """
    print(f"Reading topic reassignments from {input_file_name}")
    data = pd.read_excel(input_file_name)
    count=0
    levelOneGroupsToCreate=[]
    levelOneGroupsToModify=[]
    levelTwoGroupsToCreate=[]
    all_variable_groups=C.search_items(C.item_code('Variable Group'), SearchLatestVersion=True)['Results']
    for topic_reassignment_details in data.iloc:
        topic_dict = create_topic_reassignment_dict(topic_reassignment_details)
        print(count)
        count=count+1
        topic_type=C.item_code('Variable Group')
        level_zero_group=get_level_zero_group_from_dataset(topic_dict['physical_instance_containing_variable'],
                all_variable_groups, C)
        destination_topic = get_item_from_topic_name(topic_dict['destination_topic_name'], topic_type, 
            topic_dict['physical_instance_search_set'], C, datasetToZeroGroupMappings=datasetToZeroGroupMappings)
        if len(destination_topic)==0:
                level_one_group_name = str(destination_topic_name)[0:3]
                if (len(destination_topic_name)==5 and 
                     (topic_dict['dataset_name'], topic_dict['destination_topic_name']) 
                     not in [(x[0], x[1]) for x in levelTwoGroupsToCreate]):
                       levelTwoGroupsToCreate.append((topic_dict['dataset_name'], 
                            topic_dict['destination_topic_name'], topic_dict['namespace_version']))                   
                levelOneGroups=get_item_from_topic_name(level_one_group_name, topic_type, 
                    topic_dict['physical_instance_search_set'], C, datasetToZeroGroupMappings=datasetToZeroGroupMappings)
                if len(levelOneGroups)==0:
                    if (topic_dict['dataset_name'], level_one_group_name) not in [(x[0], x[1]) for x in levelOneGroupsToCreate]:
                       levelOneGroupsToCreate.append((topic_dict['dataset_name'], 
                        level_one_group_name, 
                        level_zero_group, 
                        topic_dict['namespace_version']))       
                else:
                    if ((level_one_group_name, level_two_group_name, topic_dict['dataset_name']) not in 
                          [(x[0], x[1], x[5]) for x in levelOneGroupsToModify]):
                              for group in levelOneGroups:
                                 levelOneGroupsToModify.append((level_one_group_name, 
                                              level_two_group_name, 
                                              topic_type,
                                              group,
                                              topic_dict['namespace_version'],
                                              topic_dict['dataset_name'])) 
    return (levelOneGroupsToCreate, levelTwoGroupsToCreate, levelOneGroupsToModify) 

#THERE IS AN ISSUE WITH EG https://discovery.closer.ac.uk/item/uk.closer/84383692-5097-4510-8463-985664c08c18
#what was this issue?

def create_ddi_objects_with_new_level_one_topics(topics_to_create, C):
   allConcepts=C.search_items(C.item_code('Concept'))['Results']
   # get rid of whitehall2 concept that doesn't properly define an itemname
   concepts=[x for x in allConcepts if list(x['ItemName'].keys())==['en-GB']]
   ddiObjectsLevelZero=[]
   ddiObjectsLevelOne=[]
   ddiObjectsLevelTwo=[]
   for topic in topics_to_create[0]:
      level_one_group_uuid=str(uuid.uuid4())
      level_one_group_name=topic[1]
      topic_type=C.item_code('Variable Group')
      namespace_version=topic[3]   
      if type(topic[2]) is list:
          level_zero_group_urn=f"urn:ddi:{topic[2][0]['Item1']['Item3']}:{topic[2][0]['Item1']['Item1']}:{str(topic[2][0]['Item1']['Item3'])}"
      else:       
          level_zero_group_urn=topic[2][0][0].text
      zero_group_agency_id = level_zero_group_urn.split(":")[2]
      zero_group_identifier = level_zero_group_urn.split(":")[3]
      zero_group_version = level_zero_group_urn.split(":")[4]
      level_zero_group_object = get_current_state_of_topic_group(zero_group_agency_id, 
          zero_group_identifier, ddiObjectsLevelZero, C, version=zero_group_version)   
      level_one_group_label=get_group_label(level_one_group_name, topic_type, C)
      concept=[x for x in concepts if x['ItemName']['en-GB']==level_one_group_name][0]
      level_one_group_object = create_group(level_one_group_name, 
          level_one_group_label, 
          level_one_group_uuid, 
          namespace_version,
          concept['AgencyId'], 
          concept['Identifier'], 
          concept['Version'])
      level_one_group_reference=create_group_reference('uk.closer', 
        level_one_group_uuid, 1, namespace_version, topic_type, C)
      get_element_fragment_by_name(level_zero_group_object, "VariableGroup").append(level_one_group_reference)
      update_list_of_topic_groups(level_zero_group_object,
                               zero_group_agency_id,
                               zero_group_identifier,
                               zero_group_version,
                               topic_type,
                               ddiObjectsLevelZero,
                               dataset=topic[0])                           
      level_two_groups=[x for x in topics_to_create[1] if x[0]==topic[0] and x[1][0:3]==topic[1]]
      for level_two_group in level_two_groups:
          level_two_group_uuid=str(uuid.uuid4())
          level_two_group_name=level_two_group[1]
          level_two_group_label=get_group_label(level_two_group_name, 
             topic_type, C)
          concept=[x for x in concepts if x['ItemName']['en-GB']==level_two_group_name][0]   
          level_two_group_object=create_group(level_two_group_name, 
             level_two_group_label, level_two_group_uuid, namespace_version,
             concept['AgencyId'], 
             concept['Identifier'], 
             concept['Version'])
          reference_to_level_two_group=create_group_reference('uk.closer', level_two_group_uuid, 1, 
             namespace_version, topic_type, C)
          level_one_group_object[0].append(reference_to_level_two_group)
          ddiObjectsLevelTwo.append((level_two_group_object, level_two_group[0]))
      ddiObjectsLevelOne.append((level_one_group_object, topic[0]))
   return(ddiObjectsLevelZero, ddiObjectsLevelOne, ddiObjectsLevelTwo)
   
def validateLevelTwoTopics(levelZeroTopics, levelOneTopics, levelTwoTopics):
   referencesValidated=[]
   levelTwoNotInOne=[]
   count=0
   for x in levelTwoTopics:
       print(count)
       count=count+1
       #levelTwoTopicName=(x[0][0][4][0].text)
       levelTwoTopicName=get_elements_of_type(y[0], "VariableGroupName")[0][0].text
       dataset=C.search_items(
                          C.item_code('Data File'),
                          SearchTerms=str(x[1]).strip(),
                          SearchLatestVersion=True)['Results']
       if len(dataset)!=1:
            print("DATASET NOT FOUND OR MULTIPLE DATASETS FOUND")
       else:
            datasetLabel=dataset[0]['Label']['en-GB']
            found = False
            identifier = x[0][0][2].text
            for y in levelOneTopics:
                levelOneTopicName=get_elements_of_type(y[0], "VariableGroupName")[0][0].text
                level_one_refs=find_all_references(y[0], 'uk.closer', identifier)
                if len(level_one_refs)==1 and y[1]==x[1]:
                    print("LEVEL TWO REFERENCE FOUND IN LEVEL ONE GROUP, AND DATASET NAMES FOR GROUPS MATCH")
                    if levelTwoTopicName[0:3]==levelOneTopicName:
                        print("FIRST THREE DIGITS OF LEVEL TWO TOPIC NAME MATCHES LEVEL ONE TOPIC NAME")
                    level_one_identifier=y[0][0][2].text
                    for z in [z1 for z1 in levelZeroTopics]:
                        level_zero_refs=find_all_references(z['Item'], 'uk.closer', level_one_identifier)
                        if len(level_zero_refs)==1:
                            print("LEVEL ONE REFERENCE FOUND IN LEVEL ZERO")
                            level_zero_label = get_element_by_name(z['Item'], 'Label')['Content']
                            if level_zero_label==datasetLabel:
                                print("LABELS FOR DATASETS CONTAINING LEVEL ONE AND TWO GROUPS, AND THE LEVEL ZERO LABEL MATCH")
                                found=True
                        referencesValidated.append(x)
            if not found:
                levelTwoNotInOne.append(x)               
   return (referencesValidated, levelTwoNotInOne)

def validateLevelOneTopics(ddiObjectsLevelZero, levelOneTopics):
   #forChecking=[]
   referencesValidated3=[]
   for y in levelOneTopics:
            level_one_identifier=y[0][0][2].text
            for z in [z1 for z1 in ddiObjectsLevelZero]:
                level_zero_refs=find_all_references(z['Item'], 'uk.closer', level_one_identifier)
                if len(level_zero_refs)==1:
                    print("LEVEL ONE REFERENCE FOUND IN LEVEL ZERO")
                    #forChecking.append((get_element_by_name(y['Item'], 'VariableGroupName')['String'],
                    #y[1],
                    #get_element_by_name(z['Item'], 'Label')['Content']))
                    physical_instance = C.search_items(
                       C.item_code('Data File'),
                       SearchTerms=str(y[1]).strip(),
                       SearchLatestVersion=True)['Results']
                    if len(physical_instance)==1:
                        levelOneDatasetLabel=physical_instance[0]['Label']['en-GB']                   
                    b=(get_element_by_name(z['Item'], 'Label')['Content'])
                    print(levelOneDatasetLabel)
                    print(b)
                    if levelOneDatasetLabel==b:
                       referencesValidated3.append(y)
                       print("DATASET LABELS FOR LEVEL ONE AND THE LEVEL ZERO LABEL MATCH")
                    else:
                       print(levelOneDatasetLabel)
                       print(b) 
                       print("WRONG DATASET")
   return referencesValidated3 

                 
def create_ddi_objects_with_modified_level_one_topics(topics_to_create, C):
   allConcepts=C.search_items(C.item_code('Concept'))['Results']
   # get rid of whitehall2 concept that doesn't properly define an itemname
   concepts=[x for x in allConcepts if list(x['ItemName'].keys())==['en-GB']]
   uniqueL1GroupsToModify=list([(x[0], x[1], x[2], x[3], x[4], x[5]) for x in topics_to_create[2]])
   new_l2_topics=[]
   modified_l1_topics=[]
   levelZeroesForModifiedL1s=[]
   for x in uniqueL1GroupsToModify:
       level_one_group_agency_id=x[3]['AgencyId']
       level_one_group_identifier=x[3]['Identifier']
       level_one_group_version=x[3]['Version']
       level_one_group_object = get_current_state_of_topic_group(level_one_group_agency_id, 
          level_one_group_identifier, modified_l1_topics, C, version=level_one_group_version)
       level_two_group_uuid=str(uuid.uuid4())
       level_two_group_name=x[1]
       topic_type=x[2]
       namespace_version=x[4]
       level_two_group_label=get_group_label(level_two_group_name, topic_type, C)
       concept=[x for x in concepts if x['ItemName']['en-GB']==level_two_group_name][0]
       level_two_group_object=create_group(level_two_group_name, 
          level_two_group_label, level_two_group_uuid, namespace_version,
          concept['AgencyId'], 
          concept['Identifier'], 
          concept['Version'])
       reference_to_level_two_group=create_group_reference('uk.closer', level_two_group_uuid, 1, 
          namespace_version, topic_type, C)
       level_zero_group=get_level_zero_group_2(x[3]['AgencyId'], x[3]['Identifier'], x[3]['Version'], x[3]['ItemType'], C)
       if len([x for x in levelZeroesForModifiedL1s if x['Item'][0][2].text==level_zero_group[0][2].text])==0:
          levelZeroesForModifiedL1s.append({"Identifier": x[3]['Identifier'],
              "AgencyId": x[3]['AgencyId'],
              "Version": x[3]['Version'],
              "ItemType": x[3]['ItemType'],
              "Item": level_zero_group}) 
       get_element_fragment_by_name(level_one_group_object, "VariableGroup").append(reference_to_level_two_group)
       update_list_of_topic_groups(level_one_group_object,
                               level_one_group_agency_id,
                               level_one_group_identifier,
                               level_one_group_version,
                               topic_type,
                               modified_l1_topics,
                               dataset=x[5])
       new_l2_topics.append((level_two_group_object, x[5]))   
   return(levelZeroesForModifiedL1s, [(x['Item'], x['Dataset']) for x in modified_l1_topics], new_l2_topics)

""" MIGHT NEED TO KEEP THIS, OR FIT IT IN SOMEHOW; IT ADDS THE LEVEL ZERO TOPICS TO MODIFIED
L1 TOPICS THAT DON'T HAVE THEM   
finalLevelOnes=[]
levelZeroesForModifiedL1s=[]
for x in modified_l1_topics:
    level_zero_group=get_level_zero_group_2(x['AgencyId'], x['Identifier'], x['Version'], x['ItemType'], C)
    if len([x for x in levelZeroesForModifiedL1s if x['Item'][0][2].text==level_zero_group[0][2].text])==0:
       levelZeroesForModifiedL1s.append({"Identifier": x['Identifier'],
           "AgencyId": x['AgencyId'],
           "Version": x['Version'],
           "ItemType": x['ItemType'],
           "Item": level_zero_group})
    finalLevelOnes.append((x['Item'], x['Dataset'], level_zero_group))
"""


To test: 

1. We need to verify that all the groups in topics_to_create[0 and 1] do not currently exist.
for y in topics_to_create[0]:
    if len([(x[0], x[1]) for x in groupsInDatasets if x[0]==y[0] and x[1]==y[1]])!=0:
        print("ERROR - LEVEL ONE TOPIC ALREADY EXISTS")
for y in topics_to_create[1]:
    if len([(x[0], x[1]) for x in groupsInDatasets if x[0]==y[0] and x[1]==y[1]])!=0:
        print(y)
        print("ERROR - LEVEL TWO TOPIC ALREADY EXISTS") 
We also need to check that the level one topics in topics_to_create[2] do exist, and 
that the level two topics they refer to do not exist.
for y in topics_to_create[2]:
    if len([(x[0], x[1]) for x in groupsInDatasets if x[1]==y[0] and x[0]==y[5]])==0:
        print(y)
        print("ERROR - LEVEL ONE TOPIC TO MODIFY DOES NOT EXIST")
    if len([(x[1], x[1]) for x in groupsInDatasets if x[1]==y[1] and x[0]==y[5]])!=0:
        print(y)
        print("ERROR - LEVEL TWO TOPIC TO CREATE ALREADY EXISTS")

       
2. We need to verify that the set of groups in ddiObjectsLevelOne is the same as in
topics_to_create[0]
a=sorted(list(set([(x[0], x[1]) for x in topics_to_create[0]])))
b=sorted(list(set([(x[1], get_element_by_name(x[0], 'VariableGroupName')['String']) for x in ddiObjectsLevelOne])))
a==b

3. We need to verify that the set of groups in ddiObjectsLevelTwo is the same as in
topics_to_create[1]
a=sorted(list(set([(x[0], x[1]) for x in topics_to_create[1]])))
b=sorted(list(set([(x[1], get_element_by_name(x[0], 'VariableGroupName')['String']) for x in ddiObjectsLevelTwo])))
set([(x[0], x[1][0:3]) for x in topics_to_create[1] if (x[0], x[1]) not in b])
a==b

4. We need to verify that the set of groups in new_l2_topics is the same as in topics_to_create[2]

5. We need to verify that the set of groups in modified_l1_topics is the same as in topics_to_create[2]

6. We need to verify that all level two topics are referenced by a level one topic,
which in turn is referenced by a level zero topic. We need to verify that the level
one topic is the first three digits of the level two topic. We need to verify that
the label of the level zero topic is the same as the label of the dataset within
which the level two topic is found, and that the level zero topic is referenced
by this dataset. We need to verify that this dataset has the same name as the 
dataset name contained in the ddiObjectsLevelTwo tuple.

DONE in validateLevelTwoTopics

7. We need to verify that all level one topics are referenced by a level zero topic.
We need to verify that the label of the level zero topic is the same as the label of 
the dataset within which the level one topic is found, and that the level zero topic 
is referenced by this dataset.

DONE in validateLevelOneTopics

1. If we're creating a topic, it doesn't already exist. If we're modifying a topic,
it does already exist.
2+3+4+5. We're creating all the topics we need to; we're not missing anything
6 + 7. The newly created/modified topics are referenced by the appropriate ancestor items; where
necessary we have created ancestor items.

SOURCE NEEDS TO SPECIFY DATASET SEE TERMINAL
def update_topics(topic_reassignments_data_frame, C, updated_topic_groups=[]):
    """Method for reassigning items to new topics. The code iterates through a data frame
    containing details of new item topic assignments and performs the reassignments. 
    """
    # Initialise lists...
    item_not_present_in_source_topic = []
    item_present_in_destination_topic = []
    #updated_topic_groups = []
    reference_from_source_ddi_version = None
    delThis=[]
    count=0
    # Iterate through the rows in the data frame. Each row contains details of a topic
    # reassignment for a item...
    for topic_reassignment_details in topic_reassignments_data_frame.iloc:
      #print("Performing the following topic reassignment...")
      #print(f"Item {topic_reassignment_details.iloc[0]} to {topic_reassignment_details.iloc[2]}")
      #print(topic_reassignment_details.iloc[3])
        print(count)
        count=count+1
        #if count==174:
        print(f"Item {topic_reassignment_details.iloc[0]} to {topic_reassignment_details.iloc[2]}")
        #   print(topic_reassignment_details.iloc[3])    
        topic_reassignment_details.iloc[0]
        item_agency_id = topic_reassignment_details.iloc[0].split(":")[2]
        item_identifier = topic_reassignment_details.iloc[0].split(":")[3]
        item_version = topic_reassignment_details.iloc[0].split(":")[4]  
        item = C.get_item_json(item_agency_id, item_identifier, version = item_version)
        topic_type=""
        if item['ItemType'] == C.item_code('Variable'):
            topic_type=C.item_code('Variable Group')
        elif item['ItemType'] == C.item_code('Question'):
            topic_type=C.item_code('Question Group')
        reference_to_move=None
        reference_from_source_ddi_version = None
        if topic_reassignment_details.iloc[1] !='':      
            source_group_item_agency_id = topic_reassignment_details.iloc[1].split(":")[2]
            source_group_item_identifier = topic_reassignment_details.iloc[1].split(":")[3]
            source_group_item_version = topic_reassignment_details.iloc[1].split(":")[4]
            source_group = C.get_item_json(source_group_item_agency_id,
                source_group_item_identifier,
                version = source_group_item_version)
            # We get the current state of the group containing a reference to the item.
            # This group represents the topic the item is currently assigned
            # to.
            source_item = get_current_state_of_topic_group(
                                                       source_group['AgencyId'],
                                                       source_group['Identifier'],
                                                       updated_topic_groups,
                                                       C,
                                                       version=source_group['Version']
                                                       )
            # Find and remove the reference to the item in the source group/topic.
            references_to_move = find_all_references(
                        source_item, item['AgencyId'], item['Identifier'])
            if len(references_to_move) > 0:
                for reference_to_move in references_to_move:
                        source_item[0].remove(reference_to_move)
                        reference_from_source_ddi_version = ("ddi:reusable:"
                                f"{get_namespace(reference_to_move.tag).split(':')[2]}")
            # Finally we update the array containing the most current versions of the
            # group/topics with the updated source topic...              
            update_list_of_topic_groups(source_item,
                               source_group['AgencyId'],
                               source_group['Identifier'],
                               source_group['Version'],
                               source_group['ItemType'],
                               updated_topic_groups,
                               #reference_to_remove=reference_to_move,
                               dataset=topic_reassignment_details.iloc[3])     
        destination_group_item_agency_id = topic_reassignment_details.iloc[2].split(":")[2]
        destination_group_item_identifier = topic_reassignment_details.iloc[2].split(":")[3]
        destination_group_item_version = topic_reassignment_details.iloc[2].split(":")[4]        
        #destination_group = C.get_item_json(destination_group_item_agency_id,
        #    destination_group_item_identifier,
        #    version = destination_group_item_version)
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
        #print(destination_item)
        # We check to see if a reference to the item is already present in the
        # destination group/topic. This information can be used to determine if the
        # topic reassignments described in the input file have already been
        # successfully performed.
        reference_in_destination_topic = find_all_references(destination_item, 
                        item['AgencyId'], item['Identifier'])
        print(len(reference_in_destination_topic))
        if len(reference_in_destination_topic)==0:
                        # We need to get the namespaces for the item reference and the
                        # group representing the topic we are re-assigning the item to. These
                        # namespaces begin with the text 'ddi:reusable:' and are followed by a
                        # version number for DDI, e.g. ddi:reusable:3_2, ddi:reusable:3_3. The DDI
                        # versions for the group/topic currently referencing a item
                        # and the DDI version for the group/topic to which we want to
                        # reassign a item to may be different. We need to ensure that when
                        # adding a new item reference to a topic, they both have the same
                        # namespace, otherwise the group update will not work.
                        destination_ddi_version_reusable = ("ddi:reusable:"
                                f"{get_namespace(destination_item.tag).split(':')[2]}")
                        destination_ddi_version_datacollection = ("ddi:datacollection:"
                                f"{get_namespace(destination_item[0].tag).split(':')[2]}")    
                        # If the namespace for the item reference from the group/topic
                        # that the item currently belongs to has a different DDI version than
                        # the group/topic that we want to add the reference to, we need
                        # to create a new version of the reference which has the same namespace as
                        # the group/topic we will be adding it to.
                        print(reference_from_source_ddi_version)
                        print(destination_ddi_version_reusable)
                        if reference_from_source_ddi_version != destination_ddi_version_reusable or reference_to_move is None:
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
                        # If the reference isn't already in the topic/group we are adding a
                        # reference to, we add the reference to the group representing the topic it is being 
                        # reassigned to...
                        print(reference_to_move==None or len(find_all_references(destination_item, reference_to_move[0].text, reference_to_move[1].text))==0)
                        print(reference_to_move)
                        print(destination_item)
                        if reference_to_move is not None:
                           print(reference_to_move[0].text)
                           print(reference_to_move[1].text)
                        if reference_to_move==None or len(find_all_references(destination_item, reference_to_move[0].text, reference_to_move[1].text))==0:
                                destination_item[0].append(new_reference)
                                # ...and we update the entry for the destination topic in our array.
                                update_list_of_topic_groups(destination_item, 
                                   destination_group_item_agency_id,
                                   destination_group_item_identifier,
                                   destination_group_item_version,
                                   topic_type,
                                   updated_topic_groups,
                                   #reference_to_add=new_reference,
                                   dataset=topic_reassignment_details.iloc[3]
                             )
        else:
                if len(references_to_move)==0:
                    print((f"Item {topic_reassignment_details.iloc[0]} "
                            f" is not in topic "
                            f"{topic_reassignment_details.iloc[1]}"))
                    item_not_present_in_source_topic.append(
                            (topic_reassignment_details.iloc[0], topic_reassignment_details.iloc[1]))
                if reference_in_destination_topic is not None:
                    print((f"Item {topic_reassignment_details.iloc[0]} "
                            f" is already in topic "
                            f"{topic_reassignment_details.iloc[2]}"))
                    item_present_in_destination_topic.append(
                            (topic_reassignment_details.iloc[0], topic_reassignment_details.iloc[2]))
                if len(references_to_move)==0 and reference_in_destination_topic is not None:
                    delThis.append(topic_reassignment_details)
    number_of_topic_reassignments_already_performed = len([x for x in item_not_present_in_source_topic
                                           if x in item_present_in_destination_topic])
    number_of_topic_reassignments_to_be_performed = len(topic_reassignments_data_frame) - number_of_topic_reassignments_already_performed
    print(f"{number_of_topic_reassignments_already_performed} of {len(topic_reassignments_data_frame)} topic" 
          f" reassignments in the input file have already been performed,")
    print(f"{number_of_topic_reassignments_to_be_performed} pair(s) of DDI Fragments implementing topic"
           " reassignments specified in the input file have been created.")            
    if (len(item_not_present_in_source_topic) == len(topic_reassignments_data_frame) and
       len(item_present_in_destination_topic) == len(topic_reassignments_data_frame)):
       print("The item topic reassignments in the input data file have already all been "
             "successfully executed.")
    return ([x[0] for x in item_not_present_in_source_topic
                                           if x[0] in [y[0] for y in item_present_in_destination_topic]], 
                                           updated_topic_groups,
                                           delThis, 
                                           item_not_present_in_source_topic, 
                                           item_present_in_destination_topic)

