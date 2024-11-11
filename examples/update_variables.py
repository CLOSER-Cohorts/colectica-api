"""A set of functions that reassign variables to new topics.
Use: python update_topics username password hostname(optional)

Hostname will default to the a default host if it is not specified.

The code can also detect if it is being called from the commandline as described
above or if it is being imported into another Python file/REPL session. The variables
for the username, password and hostname used to connect to a Colectica repository
are declared by different means in either case. The usage for changing variable topics 
from another Python file/REPL session is:

import examples.update_variables
examples.update_variables.update_topics()

"""
import sys
import pandas as pd
import defusedxml
from colectica_api import ColecticaObject
# pip install openpyxl #needed for read-excel, doesn't have to be executed every time,
# perhaps only the first time this script is run on a machine

if __name__ != '__main__':
    from .lib.utility import get_namespace, find_reference, create_variable_reference
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    HOSTNAME = "DEFAULT HOSTNAME"
    C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD,verify_ssl=False)

def get_current_state_of_item(agency_id, identifier, updated_groups, version=None):
    """Checks to see if an item has already been read into memory. If it has, that
    value stored in memory is returned. Otherwise a request is made to the REST API
    for the most recent version of that item."""
    updated_referencing_item = [x for x in updated_groups if x[0] == identifier]
    if len(updated_referencing_item) > 0:
        referencing_item = updated_referencing_item[0][4]
    else:
        fragment_xml = C.get_item_xml(
            agency_id, identifier, version=version)['Item']
        referencing_item = defusedxml.ElementTree.fromstring(fragment_xml)
    return referencing_item

def update_list_of_referencing_groups(item_without_reference, agency, identifier, version, 
                                      item_type, updated_refs_copy):
    """Update the list of items read into memory. If the item being updated is already in the
    list, we update that item with the new version. If not, we append the item to the list."""
    if ([x[0] for x in updated_refs_copy].count(identifier) > 0):
        index_of_updated_ref = [x[0] for x in updated_refs_copy].index(identifier)
        updated_refs_copy[index_of_updated_ref] = (
            identifier, agency, version, item_type, item_without_reference)
    else:
        updated_refs_copy.append(
            (identifier, agency, version, item_type, item_without_reference))

# Declare an array which will contain instances of the variable groups that represent topics that
# variables can be assigned to. We will be performing multiple updates to the groups, so instead of
# retrieving/updating/writing data using the Colectica REST API every time we update a variable
# group,the first time we need to update a variable group we will retrieve it from the Colectica
# repository using the Colectica REST API, store it in this array, and perform subsequent updates to
# the variable group (e.g. adding/removing references to variables) on the item stored in the array.
# Once we have made all the updates to the variable groups described in the input file
# Topics_to_be_changed-4-2024.xlsx, we will create a commit transaction using the Colectica REST
# API, add all the variable groups in this array to that transaction, and commit the transaction.

updatedReferencingGroups = []

# Iterate through the rows in the spreadsheet. Each row contains details of a topic reassignment for
# a variable...


def update_topics():
    """Main method for reassigning variables to new topics. The code reads a spreadsheet
    containing details of new variable topic assignments, iterates through the spreadsheet 
    and performs the reassignments. 
    """
    data = pd.read_excel("Topics_to_be_changed-4-2024.xlsx")
    for topic_reassignment_details in [data.iloc[0,]]:
        print("Performing the following topic reassignment...")
        print(topic_reassignment_details)
        # Search for the dataset item which contains the variable in the current row....
        physical_instance_containing_variable = C.search_item(
            'a51e85bb-6259-4488-8df2-f08cb43485f8', topic_reassignment_details.iloc[0].strip(), 0, 
               SearchLatestVersion=True)['Results']
        if len(physical_instance_containing_variable) == 1:
            # We need to search within the physical instance/dataset for the variable in the current
            # row. We create a JSON object representing the physical instance/dataset.
            search_sets = [{
                "agencyId": physical_instance_containing_variable[0]['AgencyId'],
                "identifier": physical_instance_containing_variable[0]['Identifier'],
                "version": physical_instance_containing_variable[0]['Version']
            }]
            # The 'SearchTerms' keyword argument represents the name of the variable. The 
            # 'SearchSets' keyword argument represents the physical instance/dataset we are
            # searching in.
            variables_metadata = C.search_items(C.item_code('Variable'), SearchSets=search_sets, 
               SearchTerms=[topic_reassignment_details.iloc[1].strip()])['Results']
            if len(variables_metadata) > 0:
                variable_agency_id = variables_metadata[0]['AgencyId']
                variable_identifier = variables_metadata[0]['Identifier']
                variable_version = variables_metadata[0]['Version']
                # Search for a variable group that references the variable we found, i.e. the 
                # variable group representing the topic that the variable has been assigned to
                all_source_group_identifiers = C.search_items(C.item_code('Variable Group'), 
                     SearchSets=search_sets, 
                     SearchTerms=[str(topic_reassignment_details.iloc[3])])['Results']
                # Each variable should only belong to one topic, so it should only be referenced by
                # one variable group. However we may find that a variable is referenced by more than
                # one variable group. This can happen if a variable has been mapped to multiple
                # topics in error, but it can also happen if a variable is referenced by a 
                # deprecated variable group.
                if len([x for x in all_source_group_identifiers 
                        if x['IsDeprecated'] is False]) == 1:
                    source_group_identifiers = all_source_group_identifiers[0]
                    # We need to search for the variable group representing the topic to which we
                    # want to assign the variable. Again, the 'SearchTerms' keyword argument
                    # represents the name of the variable group (note that it's a different column
                    # in the spreadsheet data than the name of the variable group that the variable 
                    # is currently in). The 'SearchSets' keyword argument represents the physical
                    # instance/dataset we are searching in, it's the same dataset we were searching
                    # in before.
                    destination_group_search_results = C.search_items(C.item_code('Variable Group'),
                        SearchSets=search_sets,
                        SearchTerms=[str(topic_reassignment_details.iloc[4])])['Results']
                    if len(destination_group_search_results) != 1:
                        print("Search for item representing destination group did not return a "
                              "single unique result")
                    destination_group = destination_group_search_results[0]
                    # We get the current state of the variable group currently containing a
                    # reference to the variable. This variable group represents the topic the
                    # variable is currently assigned to.
                    source_item = get_current_state_of_item(source_group_identifiers['AgencyId'],
                                                       source_group_identifiers['Identifier'],
                                                       updatedReferencingGroups,
                                                       version=source_group_identifiers['Version']
                                                       )
                    # We get the current state of the variable group that we will be adding a
                    # reference to the variable to. This variable group represents the topic the
                    # variable will be reassigned to.
                    destination_item = get_current_state_of_item(destination_group['AgencyId'],
                                                            destination_group['Identifier'],
                                                            updatedReferencingGroups,
                                                            version=destination_group['Version']
                                                            )
                    # Find and remove the reference to the variable in the variable group/topic.
                    reference_to_remove = find_reference(
                        source_item, variable_agency_id, variable_identifier)
                    # variable reference from the variable group/topic.
                    if reference_to_remove is not None:
                        source_item[0].remove(reference_to_remove)
                        # We need to get the namespace for the variable reference we will be adding
                        # to the variable group representing the topic we are re-assigning the
                        # variable to. This namespace begins with the text 'ddi:reusable:' and is
                        # followed by a version number for DDI, e.g. ddi:reusable:3_2,
                        # ddi:reusable:3_3. The DDI versions for the variable group/topic currently
                        # referencing a variable and the variable group/topic to which we want to
                        # reassign a variable to may be different, and we need to ensure that when
                        # creating a new variable reference, its namespace references the DDI
                        # version of the variable group we are adding it to, otherwise the variable
                        # group update will not work.
                        reference_from_source_ddi_version = reference_to_remove.tag
                        destination_ddi_version = f'ddi:reusable:{
                            get_namespace(destination_item.tag).split(":")[2]}'
                        # If the namespace for the variable reference from the variable group/topic
                        # that the variable currently belongs to has a different DDI version than
                        # the variable group/topic that we want to add the reference to, we cannot
                        # just add the reference 'as is', we need to create a new version of the
                        # reference which has a namespace using the DDI version of the variable
                        # group/topic we will be adding it to.
                        if reference_from_source_ddi_version != destination_ddi_version:
                            new_reference = create_variable_reference(reference_to_remove[0].text,
                                                                   reference_to_remove[1].text,
                                                                   reference_to_remove[2].text,
                                                                   reference_to_remove[3].text,
                                                                   destination_ddi_version
                                                                   )
                        else:
                            new_reference = reference_to_remove
                        # Add the variable reference to the variable group representing the topic it
                        # is being reassigned to.
                        destination_item[0].append(new_reference)
                        # Finally we update the array containing the most current version of the
                        # variable group/topics.
                        update_list_of_referencing_groups(source_item,
                           source_group_identifiers['AgencyId'],
                           source_group_identifiers['Identifier'],
                           source_group_identifiers['Version'],
                           C.item_code('Variable Group'),
                           updatedReferencingGroups)
                        update_list_of_referencing_groups(destination_item, 
                           destination_group['AgencyId'],
                           destination_group['Identifier'],
                           destination_group['Version'],
                           C.item_code('Variable Group'),
                           updatedReferencingGroups)
                    else:
                        print(f"Variable {topic_reassignment_details.iloc[3]} in dataset "
                              f"{topic_reassignment_details.iloc[0]} is not assigned to a single "
                              "topic")
            else:
                print(f"No dataset with alternate title {topic_reassignment_details[0]} found")
    return updatedReferencingGroups

if __name__ == '__main__':
    from lib.utility import get_namespace, find_reference, create_variable_reference
    USERNAME = sys.argv[1]
    PASSWORD = sys.argv[2]
    if len(sys.argv) == 4:
        HOSTNAME = sys.argv[3]
    else:
        HOSTNAME = "DEFAULT HOSTNAME"
    C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD,verify_ssl=False)
    update_topics()