def map_between_questions_and_variables(items, C):
    """Method for mapping between questions and variables.
    """
    related_items=[]
    # Iterate through the items...
    for item in items:
        agency_id = item.split(":")[2]
        identifier = item.split(":")[3]
        version = item.split(":")[4]
        itemJson = C.get_item_json(agency_id, identifier, version=version)
        item_type = C.item_code_inv(itemJson['ItemType'])
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





#disregard below
for x in questions:
    agency_id = x.split(":")[2]
    identifier = x.split(":")[3]
    version = x.split(":")[4]    
    question=C.get_item_xml(agency_id, identifier, version=version)
    destination_group_urn=


# get the question group a question is in. I need to modify
# code so it actually validates that q is in most recent version
# of group

item_urns=[]
source_group_urns=[]
destination_group_urns=[]
relatedQuestionGroups = getRelatedItemsByObject(relatedQuestion['AgencyId'], 
            relatedQuestion['Identifier'], relatedQuestion['Version'], C.item_code("Question Group")).json()
for relatedQuestionGroup in relatedQuestionGroups:
    relatedQuestionGroupMostRecentVersion=C.get_item_xml(relatedQuestionGroup['AgencyId'], relatedQuestionGroup['Identifier'])
    if relatedQuestion['Identifier'] in relatedQuestionGroupMostRecentVersion['Item']:
        group_urn = get_urn_from_item(relatedQuestionGroupMostRecentVersion)
        item_urns.append(x)
        source_group_urns.append(group_urn)


        
                 


get_topic_of_item(topic_name, topic_type, containing_item_name, containing_item_type, C)
            
            

