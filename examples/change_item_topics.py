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
    get_current_state_of_topic_group,
    update_list_of_topic_groups,
    get_urn_from_item,
    get_item_from_topic_name,
    create_group,
    create_group_reference
)
import defusedxml
#pip install openpyxl #might need to install openpyxl, a dependency for read-excel
import pandas as pd
import uuid
from collections import Counter

language = "en-GB"

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

def get_level_zero_group_2(agencyId, Identifier, version, item_type, C):
    level_zero_group = C.search_relationship_bysubject(agencyId, identifier, Version=version, 
               item_types=[item_type])[0]
    item_element = defusedxml.ElementTree.fromstring(level_zero_group['Item'])
    return (agencyId, Identifier, item_element)


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


#GET A FUNCTION THAT GETS THE UNIQUE LEVEL ONE AND LEVEL TWO GROUPS WE NEED TO CREATE
#ITERATE THRU THE L1s. CREATE EACH L1 (MIGHT HAVE TO DO LEVEL ZERO STUFF). FIND EACH L2 WHICH IS IN 
#THE SAME DATASET, CREATE IT, THEN ADD A REFERENCE TO THE L1 FOR THAT L2


def create_topics(input_file_name, C):
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
    updated_topic_groups = []
    level_zero_groups=[]
    for topic_reassignment_details in data.iloc:
        print(count)
        count=count+1
        url = topic_reassignment_details.iloc[2]
        agency_id = url.split("/")[4]
        identifier = url.split("/")[5]
        if len(url.split("/")) == 7:
            version = url.split("/")[6]
            item = C.get_item_xml(agency_id, identifier, version=version)
        else:
            item = C.get_item_xml(agency_id, identifier)
        version = item['Version']
        item_type = item['ItemType']
        item_agency_id = item['AgencyId']
        if item_type==C.item_code('Question'):
            topic_type=C.item_code('Question Group')
            containing_item_type=C.item_code('Data Collection')
        elif item_type==C.item_code('Variable'):
            topic_type=C.item_code('Variable Group')
            containing_item_type=C.item_code('Data File')
        containing_item_name = topic_reassignment_details.iloc[0]
        item_urn = get_urn_from_item(item)
        physical_instance_containing_variable = C.search_items(
                    containing_item_type,
                    SearchTerms=str(containing_item_name).strip(),
                    SearchLatestVersion=True)['Results'][0]
        physical_instance_search_set = [{
                "agencyId": physical_instance_containing_variable['AgencyId'],
                "identifier": physical_instance_containing_variable['Identifier'],
                "version": physical_instance_containing_variable['Version']
            }]
        source_topic = C.search_relationship_byobject(agency_id, identifier, Version=version, item_types=[topic_type])
        if len(source_topic)>0:
           source_topic_item=C.get_item_json(source_topic[0]['Item1']['Item3'], source_topic[0]['Item1']['Item1'],
           version=source_topic[0]['Item1']['Item2'])
           print(source_topic_item['ItemName'][language])
           print(str(topic_reassignment_details.iloc[4]))           
           if source_topic_item['ItemName'][language]==str(topic_reassignment_details.iloc[4]):
              level_zero_group=get_level_zero_group(source_topic_item, topic_type, C)
              source_topic_urn=get_urn_from_item(source_topic_item)
        else:
           level_zero_group_details=C.search_relationship_bysubject(physical_instance_containing_variable['AgencyId'], 
              physical_instance_containing_variable['Identifier'], 
              Version=physical_instance_containing_variable['Version'], 
              item_types=[C.item_code('Variable Group')])
           level_zero_group_item=C.get_item_xml(level_zero_group_details[0]['Item1']['Item3'],
                level_zero_group_details[0]['Item1']['Item1'],
                version=level_zero_group_details[0]['Item1']['Item2'])['Item']
           level_zero_group=defusedxml.ElementTree.fromstring(level_zero_group_item)     
           source_topic_urn="" 
        destination_topic = get_item_from_topic_name(topic_reassignment_details.iloc[5], 
            topic_type, physical_instance_search_set, C)
        if len(destination_topic)==0:
                #you'll have to rewrite create group it needs to actually create the group
                # NEED TO GET NAMESPACE
                level_one_group_name = str(topic_reassignment_details.iloc[5])[0:3]
                if len(str(topic_reassignment_details.iloc[5]))==5:
                    level_two_group_name = str(topic_reassignment_details.iloc[5])
                else:
                    level_two_group_name = ""
                item_element = defusedxml.ElementTree.fromstring(item['Item'])
                namespace_version = get_namespace(item_element.tag).split(':')[2]
                print(topic_type)
                print(level_one_group_name)
                print(physical_instance_search_set)
                levelOneGroups=C.search_items(topic_type, 
                                   SearchTerms=[level_one_group_name], 
                                   SearchTargets=["Name"],
                                   SearchSets=physical_instance_search_set)['Results']
                if len(levelOneGroups)==0:
                    #level_two_group_uuid=str(uuid.uuid4())
                    #level_two_group_label=get_group_label(level_two_group_name, topic_type, C)
                    #level_two_group_object=create_group(level_two_group_name, 
                    #     level_two_group_label, level_two_group_uuid, namespace_version)
                    if (topic_reassignment_details.iloc[0], 
                        level_one_group_name) not in [(x[0], x[1]) for x in levelOneGroupsToCreate]:
                       levelOneGroupsToCreate.append((topic_reassignment_details.iloc[0],
                           level_one_group_name, level_zero_group_item, namespace_version))       
                    # YOU NOW NEED TO GET THE LEVEL ONE GROUP AND ADD A REFERENCE TO IT,
                    # TO THE LEVEL TWO GROUP. WHAT IF LEVEL ONE DOES NOT EXIST?
                    #level_two_group_reference=create_group_reference('uk.closer', level_two_group_uuid, 
                    # 1, namespace_version, topic_type, C)
                    #if level_zero_group is not None:
                    #   level_zero_group.append(level_two_group_reference)
                    if level_two_group_name!="" and (topic_reassignment_details.iloc[0], 
                        level_two_group_name) not in [(x[0], x[1]) for x in levelTwoGroupsToCreate]:
                   #level_three_group_uuid=str(uuid.uuid4())
                   #level_three_group_label=get_group_label(level_three_group_name, 
                   #   topic_type, C)
                   #level_three_group_object=create_group(level_three_group_name, 
                   #     level_three_group_label, level_three_group_uuid, namespace_version)
                   #reference_to_level_three_group=create_group_reference('uk.closer', level_three_group_uuid, 1, namespace_version, topic_type, C)
                   #level_two_group_object[0].append(reference_to_level_three_group)
                       levelTwoGroupsToCreate.append((topic_reassignment_details.iloc[0],
                           str(topic_reassignment_details.iloc[5]), namespace_version))
                else:
                    for group in levelOneGroups:
                        levelOneGroupsToModify.append((level_one_group_name, 
                                              level_two_group_name, 
                                              topic_type,
                                              group,
                                              namespace_version))
                        # 1, namespace_version, topic_type, C)
                     #   fragment_xml = C.get_item_xml(group['AgencyId'], 
                     #         group['Identifier'], version=group['Version'])['Item']
                      #  level_two_group_object = defusedxml.ElementTree.fromstring(fragment_xml)
    #return (list(set(levelOneGroupsToCreate)), list(set(levelTwoGroupsToCreate)), levelOneGroupsToModify) 
    return (levelOneGroupsToCreate, levelTwoGroupsToCreate, levelOneGroupsToModify) 

for topic in topics_to_create[0]:
   print("WER: " + str(topic))
   print([x for x in topics_to_create[1] if x[0]==topic[0] and x[1][0:3]==topic[1]])


level_one_topics_to_create=list(set(topics_to_create[0]))
level_two_topics_to_create=list(set(topics_to_create[1]))

count=0
for x in topics_to_create[0]:
   if x is None:
         print(count)
   else: 
         print(x)
   count=count+1 

LEVEL ZERO OBJECTS SHOULDN'T BE IN TOPICS TO CREATE. YOU NEED TO USE THE 
GET CURRENT STATE OF TOPICS LIST/UPDATE TOPICS LIST FUNCTIONS (OR SOMETHING
SIMILAR)

THIS CODE CREATES THE NEW TOPIC GROUPS AND UPDATES THE LEVEL ZERO TOPIC GROUPS

ddiObjectsLevelZero=[]
ddiObjectsLevelOne=[]
ddiObjectsLevelTwo=[]
tempArray=[]
for topic in topics_to_create[0]:
   print(topic[1])
   level_one_group_uuid=str(uuid.uuid4())
   level_one_group_name=topic[1]
   topic_type=C.item_code('Variable Group')
   if type(topic[2]) is list:
        level_zero_group_urn=f"urn:ddi:{topic[2][0]['Item1']['Item3']}:{topic[2][0]['Item1']['Item1']}:{str(topic[2][0]['Item1']['Item3'])}"
   else:       
        level_zero_group_urn=topic[2][0][0].text
   zero_group_agency_id = level_zero_group_urn.split(":")[2]
   zero_group_identifier = level_zero_group_urn.split(":")[3]
   zero_group_version = level_zero_group_urn.split(":")[4]
   level_zero_group_object = get_current_state_of_topic_group(zero_group_agency_id, 
       zero_group_identifier, ddiObjectsLevelZero, C, version=zero_group_version)     
   namespace_version=topic[3]   
   level_one_group_label=get_group_label(level_one_group_name, topic_type, C)
   level_one_group_object=create_group(level_one_group_name, 
       level_one_group_label, level_one_group_uuid, namespace_version)
   level_one_group_reference=create_group_reference('uk.closer', level_one_group_uuid, 1, namespace_version, topic_type, C)
   level_zero_group_object.append(level_one_group_reference)
   update_list_of_topic_groups(level_zero_group_object,
                               zero_group_agency_id,
                               zero_group_identifier,
                               zero_group_version,
                               topic_type,
                               ddiObjectsLevelZero)
   #if level_zero_group is not None:
   #     level_zero_group.append(level_one_group_reference)
   #     ddiObjectsLevelZero.append(level_zero_group) 
   level_two_groups=[x for x in topics_to_create[1] if x[0]==topic[0] and x[1][0:3]==topic[1]]
   #tempArray=tempArray+level_two_groups 
   for level_two_group in level_two_groups:
       level_two_group_uuid=str(uuid.uuid4())
       level_two_group_name=level_two_group[1]
       level_two_group_label=get_group_label(level_two_group_name, 
          topic_type, C)
       level_two_group_object=create_group(level_two_group_name, 
          level_two_group_label, level_two_group_uuid, namespace_version)
       reference_to_level_two_group=create_group_reference('uk.closer', level_two_group_uuid, 1, 
           namespace_version, topic_type, C)
       level_one_group_object[0].append(reference_to_level_two_group)
       ddiObjectsLevelTwo.append(level_two_group_object)
   ddiObjectsLevelOne.append((level_one_group_object, topic[0], topic[2]))


YOU WANT TO VERIFY:

1. ALL LEVEL TWO TOPICS ARE REFERENCED BY A LEVEL ONE TOPIC, WHICH IN TURN IS REFERENCED BY A 
LEVEL ZERO TOPIC

2. ALL LEVEL ONE TOPICS ARE REFERENCED BY A LEVEL ZERO TOPIC

THE BELOW CODE IMPLEMENTS CHECK 1

levelTwoIdentifiers=[x[0][2].text for x in ddiObjectsLevelTwo]
levelOneIdentifiers=[x[0][2].text for x in ddiObjectsLevelOne]
referencesValidatedIdentifiers=[x[0][2].text for x in referencesValidated]
referencesValidated=[]
levelTwoNotInOne=[]
for x in ddiObjectsLevelTwo:
    identifier = x[0][2].text
    print("LEVEL TWO: " + identifier)
    for y in ddiObjectsLevelOne:
        level_one_refs=find_all_references(y[0], 'uk.closer', identifier)
        if len(level_one_refs)==1:
            print("LEVEL TWO REFERENCE FOUND IN LEVEL ONE")
            level_one_identifier=y[0][0][2].text
            for z in [z1['Item'] for z1 in ddiObjectsLevelZero]:
                level_zero_refs=find_all_references(z, 'uk.closer', level_one_identifier)
                if len(level_zero_refs)>0:
                    print("LEVEL ONE REFERENCE FOUND IN LEVEL ZERO")
                    referencesValidated.append(y)
            

THE BELOW CODE IMPLEMENTS CHECK 2

forChecking2=[]
for x in topics_to_create[0]:
    physicalInstanceLabel=C.search_items(
                    C.item_code('Data File'),
                    SearchTerms=str(x[0]).strip(),
                    SearchLatestVersion=True)['Results'][0]['Label']['en-GB']
    forChecking2.append((x[1], x[0], physicalInstanceLabel))


forChecking=[]
referencesValidated3=[]
for y in ddiObjectsLevelOne:
            level_one_identifier=y[0][0][2].text
            for z in [z1 for z1 in ddiObjectsLevelZero]:
                level_zero_refs=find_all_references(z['Item'], 'uk.closer', level_one_identifier)
                if len(level_zero_refs)==1:
                    print("LEVEL ONE REFERENCE FOUND IN LEVEL  ZERO")
                    forChecking.append((get_element_by_name(y[0], 'VariableGroupName')['String'],
                    y[1],
                    get_element_by_name(z['Item'], 'Label')['Content']))
                    referencesValidated3.append(y)

datasets=C.search_relationship_byobject(z['AgencyId'], z['Identifier'], Version=z['Version'], item_types=[C.item_code('Data File')])
                    for d in datasets:
                        item=C.get_item_json(d['Item1']['Item3'], d['Item1']['Item1'], version=d['Item1']['Item2'])
                        if 'ItemName' in item.keys() and language in item['ItemName'].keys():
                            datasetName=item['ItemName'][language]
                            print("DATASET NAME: " + datasetName)
                    
                    

refsValidatedIds=[]
for x in referencesValidated:
   group_urn=x[0][0].text
   #zero_group_agency_id = level_zero_group_urn.split(":")[2]
   zero_group_identifier = group_urn.split(":")[3]
   #zero_group_version = level_zero_group_urn.split(":")[4]
   refsValidatedIds.append(zero_group_identifier)



refsValidatedIds2=[]
for x in ddiObjectsLevelOne:
   group_urn=x[0][0].text
   #zero_group_agency_id = level_zero_group_urn.split(":")[2]
   zero_group_identifier = group_urn.split(":")[3]
   #zero_group_version = level_zero_group_urn.split(":")[4]
   refsValidatedIds2.append(zero_group_identifier)

refsValidatedIds=[]
for x in referencesValidated:
   group_urn=x[0][0].text
   #zero_group_agency_id = level_zero_group_urn.split(":")[2]
   zero_group_identifier = group_urn.split(":")[3]
   #zero_group_version = level_zero_group_urn.split(":")[4]
   refsValidatedIds.append(zero_group_identifier)

len(list(set([(x[0], x[1]) for x in topics_to_create[0]])))
len(list(
    set([(x[1], x[2], x[3]['AgencyId'], x[3]['Identifier'], x[3]['Version']) for x in topics_to_create[2]])))


uniqueL1GroupsToModify=list(
    set([(x[1], x[2], x[3]['AgencyId'], x[3]['Identifier'], x[3]['Version']) for x in topics_to_create[2]]))

new_l2_topics=[]
modified_l1_topics=[]
for x in uniqueL1GroupsToModify:
    level_one_group_object = get_current_state_of_topic_group(x[2], 
       x[3], modified_l1_topics, C, version=x[4])
    level_two_group_uuid=str(uuid.uuid4())
    level_two_group_name=x[0]
    topic_type=x[1]
    level_two_group_label=get_group_label(level_two_group_name, topic_type, C)
    level_two_group_object=create_group(level_two_group_name, 
          level_two_group_label, level_two_group_uuid, namespace_version)
    reference_to_level_two_group=create_group_reference('uk.closer', level_two_group_uuid, 1, 
        namespace_version, topic_type, C)
    level_one_group_object[0].append(reference_to_level_two_group)
    update_list_of_topic_groups(level_one_group_object,
                               x[2],
                               x[3],
                               x[4],
                               topic_type,
                               modified_l1_topics)
    new_l2_topics.append(level_two_group_object)
       
To test: 

ddiObjectsLevelOne=[]
ddiObjectsLevelTwo=[]

we need to verify that the set of groups in ddiObjectsLevelOne is the same as in
topics_to_create[0], and that the set of groups in ddiObjectsLevelTwo is the same as in
topics_to_create[1]. We need to verify that the level zero group for the dataset
associated with the level one group contains a reference to the new level one group.
We need to verify for the level two groups that their corresponding level one group
contains a reference to them.

for x in topics_to_create[0]:
    level_zero_group=

level_two_group_uuid=str(uuid.uuid4())
                        level_two_group_label=get_group_label(level_two_group_name, 
                            topic_type, C)
                        level_two_group_object=create_group(level_two_group_name, 
                            level_two_group_label, level_two_group_uuid, namespace_version)
                        reference_to_level_two_group=create_group_reference('uk.closer', 
                           level_two_group_uuid, 1, namespace_version, topic_type, C)
                        modifiedGroup=group[0].append(reference_to_level_two_group)

   reference_to_level_two_group=create_group_reference('uk.closer', group['Identifier'], group['Version'],
                           topic_type, C)
                        level_one_groups_to_modify.append(group, reference_to_level_one_group)
                                         

missing=[]
tempArray2=[(x[0], x[1]) for x in tempArray]        
for topic in topics_to_create[1]:
    if (topic[0], topic[1]) not in tempArray2:
        print(topic)
        missing.append(topic)            
   print([x for x in level_two_topics_to_create if x[0]==topic[0] and x[1][0:3]==topic[1]])

list(set([(x[0], x[1][0:3]) for x in missing])) THESE ARE GROUPS TO WHICH WE NEED TO ADD
YOU NEED TO WORK THROUGH 

   

def generate_urn_dataframe(input_file_name, C):
    """Method for generating input for code that updates topics. The code iterates through 
    a spreadsheet containing details of new item topic assignments and generates a dataframe
    of URNs that can be used as input to a method that reassigns items to new topics. 
    """
    print(f"Reading topic reassignments from {input_file_name}")
    data = pd.read_excel(input_file_name)
    urn_data_frame={
        "itemUrns": [],
        "sourceTopicGroups": [],
        "destinationTopicGroups": []
    }
    count=1
    groupsToCreate=[]
    # Iterate through the rows in the spreadsheet. Each row contains details of a topic
    # reassignment for an item...
    for topic_reassignment_details in data.iloc:
        print(count)
        count=count+1
        containing_item_name = topic_reassignment_details.iloc[0]
        url = topic_reassignment_details.iloc[2]
        agency_id = url.split("/")[4]
        identifier = url.split("/")[5]
        if len(url.split("/")) == 7:
            version = url.split("/")[6]
            item = C.get_item_xml(agency_id, identifier, version=version)
        else:
            item = C.get_item_xml(agency_id, identifier)
        version = item['Version']
        item_urn = "urn:ddi:" + agency_id + ":" + identifier + ":" + str(version)
        item_type = item['ItemType']
        item_agency_id = item['AgencyId']
        if item_type==C.item_code('Question'):
            topic_type=C.item_code('Question Group')
            containing_item_type=C.item_code('Data Collection')
        elif item_type==C.item_code('Variable'):
            topic_type=C.item_code('Variable Group')
            containing_item_type=C.item_code('Data File')
        item_urn = get_urn_from_item(item)
        physical_instance_containing_variable = C.search_items(
                    containing_item_type,
                    SearchTerms=str(containing_item_name).strip(),
                    SearchLatestVersion=True)['Results']
        source_topic = get_item_from_topic_name(topic_reassignment_details.iloc[4], topic_type, physical_instance_containing_variable, C)
        print(source_topic)
        if len(source_topic)>0:
           level_zero_group=get_level_zero_group(source_topic[0], topic_type, C)
           source_topic_urn=get_urn_from_item(source_topic[0])
        else:
           level_zero_group=None
           source_topic_urn="" 
        destination_topic = get_item_from_topic_name(topic_reassignment_details.iloc[5], topic_type, physical_instance_containing_variable, C)
        if len(destination_topic)==0:
                #you'll have to rewrite create group it needs to actually create the group
                # NEED TO GET NAMESPACE
                level_two_group_name = str(topic_reassignment_details.iloc[5])[0:3]
                if len(str(topic_reassignment_details.iloc[5]))==5:
                    level_three_group_name = str(topic_reassignment_details.iloc[5])
                else:
                    level_three_group_name = ""
                item_element = defusedxml.ElementTree.fromstring(item['Item'])
                namespace_version = get_namespace(item_element.tag).split(':')[2]
                levelTwoGroups=C.search_items(topic_type, 
                                   SearchTerms=[level_two_group_name], 
                                   SearchTargets=["Name"],
                                   SearchSets=physical_instance_containing_variable)['Results']
                if len(levelTwoGroups)==0:
                    level_two_group_uuid=str(uuid.uuid4())
                    level_two_group_label=get_group_label(level_two_group_name, topic_type, C)
                    level_two_group_object=create_group(level_two_group_name, 
                         level_two_group_label, level_two_group_uuid, namespace_version)  
                    # YOU NOW NEED TO GET THE LEVEL ONE GROUP AND ADD A REFERENCE TO IT,
                    # TO THE LEVEL TWO GROUP. WHAT IF LEVEL ONE DOES NOT EXIST?
                    level_two_group_reference=create_group_reference('uk.closer', level_two_group_uuid, 1, namespace_version, topic_type, C)
                    print(level_zero_group)
                    if level_zero_group is not None:
                       level_zero_group.append(level_two_group_reference)   
                else:
                    for group in levelTwoGroups:
                        fragment_xml = C.get_item_xml(group['AgencyId'], 
                              group['Identifier'], version=group['Version'])['Item']
                        level_two_group_object = defusedxml.ElementTree.fromstring(fragment_xml)
                if level_three_group_name!="":
                   level_three_group_uuid=str(uuid.uuid4())
                   level_three_group_label=get_group_label(level_three_group_name, 
                      topic_type, C)
                   level_three_group_fragment=create_group(level_three_group_name, 
                        level_three_group_label, level_three_group_uuid, namespace_version)
                   reference_to_level_three_group=create_group_reference('uk.closer', level_three_group_uuid, 1, namespace_version, topic_type, C)
                   print(level_two_group_object)
                   level_two_group_object[0].append(reference_to_level_three_group)
                if len(str(topic_reassignment_details.iloc[5]))==5:
                    print(level_three_group_fragment)
                    destination_group_urn = f"urn:ddi:uk.closer:{level_three_group_uuid}:1"
                else:
                    destination_group_urn = f"urn:ddi:uk.closer:{level_two_group_uuid}:1"
        else:
            destination_group_urn = get_urn_from_item(destination_topic[0])
        urn_data_frame['itemUrns'].append(item_urn)
        urn_data_frame['sourceTopicGroups'].append(source_topic_urn)
        urn_data_frame['destinationTopicGroups'].append(destination_group_urn)
    print(groupsToCreate)
    for group in groupsToCreate:
        create_group(group[0], group[1])
    print(urn_data_frame)
    return pd.DataFrame(urn_data_frame)

def update_topics(input_file_name, C):
    """Method for reassigning items to new topics. The code iterates through a data frame
    containing details of new item topic assignments and performs the reassignments. 
    """
    topic_reassignments_data_frame=generate_urn_dataframe(input_file_name, C)
    # Initialise lists...
    item_not_present_in_source_topic = []
    item_present_in_destination_topic = []
    updated_topic_groups = []
    # Iterate through the rows in the data frame. Each row contains details of a topic
    # reassignment for a item...
    for topic_reassignment_details in topic_reassignments_data_frame.iloc:
        print("Performing the following topic reassignment...")
        print(f"Item {topic_reassignment_details.iloc[0]} to {topic_reassignment_details.iloc[1]}")
        topic_reassignment_details.iloc[0]
        item_agency_id = topic_reassignment_details.iloc[0].split(":")[2]
        item_identifier = topic_reassignment_details.iloc[0].split(":")[3]
        item_version = topic_reassignment_details.iloc[0].split(":")[4]        
        source_group_item_agency_id = topic_reassignment_details.iloc[1].split(":")[2]
        source_group_item_identifier = topic_reassignment_details.iloc[1].split(":")[3]
        source_group_item_version = topic_reassignment_details.iloc[1].split(":")[4]
        destination_group_item_agency_id = topic_reassignment_details.iloc[2].split(":")[2]
        destination_group_item_identifier = topic_reassignment_details.iloc[2].split(":")[3]
        destination_group_item_version = topic_reassignment_details.iloc[2].split(":")[4]
        item = C.get_item_json(item_agency_id, item_identifier, version = item_version)        
        source_group = C.get_item_json(source_group_item_agency_id,
            source_group_item_identifier,
            version = source_group_item_version)
        destination_group = C.get_item_json(destination_group_item_agency_id,
            destination_group_item_identifier,
            version = destination_group_item_version)
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
        # We get the current state of the group that we will be adding a
        # reference to the item to. This group represents the topic the
        # item will be reassigned to.
        destination_item = get_current_state_of_topic_group(
                                                            destination_group['AgencyId'],
                                                            destination_group['Identifier'],
                                                            updated_topic_groups,
                                                            C,
                                                            version=destination_group['Version']
                                                            )
        # Find and remove the reference to the item in the source group/topic.
        references_to_move = find_all_references(
                        source_item, item['AgencyId'], item['Identifier'])
        # We check to see if a reference to the item is already present in the
        # destination group/topic. This information can be used to determine if the
        # topic reassignments described in the input file have already been
        # successfully performed.
        reference_in_destination_topic = find_all_references(destination_item, 
                        item['AgencyId'], item['Identifier'])
        if len(references_to_move) > 0 and len(reference_in_destination_topic)==0:
                for reference_to_move in references_to_move:
                        source_item[0].remove(reference_to_move)
                        # We need to get the namespaces for the item reference and the
                        # group representing the topic we are re-assigning the item to. These
                        # namespaces begin with the text 'ddi:reusable:' and are followed by a
                        # version number for DDI, e.g. ddi:reusable:3_2, ddi:reusable:3_3. The DDI
                        # versions for the group/topic currently referencing a item
                        # and the DDI version for the group/topic to which we want to
                        # reassign a item to may be different. We need to ensure that when
                        # adding a new item reference to a topic, they both have the same
                        # namespace, otherwise the group update will not work.
                        reference_from_source_ddi_version = reference_to_move.tag
                        destination_ddi_version_reusable = ("ddi:reusable:"
                                f"{get_namespace(destination_item.tag).split(':')[2]}")
                        destination_ddi_version_datacollection = ("ddi:datacollection:"
                                f"{get_namespace(destination_item[0].tag).split(':')[2]}")    
                        # If the namespace for the item reference from the group/topic
                        # that the item currently belongs to has a different DDI version than
                        # the group/topic that we want to add the reference to, we need
                        # to create a new version of the reference which has the same namespace as
                        # the group/topic we will be adding it to.
                        if reference_from_source_ddi_version != destination_ddi_version_reusable:
                                if destination_group['ItemType'] == '91da6c62-c2c2-4173-8958-22c518d1d40d':
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
                        # Finally we update the array containing the most current versions of the
                        # group/topics. First we update the entry for the topic/group we
                        # removed a reference from...
                        update_list_of_topic_groups(source_item,
                               source_group['AgencyId'],
                               source_group['Identifier'],
                               source_group['Version'],
                               source_group['ItemType'],
                               updated_topic_groups)
                        # ...and then if the reference isn't already in the topic/group we are adding a
                        # reference to, we add the reference to the group representing the topic it is being 
                        # reassigned to...
                        if len(find_all_references(destination_item, reference_to_move[0].text, reference_to_move[1].text))==0:
                                destination_item[0].append(new_reference)
                                # ...and we update the entry for the destination topic in our array.
                                update_list_of_topic_groups(destination_item, 
                                   destination_group['AgencyId'],
                                   destination_group['Identifier'],
                                   destination_group['Version'],
                                   destination_group['ItemType'],
                                   updated_topic_groups)
        else:
                if len(references_to_move)==0:
                    print((f"Item {topic_reassignment_details.iloc[0]} "
                            f" is not in topic "
                            f"{topic_reassignment_details.iloc[1]}"))
                    item_not_present_in_source_topic.append(
                            topic_reassignment_details.iloc[1])
                if reference_in_destination_topic is not None:
                    print((f"Item {topic_reassignment_details.iloc[0]} "
                            f" is already in topic "
                            f"{topic_reassignment_details.iloc[2]}"))
                    item_present_in_destination_topic.append(
                            topic_reassignment_details.iloc[1])
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
    return updated_topic_groups

def verify_topic_group_structure(ddiObjectsLevelOne, ddiObjectsLevelTwo, topics_to_create, level_zero_groups=None):
    """
    Verifies the structure of topic groups after creation.
    1. Checks that ddiObjectsLevelOne matches topics_to_create[0].
    2. Checks that ddiObjectsLevelTwo matches topics_to_create[1].
    3. Verifies level zero group contains reference to new level one group.
    4. Verifies level one group contains reference to its level two groups.
    """
    results = {}
    # 1. Check set equality for level one groups
    set_ddi_l1 = set([getattr(obj, 'name', None) for obj in ddiObjectsLevelOne])
    set_topics_l1 = set([x[1] for x in topics_to_create[0]])
    results['level_one_groups_match'] = set_ddi_l1 == set_topics_l1

    # 2. Check set equality for level two groups
    set_ddi_l2 = set([getattr(obj, 'name', None) for obj in ddiObjectsLevelTwo])
    set_topics_l2 = set([x[1] for x in topics_to_create[1]])
    results['level_two_groups_match'] = set_ddi_l2 == set_topics_l2

    # 3. Verify level zero group contains reference to new level one group
    results['level_zero_group_references'] = []
    if level_zero_groups:
        for l1_obj, l0_group in zip(ddiObjectsLevelOne, level_zero_groups):
            found = False
            for ref in getattr(l0_group, 'references', []):
                if getattr(ref, 'target_uuid', None) == getattr(l1_obj, 'uuid', None):
                    found = True
                    break
            results['level_zero_group_references'].append(found)
    # 4. Verify level one group contains reference to its level two groups
    results['level_one_group_references'] = []
    for l1_obj in ddiObjectsLevelOne:
        l2_refs = []
        for ref in getattr(l1_obj, 'references', []):
            for l2_obj in ddiObjectsLevelTwo:
                if getattr(ref, 'target_uuid', None) == getattr(l2_obj, 'uuid', None):
                    l2_refs.append(getattr(l2_obj, 'name', None))
        results['level_one_group_references'].append(l2_refs)
    print('Verification Results:', results)
    return results
