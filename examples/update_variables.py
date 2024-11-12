"""A set of functions that reassign variables to new topics. This code assumes the existence of
a file called 'Topics_to_be_changed.xlsx' in the same directory as this file. The set of 
commands for changing variable topics is:

import examples.update_variables
updatedVariableGroups = examples.update_variables.update_topics()
examples.update_variables.update_repository(updatedVariableGroups, 'Repository commit message')

"""
import pandas as pd
import defusedxml
from colectica_api import ColecticaObject
from .lib.utility import get_namespace, find_reference, create_variable_reference
# pip install openpyxl
# The above install is needed for the pd.read-excel command, it doesn't have to be executed every
# time, perhaps only the first time this script is run on a machine

USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)

def get_current_state_of_topic_group(agency_id, identifier, updated_groups, version=None):
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

# Declare an array which will contain instances of the variable groups/topics.
updated_topic_groups = []

def update_topics():
    """Method for reassigning variables to new topics. The code iterates through a spreadsheet
    containing details of new variable topic assignments and performs the reassignments. 
    """
    data = pd.read_excel("Topics_to_be_changed.xlsx")
    # Iterate through the rows in the spreadsheet. Each row contains details of a topic
    # reassignment for a variable...
    for topic_reassignment_details in data.iloc:
        print("Performing the following topic reassignment...")
        print(topic_reassignment_details)
        # Search for the physical instance/dataset item which contains the variable in the current
        # row....
        physical_instance_containing_variable = C.search_item(
            'a51e85bb-6259-4488-8df2-f08cb43485f8', topic_reassignment_details.iloc[0].strip(), 0, 
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
            variables_metadata = C.search_items(C.item_code('Variable'), SearchSets=search_sets,
               SearchTerms=[topic_reassignment_details.iloc[1].strip()])['Results']
            if len(variables_metadata) > 0:
                variable_agency_id = variables_metadata[0]['AgencyId']
                variable_identifier = variables_metadata[0]['Identifier']
                variable_version = variables_metadata[0]['Version']
                # Search for a variable group that references the variable we found, i.e. the
                # variable group representing the topic that the variable is currently assigned to.
                all_source_group_identifiers = C.search_items(C.item_code('Variable Group'),
                     SearchSets=search_sets, 
                     SearchTerms=[str(topic_reassignment_details.iloc[3])])['Results']
                # Each variable should only belong to one topic, so it should only be referenced by
                # one variable group. However we may find that a variable is referenced by more than
                # one variable group. This can happen if a variable has been mapped to multiple
                # topics in error, but it can also happen if a variable is referenced by a
                # deprecated variable group.
                if len([x for x in all_source_group_identifiers if x['IsDeprecated']
                        is False]) == 1:
                    source_group_identifiers = all_source_group_identifiers[0]
                    # We need to search for the variable group representing the new topic to which
                    # we want to assign the variable. The 'SearchTerms' keyword argument represents
                    # the name of the variable group (note that it's a different column in the
                    # spreadsheet data than the name of the variable group that the variable
                    # is currently in). The 'SearchSets' keyword argument represents the physical
                    # instance/dataset we are searching in for that topic/variable group; it's the
                    # same dataset we were searching for the variable in previously.
                    destination_group_search_results = C.search_items(C.item_code('Variable Group'),
                        SearchSets=search_sets,
                        SearchTerms=[str(topic_reassignment_details.iloc[4])])['Results']
                    if len(destination_group_search_results) != 1:
                        print("Search for item representing destination group did not return a "
                              "single unique result")
                    destination_group = destination_group_search_results[0]
                    # We get the state of the variable group containing a reference to the variable.
                    # This variable group represents the topic the variable is currently assigned
                    # to.
                    source_item = get_current_state_of_topic_group(
                                                       source_group_identifiers['AgencyId'],
                                                       source_group_identifiers['Identifier'],
                                                       updated_topic_groups,
                                                       version=source_group_identifiers['Version']
                                                       )
                    # We get the current state of the variable group that we will be adding a
                    # reference to the variable to. This variable group represents the topic the
                    # variable will be reassigned to.
                    destination_item = get_current_state_of_topic_group(
                                                            destination_group['AgencyId'],
                                                            destination_group['Identifier'],
                                                            updated_topic_groups,
                                                            version=destination_group['Version']
                                                            )
                    # Find and remove the reference to the variable in the source group/topic.
                    reference_to_move = find_reference(
                        source_item, variable_agency_id, variable_identifier)
                    if reference_to_move is not None:
                        source_item[0].remove(reference_to_move)
                        # We need to get the namespaces for the variable reference and the variable
                        # group representing the topic we are re-assigning the variable to. These
                        # namespaces begin with the text 'ddi:reusable:' and are followed by a
                        # version number for DDI, e.g. ddi:reusable:3_2, ddi:reusable:3_3. The DDI
                        # versions for the variable group/topic currently referencing a variable
                        # and the DDI version for the variable group/topic to which we want to
                        # reassign a variable to may be different. We need to ensure that when
                        # adding a new variable reference to a topic, they both have the same
                        # namespace, otherwise the variable group update will not work.
                        reference_from_source_ddi_version = reference_to_move.tag
                        destination_ddi_version = f'ddi:reusable:{
                            get_namespace(destination_item.tag).split(":")[2]}'
                        # If the namespace for the variable reference from the variable group/topic
                        # that the variable currently belongs to has a different DDI version than
                        # the variable group/topic that we want to add the reference to, we need
                        # to create a new version of the reference which has the same namespace as
                        # the variable group/topic we will be adding it to.
                        if reference_from_source_ddi_version != destination_ddi_version:
                            new_reference = create_variable_reference(reference_to_move[0].text,
                                                                   reference_to_move[1].text,
                                                                   reference_to_move[2].text,
                                                                   reference_to_move[3].text,
                                                                   destination_ddi_version
                                                                   )
                        else:
                            new_reference = reference_to_move
                        # Add the variable reference to the variable group representing the topic it
                        # is being reassigned to.
                        destination_item[0].append(new_reference)
                        # Finally we update the array containing the most current versions of the
                        # variable group/topics. First we update the entry for the topic/variable
                        # group we removed a reference from...
                        update_list_of_topic_groups(source_item,
                           source_group_identifiers['AgencyId'],
                           source_group_identifiers['Identifier'],
                           source_group_identifiers['Version'],
                           C.item_code('Variable Group'),
                           updated_topic_groups)
                        # ...and then we update the entry for the topic/variable group we added a reference
                        # to.
                        update_list_of_topic_groups(destination_item, 
                           destination_group['AgencyId'],
                           destination_group['Identifier'],
                           destination_group['Version'],
                           C.item_code('Variable Group'),
                           updated_topic_groups)
                    else:
                        print(f"Variable {topic_reassignment_details.iloc[3]} in dataset "
                              f"{topic_reassignment_details.iloc[0]} is not assigned to a single "
                              "topic")
            else:
                print(f"No dataset with alternate title {topic_reassignment_details[0]} found")
    return updated_topic_groups

# Once we have made all the updates to the variable groups described in the input file
# Topics_to_be_changed.xlsx, we can use the update_repository function to create a
# transaction using the Colectica REST API, add all the variable groups in this array to that
# transaction, and finally commit the transaction.

def update_repository(updated_items, transaction_message):
    """Update a set of Variable Group items in the repository."""
    transaction_response = C.create_transaction()
    transaction_id = transaction_response['TransactionId']
    for item in updated_items:
        fragment_string = defusedxml.ElementTree.tostring(item[4], encoding='unicode')
        C.add_items_to_transaction(item[1], item[0], item[2], fragment_string, 
                                   C.item_code('Variable Group'), transaction_id)
        commit_response = C.commit_transaction(transaction_id, transaction_message, 3)
    return commit_response
