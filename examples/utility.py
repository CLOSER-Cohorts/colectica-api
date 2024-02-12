EXAMPLE: FIND THE ORPHANS

allResults=C.search_item(questionConstructIdentifier, '', 1)
questionConstructIdentifiers=[]
questionReferenceIDValues=[]
for x in allResults['Results']:
    questionConstructIdentifiers.append(x['Identifier'])
    fragmentXML = C.get_item_json(x['AgencyId'], x['Identifier'])['Item']    
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)  
    questionReferenceAgency=xmlTree.findall("./{ddi:datacollection:3_2}QuestionConstruct/{ddi:reusable:3_2}QuestionReference/{ddi:reusable:3_2}Agency")
    questionReferenceID=xmlTree.findall("./{ddi:datacollection:3_2}QuestionConstruct/{ddi:reusable:3_2}QuestionReference/{ddi:reusable:3_2}ID")
    questionReferenceVersion=xmlTree.findall("./{ddi:datacollection:3_2}QuestionConstruct/{ddi:reusable:3_2}QuestionReference/{ddi:reusable:3_2}Version")
    questionReferenceIDValues.append("urn:ddi:" + questionReferenceAgency[0].text + ":" + questionReferenceID[0].text + ":" + questionReferenceVersion[0].text)


questionItemIdentifiers=[]
questionItemUrnValues=[]

for x in allQuestionItemsMetadata['Results']:
    questionItemIdentifiers.append(x['Identifier'])
    fragmentXML = C.get_item_json(x['AgencyId'], x['Identifier'])['Item']    
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)  
    questionItemUrn=xmlTree.findall("./{ddi:datacollection:3_2}QuestionItem/{ddi:reusable:3_2}URN")
    questionItemUrnValues.append(questionItemUrn[0].text)

s = set(questionReferenceIdValuesList)
orphanQuestionItems = [x for x in questionItemUrnValuesList if x not in s]    

EXAMPLE: PROCESS ITEM TO GET ID FROM XML

for x in allQuestionItemsMetadata['Results'][45338:]:
    itemXML=C.get_item_json(x['AgencyId'], x['Identifier'])
    childItemIdentifiers=defusedxml.ElementTree.fromstring(itemXML['Item']).findall(".//{ddi:reusable:3_2}ID")
    (list(map(lambda x: itemIdentifiers.append(x.text), childItemIdentifiers)))

for x in orphanQuestionItems:
    itemXML=C.get_item_json(x.split(':')[2], x.split(':')[3])
    childItemIdentifiers=defusedxml.ElementTree.fromstring(itemXML['Item']).findall(".//{ddi:reusable:3_2}ID")
    (list(map(lambda x: orphanedItemIdentifiers.append(x.text), childItemIdentifiers)))
    
EXAMPLE: PROCESS XML

questionReferences=[]
for x in json_data:
    print(x['Variable']['Item1'])
    fragmentXML = C.get_item_xml(x['Variable']['Item3'], x['Variable']['Item1'], version=x['Variable']['Item2'])['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)  
    questionReferencesXML=xmlTree.findall("./{ddi:logicalproduct:3_2}Variable/{ddi:reusable:3_2}QuestionReference")
    for y in questionReferencesXML:
        agency = y.findall("./{ddi:reusable:3_2}Agency")
        id = y.findall("./{ddi:reusable:3_2}ID")
        version = y.findall("./{ddi:reusable:3_2}Version")
        typeOfObject = y.findall("./{ddi:reusable:3_2}TypeOfObject")
        print(typeOfObject[0].text)
        questionReferences.append(("urn:ddi:" + x['Variable']['Item3'] + ":" + x['Variable']['Item1'] + ":" + str(x['Variable']['Item2']), "urn:ddi:" + agency[0].text + ":" + id[0].text + ":" + version[0].text))
        print(len(questionReferences))
    
    

    for y in questionReferenceAgency:
        agency = y.findall("./{ddi:reusable:3_2}Agency")
        id = y.findall("./{ddi:reusable:3_2}ID")
        version = y.findall("./{ddi:reusable:3_2}Version")
        typeOfObject = y.findall("./{ddi:reusable:3_2}TypeOfObject")
        questionReferences.append("urn:ddi:" + agency[0].text + ":" + id[0].text + ":" + version[0].text)
        print(typeOfObject)

EXAMPLE DEPRECATING ITEM

def getDeprecateBody(agency_id, item_id, version):
        return {
        "ids": [
            {
            "agencyId": agency_id,
            "identifier": item_id,
            "version": version
            }
        ],
        "state": False,
        "applyToAllVersions": True
        }


def deprecateItem(agency_id, item_id, version):
    query=getDeprecateBody(agency_id, item_id, version)
    
    response = requests.post(
            "https://" + C.host + "/api/v1/item/_updateState",
            headers=C.token,
            json=query,
            verify=False
        )
    return response

EXAMPLE ADD ITEM TO TRANSACTION

        def addItemToTransaction(agency_id, item_id, version, transactionId, fragment):
    jsonBody=getJsonQueryForDeprecatingQuestionItems(agency_id, item_id, version, fragment)
    print(jsonBody)
    response = requests.post(
            "https://" + C.host + "/api/v1/transaction/_addItemsToTransaction",
            headers=C.token,
            json=jsonBody,
            verify=False
        )
    return response    

count=1
for x in orphanQuestionItemsList[1:2]:
    print(count)
    count=count+1
    agency=x.split(':')[2]
    id = x.split(':')[3]
    version = x.split(':')[4]
    fragmentXML = C.get_item_xml(agency, id, version=version)['Item']
    addItemToTransaction(agency, id, version, transactionId, fragmentXML)

def createTransaction():
    return requests.post(
            "https://" + C.host + "/api/v1/transaction",
            headers=C.token,
            json= {"transactionType": "CommitAsLatestWithLatestChildrenAndPropagateVersions"},
            verify=False
        )

EXAMPLE GET DDISET

def getDdiSet(agency, id, version):
    return requests.get(
            "https://" + C.host + "/api/v1/ddiset/" + agency + "/" + id + "/" + version,
            headers=C.token,
            verify=False
        )

fragmentXML=getDdiSet('uk.alspac', 'a300e7bd-485b-42e7-a304-daf2ac685192', "1")
xmlTree=defusedxml.ElementTree.fromstring(fragmentXML.text)
childFragments=xmlTree.findall("./{ddi:instance:3_3}Fragment")

for x in childFragments:
    agency=x[0].findall("./{ddi:reusable:3_3}Agency")[0].text
    id=x[0].findall("./{ddi:reusable:3_3}ID")[0].text
    version=x[0].findall("./{ddi:reusable:3_3}Version")[0].text
    print(agency + ", " + id + ", " + version)


EXAMPLE DELETE ITEM

def getDeleteJson(agency_id, item_id, version):
    return {
  "identifiers": [
    {
      "agencyId": agency_id,
      "identifier": item_id,
      "version": version
    }
  ],
  "deleteType": 0
}

def deleteItems(agency, id, version):
    return requests.post(
            "https://" + C.host + "/api/v1/item/_delete",
            headers=C.token,
            json= getDeleteJson(agency, id, version),
            verify=False
        )

EXAMPLE ALREADY DONE: PROCESSING XML    

agency=xmlTree.findall("./{ddi:instance:3_3}Fragment")[3][0].findall("./{ddi:reusable:3_3}Agency")[0].text
id=xmlTree.findall("./{ddi:instance:3_3}Fragment")[3][0].findall("./{ddi:reusable:3_3}ID")[0].text
version=xmlTree.findall("./{ddi:instance:3_3}Fragment")[3][0].findall("./{ddi:reusable:3_3}Version")[0].text

NEED TO REPLACE GETALLITEMSOFATYPE WITH SEARCH_ITEM

DASHBOARD 1
count=1
allDataSets=getAllItemsOfAType("a51e85bb-6259-4488-8df2-f08cb43485f8")
for x in allDataSets.json()['Results']:
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], "30ea0200-7121-4f01-8d21-a931a182b86d")    
    print(str(count) + ": " + str(len(y.json())))
    count=count+1

NEED TO REPLACE GETRELATEDITEMSBYOBJECT WITH search_relationship_byobject. W

DASHBOARD 2
count=1
for x in allDataSets.json()['Results']:
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], "30ea0200-7121-4f01-8d21-a931a182b86d")    
    fragmentXML=C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    z=str(len(xmlTree.findall(".//{ddi:physicalinstance:3_2}DataFileURI[@isPublic='true']")))
    print(str(count) + ": " + str(len(y.json())) + ", " + z)
    count=count+1

 DASHBOARD 3

 3. Variables which are not within datasets

5 minutes to get all variable items

count=1
allVariables=getAllItemsOfAType("683889c6-f74b-4d5e-92ed-908c0a42bb2d")
for x in allVariables.json()['Results']:
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], "a51e85bb-6259-4488-8df2-f08cb43485f8")    
    print(str(count) + ": " + str(len(y.json())))
    count=count+1


DASHBOARD 4

4 Questionnaires (instrument) not within data collections

count=1
allQuestionnaires=getAllItemsOfAType("f196cc07-9c99-4725-ad55-5b34f479cf7d")
for x in allQuestionnaires.json()['Results']:
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], "c5084916-9936-47a9-a523-93be9fd816d8")    
    print(str(count) + ": " + str(len(y.json())))
    count=count+1

DASHBOARD 5

5. Questionnaires with no PDF

count=1
allQuestionnaires=getAllItemsOfAType("f196cc07-9c99-4725-ad55-5b34f479cf7d")
for x in allQuestionnaires.json()['Results']:
    fragmentXML=C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    z=str(len(xmlTree.findall(".//{ddi:datacollection:3_2}ExternalInstrumentLocation")))
    print(str(count) + ": " + z)
    count=count+1

DASHBOARD 6

6. Questions not within questionnaires

DASHBOARD 7 

7. Agency of questionnaires and datasets match the CV list, or if possible agency matches study

Questionnaires

count=1
agencies = [ "uk.alspac", "uk.cls.bcs70", "uk.mrcleu-uos.hcs", "uk.cls.mcs", "uk.cls.ncds", "uk.cls.nextsteps", "uk.lha", "uk.mrcleu-uos.sws", "uk.iser.ukhls", "uk.wchads", "uk.mrcleu-uos.heaf", "uk.genscot" ]
allQuestionnaires=getAllItemsOfAType("f196cc07-9c99-4725-ad55-5b34f479cf7d")
for x in allQuestionnaires.json()['Results']:
    print(str(count) + ": " + str(x['AgencyId'] in agencies))
    if (not x['AgencyId'] in agencies):
        print (x['AgencyId'])
    count = count + 1

Datasets

count=1
allDataSets=getAllItemsOfAType("a51e85bb-6259-4488-8df2-f08cb43485f8")
for x in allDataSets.json()['Results']:
    print(str(count) + ": " + str(x['AgencyId'] in agencies))
    if (not x['AgencyId'] in agencies):
        print (x['AgencyId'])
    count = count + 1

REMOVE QUESTION REFERENCE FROM Variable


transactionResponse=createTransaction()
transactionId = transactionResponse.json()['TransactionId']
print(transactionId)
count=0
for x in uniqueVariables:
    print(count)
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    fragmentXML = C.get_item_xml(agencyId, variableId, version=version)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    removeElement=xmlTree.findall(".//{ddi:logicalproduct:3_2}Variable/{ddi:reusable:3_2}QuestionReference")
    updateItem=False
    count=count+1
    for y in removeElement:
        agency = y.findall(".//{ddi:reusable:3_2}Agency")[0].text    
        id = y.findall(".//{ddi:reusable:3_2}ID")[0].text
        version = y.findall(".//{ddi:reusable:3_2}Version")[0].text
        urn = "urn:ddi:" + agency + ":" + id + ":" + version
        if urn in orphanQuestionItemsList:
            print(urn + " is orphaned")
            xmlTree.findall("./{ddi:logicalproduct:3_2}Variable")[0].remove(y)
            updateItem=True
        else:
            print(urn + " is not orphaned")
    if updateItem:        
        fragmentString = defusedxml.ElementTree.tostring(xmlTree, encoding='unicode')    
        response2=addItemToTransaction(agencyId, variableId, version, transactionId, fragmentString)
        print(response2)
