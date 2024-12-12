from .lib.utility import get_namespace, 
    find_reference,
    create_variable_reference,
    get_current_state_of_topic_group,
    update_list_of_topic_groups

def update_topics(topic_reassignments_data_frame):
    """Method for reassigning items to new topics. The code iterates through a data frame
    containing details of new item topic assignments and performs the reassignments. 
    """
    # Initialise variables...
    item_not_present_in_source_topic = []
    item_present_in_destination_topic = []
    updated_topic_groups = []
    # Iterate through the rows in the data frame. Each row contains details of a topic
    # reassignment for a item...
    for topic_reassignment_details in topic_reassignments_data_frame.iloc:
        print("Performing the following topic reassignment...")
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
        if True:
                    # We get the state of the group containing a reference to the item.
                    # This group represents the topic the item is currently assigned
                    # to.
                    source_item = get_current_state_of_topic_group(
                                                       source_group['AgencyId'],
                                                       source_group['Identifier'],
                                                       updated_topic_groups,
                                                       version=source_group['Version']
                                                       )
                    # We get the current state of the group that we will be adding a
                    # reference to the item to. This group represents the topic the
                    # item will be reassigned to.
                    destination_item = get_current_state_of_topic_group(
                                                            destination_group['AgencyId'],
                                                            destination_group['Identifier'],
                                                            updated_topic_groups,
                                                            version=destination_group['Version']
                                                            )
                    # Find and remove the reference to the item in the source group/topic.
                    reference_to_move = find_reference(
                        source_item, item['AgencyId'], item['Identifier'])
                    # We check to see if a reference to the item is already present in the
                    # destination group/topic. This information can be used to determine if the
                    # topic reassignments described in the input file have already been
                    # successfully performed.
                    reference_in_destination_topic = find_reference(destination_item, 
                        item['AgencyId'], item['Identifier'])
                    if reference_to_move is not None and reference_in_destination_topic is None:
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
                        destination_ddi_version = ("ddi:reusable:"
                            f"{get_namespace(destination_item.tag).split(':')[2]}")
                        # If the namespace for the item reference from the group/topic
                        # that the item currently belongs to has a different DDI version than
                        # the group/topic that we want to add the reference to, we need
                        # to create a new version of the reference which has the same namespace as
                        # the group/topic we will be adding it to.
                        if reference_from_source_ddi_version != destination_ddi_version:
                            if item_type == '683889c6-f74b-4d5e-92ed-908c0a42bb2d':
                                new_reference = create_variable_reference(reference_to_move[0].text,
                                                                   reference_to_move[1].text,
                                                                   reference_to_move[2].text,
                                                                   reference_to_move[3].text,
                                                                   destination_ddi_version
                                                                   )
                            else:
                                new_reference = create_question_reference(referenceToRemove[0].text, 
                                                                   referenceToRemove[1].text,
                                                                   referenceToRemove[2].text,
                                                                   referenceToRemove[3].text,
                                                                   namespace,
                                                                   namespace2,
                                                                   tag_name
                                                                   )
                        else:
                            new_reference = reference_to_move
                        # Add the reference to the group representing the topic it is being 
                        # reassigned to.
                        destination_item[0].append(new_reference)
                        # Finally we update the array containing the most current versions of the
                        # group/topics. First we update the entry for the topic/group we
                        # removed a reference from...
                        update_list_of_topic_groups(source_item,
                           source_group['AgencyId'],
                           source_group['Identifier'],
                           source_group['Version'],
                           source_group['ItemType'],
                           updated_topic_groups)
                        # ...and then we update the entry for the topic/group we added a
                        # reference to.
                        update_list_of_topic_groups(destination_item, 
                           destination_group['AgencyId'],
                           destination_group['Identifier'],
                           destination_group['Version'],
                           source_group['ItemType'],
                           updated_topic_groups)
                    else:
                        if reference_to_move is None:
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
        else:
                print(f"A single instance of the item {topic_reassignment_details.iloc[1]} "
                      f"has not been found. Either none or multiple instances were found.")
    number_of_successful_topic_reassignments = len([x for x in item_not_present_in_source_topic
                                           if x in item_present_in_destination_topic])
    print(f"{number_of_successful_topic_reassignments} of {len(data)} items"
          f" were successfully assigned to new topics.")
    if (len(item_not_present_in_source_topic) == len(data) and
       len(item_present_in_destination_topic) == len(data)):
       print("The item topic reassignments in the input data file have already all been "
             "successfully executed.")
    return updated_topic_groups

    update_topics(df2)