from .lib.utility import get_urn_from_item, get_topic_of_item
#pip install openpyxl #might need to install openpyxl, a dependency for read-excel
import pandas as pd
   
def generate_urn_dataframe(input_file_name, C):
    """Method for reassigning items to new topics. The code iterates through a spreadsheet
    containing details of new variable topic assignments and generates a dataframe of URNs that
    can be used as input to a method defined in changeItemTopics.py that reassigns items to new
    topics. 
    """
    print(f"Reading topic reassignments from {input_file_name}")
    data = pd.read_excel(input_file_name)
    # Iterate through the rows in the spreadsheet. Each row contains details of a topic
    # reassignment for a variable...
    urnDataFrame={
        "itemUrns": [],
        "sourceTopicGroups": [],
        "destinationTopicGroups": []
    }
    for topic_reassignment_details in data.iloc:
        instrumentName = topic_reassignment_details.iloc[0]
        url = topic_reassignment_details.iloc[2]
        agency_id = url.split("/")[4]
        identifier = url.split("/")[5]
        if len(url.split("/")) == 7:
            version = url.split("/")[6]
            item = C.get_item_json(agency_id, identifier, version=version)
        else:
            item = C.get_item_json(agency_id, identifier)
        version = item['Version']
        itemUrn = "urn:ddi:" + agency_id + ":" + identifier + ":" + str(version)
        item_type = item['ItemType']
        topicName = item['ItemName']['en-GB']  
        if item_type==C.item_code('Question'):
            topic_type=C.item_code('Question Group')
            containing_item_type=C.item_code('Data Collection')
        elif item_type==C.item_code('Variable'):
            topic_type=C.item_code('Variable Group')
            containing_item_type=C.item_code('Data File')
        itemUrn = get_urn_from_item(item)    
        sourceTopic = get_topic_of_item(topic_reassignment_details.iloc[4], topic_type, instrumentName, containing_item_type, C)
        destinationTopic = get_topic_of_item(topic_reassignment_details.iloc[5], topic_type, instrumentName, containing_item_type, C)
        urnDataFrame['itemUrns'].append(itemUrn)
        if len(sourceTopic)>0:
            urnDataFrame['sourceTopicGroups'].append(get_urn_from_item(sourceTopic[0]))
        if len(destinationTopic)>0:
            urnDataFrame['destinationTopicGroups'].append(get_urn_from_item(destinationTopic[0])) 
    return pd.DataFrame(urnDataFrame)
