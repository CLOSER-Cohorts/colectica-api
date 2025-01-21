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

from .lib.utility import (
    get_namespace,
    find_reference,
    create_variable_reference,
    create_question_reference,
    get_current_state_of_topic_group,
    update_list_of_topic_groups
)
from .generate_urn_dataframe import generate_urn_dataframe 
import defusedxml

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
        # We get the state of the group containing a reference to the item.
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
        references_to_move = find_reference(
                        source_item, item['AgencyId'], item['Identifier'])
        # We check to see if a reference to the item is already present in the
        # destination group/topic. This information can be used to determine if the
        # topic reassignments described in the input file have already been
        # successfully performed.
        reference_in_destination_topic = find_reference(destination_item, 
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
                                                                   "Variable",
                                                                   destination_ddi_version_reusable
                                                                   )
                                else:
                                    new_reference = create_question_reference(item_agency_id,
                                                                   item_identifier,
                                                                   item_version,
                                                                   "QuestionItem",
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
                        if len(find_reference(destination_item, reference_to_move[0].text, reference_to_move[1].text))==0:
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
