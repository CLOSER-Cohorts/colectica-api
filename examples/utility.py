EXAMPLE: FIND THE ORPHANS

questionItemIdentifier = 'a1bb19bd-a24a-4443-8728-a6ad80eb42b8'
allQuestionItemsMetadata=C.search_item(questionItemIdentifier, '', 0)
questionConstructIdentifier='f433e43d-29a4-4c25-9610-9dd9819a0519'

allResults=C.search_item(questionConstructIdentifier, '', 0)
questionConstructIdentifiers=[]
questionReferenceIDValues=[]
count=0
for x in allResults['Results']:
    print(count)
    count=count+1
    questionConstructIdentifiers.append(x['Identifier'])
    fragmentXML = C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']    
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)    
    questionConstructNamespace=findNamespaceText("QuestionConstruct", xmlTree)
    questionReferenceNamespace=findNamespaceText("QuestionReference", xmlTree)
    agencyNamespace=findNamespaceText("Agency", xmlTree)
    idNamespace=findNamespaceText("ID", xmlTree)
    versionNamespace=findNamespaceText("Version", xmlTree)
      
    questionReferenceAgency=xmlTree.findall(f"./{{{questionConstructNamespace}}}QuestionConstruct/{{{questionReferenceNamespace}}}QuestionReference/{{{agencyNamespace}}}Agency")
    questionReferenceID=xmlTree.findall(f"./{{{questionConstructNamespace}}}QuestionConstruct/{{{questionReferenceNamespace}}}QuestionReference/{{{idNamespace}}}ID")
    questionReferenceVersion=xmlTree.findall(f"./{{{questionConstructNamespace}}}QuestionConstruct/{{{questionReferenceNamespace}}}QuestionReference/{{{versionNamespace}}}Version")
    questionReferenceIDValues.append("urn:ddi:" + questionReferenceAgency[0].text + ":" + questionReferenceID[0].text + ":" + questionReferenceVersion[0].text)


questionItemIdentifiers=[]
questionItemUrnValues=[]

count=0
for x in allQuestionItemsMetadata['Results']:
    print(count)
    count=count+1
    questionItemIdentifiers.append(x['Identifier'])
    fragmentXML = C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']    
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML) 
    questionItemNamespace=findNamespaceText("QuestionItem", xmlTree)
    urnItemNamespace=findNamespaceText("URN", xmlTree) 
    questionItemUrn=xmlTree.findall(f"./{{{questionItemNamespace}}}QuestionItem/{{{urnItemNamespace}}}URN")
    questionItemUrnValues.append(questionItemUrn[0].text)



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
        "state": True,
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


def getJsonQueryForDeprecatingQuestionItems(agency_id, item_id, version, fragment):
        return {
            "transactionId": transactionId,
            "items": []
                {
                "itemType": "a1bb19bd-a24a-4443-8728-a6ad80eb42b8",
                "agencyId": agency_id,
                "version": version,
                "identifier": item_id,
                "item": fragment,
                "transactionId": transactionId,
                "isPublished": True,
                "isDeprecated": True,
                },
            ],
        }

NOTE BELOW WE TOOK OUT VERSION
def getJsonQueryForTransaction(agency_id, item_id, version, fragment, itemType):
        return {
            "transactionId": transactionId,
            "items": [
                {
                "itemType": itemType,
                "agencyId": agency_id,
                "identifier": item_id,
                "item": fragment,
                "transactionId": transactionId,
                "isPublished": True,
                },
            ],
        } 
def addItemToTransaction(agency_id, item_id, version, transactionId, fragment, item_type):
    jsonBody=getJsonQueryForTransaction(agency_id, item_id, version, fragment, item_type)
    response = requests.post(
            "https://" + C.host + "/api/v1/transaction/_addItemsToTransaction",
            headers=C.token,
            json=jsonBody,
            verify=False
        )
    return response    

def findNamespaceText(elementType, referencingItem):
    elementNamespace = ''
    for elem in referencingItem.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementType:
            elementNamespace = getNamespace(elem.tag)
    return elementNamespace        
        
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
    fragmentXML=C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    z=str(len(xmlTree.findall(".//{ddi:physicalinstance:3_2}DataFileURI[@isPublic='true']")))
    count=count+1

 DASHBOARD 3

 3. Variables which are not within datasets

5 minutes to get all variable ITEMS

count=1
allVariables=getAllItemsOfAType("683889c6-f74b-4d5e-92ed-908c0a42bb2d")
for x in allVariables.json()['Results']: 
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["a51e85bb-6259-4488-8df2-f08cb43485f8", "f39ff278-8500-45fe-a850-3906da2d242b"])    
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

CONVERT XML FRAGMENT TO fragmentString
fragmentString = defusedxml.ElementTree.tostring(xmlTree, encoding='unicode')

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


NEED TO RUN THE CODE BELOW BUT IT WILL TAKE TIME TO EXECUTE FOR ALL 190,000 VARIABLES

3389
9273
25062
64589


referencingItemTypes=[]
getAllItemsOfAType
allVariables=("683889c6-f74b-4d5e-92ed-908c0a42bb2d")
count=1
orphanedVariables=[]
for x in allVariables.json()['Results'][0:1]:
   y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], [])
   numOfReferencingDatasets=len(list(filter(lambda x: (x['Item2'] == "a51e85bb-6259-4488-8df2-f08cb43485f8"), y.json())))
   referencingDataRelationship=list(filter(lambda x: (x['Item2'] == "f39ff278-8500-45fe-a850-3906da2d242b"), y.json()))
   for z in referencingDataRelationship:
        a = getRelatedItemsByObject(z['Item1']['Item3'], z['Item1']['Item1'], z['Item1']['Item2'], [])
        numOfReferencingDatasets2=len(list(filter(lambda x: (x['Item2'] == "a51e85bb-6259-4488-8df2-f08cb43485f8"), a.json())))
        numOfReferencingDatasets=numOfReferencingDatasets+numOfReferencingDatasets2
   print(str(count) + ": " + str(numOfReferencingDatasets))
   if (numOfReferencingDatasets == 0):
      orphanedVariables.append(x)
      referencingItemTypes = referencingItemTypes + (list(x['Item2'] for x in y.json()))
   count=count+1

count=0
for x in allVariables.json()['Results']:
   y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], [])
   numOfReferencingVariables=len(list(filter(lambda x: (x['Item2'] == "3b438f9f-e039-4eac-a06d-3fa1aedf48bb"), y.json())))
   if (numOfReferencingVariables>0):
        print(count)
   count=count+1     

orphanedQuestions=[]
referencingQuestionItemTypes=[]

count=1
for x in orphanQuestionItemsList:
   agency=x.split(':')[2]
   id = x.split(':')[3]
   version = x.split(':')[4]  
   y = getRelatedItemsByObject(agency, id, version, [])
   referencingQuestionItemTypes = referencingQuestionItemTypes + (list(x['Item2'] for x in y.json()))
   count=count+1
   print(count)  
   
   
   
   numOfReferencingObjects=len(y)
   referencingDataRelationship=list(filter(lambda x: (x['Item2'] == "f39ff278-8500-45fe-a850-3906da2d242b"), y.json()))
   for z in referencingDataRelationship:
        a = getRelatedItemsByObject(z['Item1']['Item3'], z['Item1']['Item1'], z['Item1']['Item2'], [])
        numOfReferencingDatasets2=len(list(filter(lambda x: (x['Item2'] == "a51e85bb-6259-4488-8df2-f08cb43485f8"), a.json())))
        numOfReferencingDatasets=numOfReferencingDatasets+numOfReferencingDatasets2
   print(str(count) + ": " + str(numOfReferencingDatasets))
   if (numOfReferencingDatasets == 0):
      orphanedVariables.append(x)
       count=count+1

variableReference=defusedxml.ElementTree.fromstring(itemXML['Item']).findall(".//{ddi:reusable:3_2}VariableReference")
variableReference=defusedxml.ElementTree.fromstring(itemXML['Item']).findall(".//{ddi:reusable:3_2}VariableReference[{ddi:reusable:3_2}ID='2573ff1d-41da-4025-b792-fd540315e6f8']")


itemXML=C.get_item_xml(variable_statistic_agency_id, variable_statistic_identifier)
fragmentXML=itemXML['Item']
xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
variableReferenceToRemove=xmlTree.findall(".//{ddi:reusable:3_2}VariableReference[{ddi:reusable:3_2}ID='" + identifier + "']")
for y in variableReferenceToRemove:
    xmlTree.findall("./{ddi:physicalinstance:3_2}VariableStatistics")[0].remove(y)
    

variableReference=defusedxml.ElementTree.fromstring(itemXML['Item']).findall(".//{ddi:reusable:3_2}VariableReference[{ddi:reusable:3_2}ID]")
removeVariableReferenceFromVariableStatistic('uk.iser.ukhls', 'd6325fe0-f5f0-482f-8aaa-7ea2e0903a13', 'uk.iser.uklhs', 'd982c189-91ce-4a85-bad1-09e1e86f8675')


def removeVariableReferenceFromVariableStatistic(variable_statistic_agency_id, variable_statistic_identifier, agency_id, identifier):
    itemXML=C.get_item_xml(variable_statistic_agency_id, variable_statistic_identifier)
    fragmentXML=itemXML['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:reusable:3_2}VariableReference[{ddi:reusable:3_2}ID='" + identifier + "']")
    print(xmlTree)
    print(variableReferenceToRemove)
    for y in variableReferenceToRemove:
        xmlTree.findall("./{ddi:physicalinstance:3_2}VariableStatistics")[0].remove(y)
    print(variableReferenceToRemove)
    return variableReferenceToRemove

def removeVariableReferenceFromVariable(variable_agency_id, variable_identifier, agency_id, identifier):
    fragmentXML=C.get_item_xml(variable_agency_id, variable_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:reusable:3_2}SourceVariableReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:logicalproduct:3_2}Variable")[0].remove(y)
    print(variableReferenceToRemove)
    return xmlTree


def removeVariableReferenceFromDataRelationship(data_relationship_agency_id, data_relationship_identifier, agency_id, identifier):
    fragmentXML=C.get_item_xml(data_relationship_agency_id, data_relationship_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:logicalproduct:3_2}VariableUsedReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    # note the double forward slashes, VariablesInRecord is not in the xml root
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:logicalproduct:3_2}VariablesInRecord")[0].remove(y)
    print(variableReferenceToRemove)
    return xmlTree    


def removeVariableReferenceFromVariableGroup(variable_group_agency_id, variable_group_identifier, agency_id, identifier):
    fragmentXML=C.get_item_xml(variable_group_agency_id, variable_group_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:reusable:3_2}VariableReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:logicalproduct:3_2}VariableGroup")[0].remove(y)
    print(variableReferenceToRemove)
    return xmlTree      



def removeQuestionReferenceFromVariable(question_agency_id, question_identifier, agency_id, identifier):
    fragmentXML=C.get_item_xml(question_agency_id, question_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:reusable:3_2}QuestionReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:logicalproduct:3_2}Variable")[0].remove(y)
    print(variableReferenceToRemove)
    return xmlTree


def removeQuestionReferenceFromQuestionGroup(question_agency_id, question_identifier, agency_id, identifier):
    fragmentXML=C.get_item_xml(question_agency_id, question_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:datacollection:3_2}QuestionItemReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:datacollection:3_2}QuestionGroup")[0].remove(y)

def removeQuestionReferenceFromQuestionScheme(question_agency_id, question_identifier, agency_id, identifier):    
    fragmentXML=C.get_item_xml(question_agency_id, question_identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    variableReferenceToRemove=xmlTree.findall(".//{ddi:datacollection:3_2}QuestionItemReference[{ddi:reusable:3_2}ID='" + identifier+ "']")
    for y in variableReferenceToRemove:
        xmlTree.findall(".//{ddi:datacollection:3_2}QuestionScheme")[0].remove(y)


#def removeReferenceFromItem(item_agency_id, item_identifier, elementContainingReferenceXPath, agencyXPath, identifierXPath):
#    fragmentXML=C.get_item_xml(item_agency_id, item_identifier)['Item']
#    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    # GET VARIABLE REFERENCE TO REMOVE
#    referencesWithAgency=xmlTree.findall(agencyXPath)
#    referencesWithIdentifier=xmlTree.findall(identifierXPath)
#    referenceToRemove = list(set(referencesWithAgency) & set(referencesWithIdentifier))
#    for y in referenceToRemove:
#        xmlTree.findall(elementContainingReferenceXPath)[0].remove(y)
#        REMOVE VARIABLE REFERENCES FROM HOSTING OBJECT


NEED TO WRITE CODE THAT:

ITERATES THROUGH THE LIST OF ORPHANED QUESTIONS/VARIABLES
CHECKS IF EACH IS DEPRECATED. IF NOT, DEPRECATE.
CALL THE RELATIONSHIP/BYOBJECT METHOD. FOR EACH OBJECT THAT REFERS TO THE ORPHANED ITEM, 
CALL THE APPROPRIATE FUNCTION ABOVE. YOU NEED TO MAINTAIN A LOG OF THE ITEMS YOU DEPRECATE.

def getRelatedItemsByObject(agency_id, item_id, version, typeOfItem):
    query=getJsonQueryByObject(agency_id, item_id, version, typeOfItem)
    response = requests.post(
            "https://" + C.host + "/api/v1/_query/relationship/byobject",
            headers=C.token,
            json=query,
            verify=False    
        )
    return response

def getJsonQueryByObject(agency_id, item_id, version, typeOfItem):
        return {
        "itemTypes": typeOfItem ,
        "targetItem": {
        "agencyId": agency_id,
        "identifier": item_id,
        "version": version
        },
        "useDistinctResultItem": True
        }    


with open('orphanedVariablesUrns.txt', encoding="utf-8") as f:
    orphanVariableItems = f.read()

orphanVariablesUrnValuesList=orphanVariableItems.split("\n")   


with open('questionItemsUrns.txt', encoding="utf-8") as f:
    orphanQuestionItems = f.read()
orphanQuestionItemsList=orphanQuestionItems.split("\n")

with open('orphanQuestions.txt', encoding="utf-8") as f:
    orphanQuestionItems = f.read()
orphanQuestionItemsList=orphanQuestionItems.split("\n")


orphanUrnsNEW=[]
for x in orphanedVariables5:
    agencyId=x['AgencyId']
    variableId=x['Identifier']
    version=x['Version']
    orphanUrnsNEW.append("urn:ddi:" + agencyId + ":" + variableId + ":" + str(version))


    orphanQuestionItemsList=orphanQuestionItems.split("\n")


orphanVariablesUrnValuesList=orphanVariableItems.split("\n")


allQuestionItems=[]
deprecatedQuestionItems=[]
versionMismatches=[]
count=0
for x in orphanQuestionItemsList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    variableItem=C.get_item_xml(agencyId, variableId)
    if (variableItem['IsDeprecated']==False):
        deprecatedQuestionItems.append(variableItem)
        allQuestionItems.append(variableItem)
        referencingItems=getRelatedItemsByObject(agencyId, variableId, version, ['a51e85bb-6259-4488-8df2-f08cb43485f8']).json()
        for y in referencingItems:
            referencingItem=C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'])
            allQuestionItems.append(y)
            if (referencingItem['IsDeprecated']==False):
                deprecatedQuestionItems.append(variableItem)
                allQuestionItems.append(variableItem)
                deprecateItem(y['Item1']['Item3'], y['Item1']['Item1'], y['Item1']['Item2'])
        deprecateItem(agencyId, variableId, version)


allQuestionItems=[]
deprecatedQuestionItems=[]
versionMismatches=[]
count=0
for x in orphanVariablesUrnValuesList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    variableItem=C.get_item_xml(agencyId, variableId)
    if(str(variableItem['Version']) != version):
        versionMismatches.append(x)
    
    
    if (variableItem['IsDeprecated']==False):
        deprecatedQuestionItems.append(variableItem)
        allQuestionItems.append(variableItem)
        deprecateItem(agencyId, variableId, version)

    count=0
    for x in orphanVariablesUrnValuesList:
        print(count)
        count = count + 1
        agencyId=x.split(":")[2]
        variableId=x.split(":")[3]
        version=x.split(":")[4]
        referencingItems=getRelatedItemsByObject(agencyId, variableId, version, ['a51e85bb-6259-4488-8df2-f08cb43485f8']).json()
        if (len(referencingItems)>0):
            print(str(count) + "HIT!")      

    #variableItem=C.get_item_xml(agencyId, variableId)
    if (variableItem['IsDeprecated']==False):
        deprecatedQuestionItems.append(variableItem)
        allQuestionItems.append(variableItem)
        


allQuestionItems=[]
count=0
numItems=0
for x in orphanQuestionItems:
    #print(count)
    count = count + 1   
 #   allItems.append(x)
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, variableId, version, []).json()
    for y in referencingItems:
        print(str(count) + ": " + y['IsDeprecated'])


count=0
referencingItemTypes2=[]
for x in orphanVariablesUrnValuesList[count:]:
    print(count)
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4] 
    y = getRelatedItemsByObject(agencyId, variableId, version, []).json()
    for x in y:
        referencingItemTypes2.append(x['Item2'])
   # if (len(y.json()) > 0):
   #     print(orphanVariablesUrnValuesList[count])
    count = count + 1  


DEPRECATE QUESTIONS

allQuestionItems=[]
deprecatedQuestionItems=[]
versionMismatches=[]
count=0
for x in orphanQuestionItemsList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    deprecateItem(agencyId, variableId, version)
    print(count)

DEPRECATE VARIABLES

count=0
for x in orphanVariablesUrnValuesList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    deprecateItem(agencyId, variableId, version)
    print(count)

REMOVE REFERENCES FROM QUESTION GROUPS AND VARIABLES THAT REFER TO THE ORPHAN QUESTIONS


#def removeReferenceFromItem(xmlTree, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath):
#    referencesWithAgency=xmlTree.findall(agencyXPath)
#    referencesWithIdentifier=xmlTree.findall(identifierXPath)
#    referencesWithVersion=xmlTree.findall(versionXPath)
#    referenceToRemove = list(set(referencesWithAgency) & set(referencesWithIdentifier) & set(referencesWithVersion))
#    print(referenceToRemove)
#    return referenceToRemove    
        
def removeReferenceFromItem(xmlTree, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath):
    # GET VARIABLE REFERENCE TO REMOVE
    referencesWithAgency=xmlTree.findall(agencyXPath)
    referencesWithIdentifier=xmlTree.findall(identifierXPath)
    referencesWithVersion=xmlTree.findall(versionXPath)
    referenceToRemove = list(set(referencesWithAgency) & set(referencesWithIdentifier) & set(referencesWithVersion))
    print(referenceToRemove)
    for y in referenceToRemove:
        xmlTree.findall(elementContainingReferenceXPath)[0].remove(y)
    return referenceToRemove    

transactionResponse = createTransaction()
transactionId = transactionResponse.json()['TransactionId']
print("TRANSACTION ID: ")
print(transactionId)
updatedRefs=[]
count=0
for x in orphanQuestionItemsList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, ['5cc915a1-23c9-4487-9613-779c62f8c205', '683889c6-f74b-4d5e-92ed-908c0a42bb2d']).json()
    for y in referencingItems:
            fragmentXML=C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item']
            updatedReferencingItem = [x for x in updatedRefs if x[0]==y['Item1']['Item1']]
            if (len(updatedReferencingItem)>0):
                referencingItem = updatedReferencingItem[0][1]
            else:
                referencingItem = C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])
            if y['Item2'] == '5cc915a1-23c9-4487-9613-779c62f8c205':
                agencyXPath = ".//{ddi:datacollection:3_2}QuestionItemReference[{ddi:reusable:3_2}Agency='" + agencyId + "']"
                identifierXPath = ".//{ddi:datacollection:3_2}QuestionItemReference[{ddi:reusable:3_2}ID='" + identifier + "']"
                versionXPath = ".//{ddi:datacollection:3_2}QuestionItemReference[{ddi:reusable:3_2}Version='" + version + "']"
                elementContainingReferenceXPath = ".//{ddi:datacollection:3_2}QuestionGroup"
                itemWithoutReference = removeReferenceFromItem(fragmentXML, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                if ([x[0] for x in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x[0] for x in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'])
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2']))
            elif y['Item2'] == '683889c6-f74b-4d5e-92ed-908c0a42bb2d':
                agencyXPath = ".//{ddi:reusable:3_2}QuestionReference[{ddi:reusable:3_2}Agency='" + agencyId + "']"
                identifierXPath = ".//{ddi:reusable:3_2}QuestionReference[{ddi:reusable:3_2}ID='" + identifier + "']"
                versionXPath = ".//{ddi:reusable:3_2}QuestionReference[{ddi:reusable:3_2}Version='" + version + "']"
                elementContainingReferenceXPath = ".//{ddi:logicalproduct:3_2}Variable" 
                itemWithoutReference = removeReferenceFromItem(fragmentXML, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                if ([x[0] for x in updatedRefs].count(y['Item1'][   'Item1']) > 0):
                    indexOfUpdatedRef = [x[0] for x in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'])
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2']))
            
test2 = get_item_xml('uk.alspac', '150c6eb8-2434-4368-a4dd-862bacc1768b')            

orphan=['urn:ddi:uk.iser.ukhls:327a994b-3ced-4e0e-be90-f6a79cfe2791:1']
orphanVariablesUrnValuesList
transactionResponse=createTransaction()
transactionId = transactionResponse.json()['TransactionId']
print("TRANSACTION ID: ")
print(transactionId)
updatedRefs=[]
updatedRefs2=[]
allGroupRefs=[]
allRefs=[]
allRefTypes=[]
referencingItems=[]
count=0
referencingItemType='683889c6-f74b-4d5e-92ed-908c0a42bb2d'
#for x in orphanUrns:
for x in orphanQuestionItems:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, []).json()
    for y in referencingItems:
            allRefTypes.append(y['Item2'])
            #fragmentXML=C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item'] 
            if (y['Item2'] == referencingItemType):
                allRefs.append(x) 
                allGroupRefs.append(("urn:ddi:" + y['Item1']['Item3'] + ":" + y['Item1']['Item1'] + ":" + str(y['Item1']['Item2'])))             
            updatedReferencingItem = [x1 for x1 in updatedRefs if x1[0]==y['Item1']['Item1']]
            if (len(updatedReferencingItem)>0):
                referencingItem = updatedReferencingItem[0][3]
            else:
                fragmentXML = C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item']
                referencingItem = defusedxml.ElementTree.fromstring(fragmentXML)
            variableGroupNamespace = ''
            variableReferenceNamespace = ''    
            agencyNamespace = ''
            idNamespace = ''
            versionNamespace = ''
            sourceVariableReferenceNamespace = ''
            variableNamespace = ''
            for elem in referencingItem.findall(".//"):
                startOfTagName = elem.tag.index("}")+1
                tagName = elem.tag[startOfTagName:]
                if tagName == 'VariableGroup':
                    variableGroupNamespace = getNamespace(elem.tag)
                if tagName == 'VariableReference':
                    variableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Agency':
                    agencyNamespace = getNamespace(elem.tag)   
                if tagName == 'ID':
                    idNamespace = getNamespace(elem.tag)
                if tagName == 'Version':
                    versionNamespace = getNamespace(elem.tag)
                if tagName == 'SourceVariableReference':
                    sourceVariableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Variable':
                    variableNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionReference':
                    questionReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionItemReference':
                    questionItemReferenceNamespace = getNamespace(elem.tag)    
            if y['Item2'] == referencingItemType:
                agencyXPath = f".//{{{variableReferenceNamespace}}}VariableReference[{{{agencyNamespace}}}Agency='" + agencyId + "']"
                identifierXPath = f".//{{{variableReferenceNamespace}}}VariableReference[{{{idNamespace}}}ID='" + identifier + "']"
                versionXPath = f".//{{{variableReferenceNamespace}}}VariableReference[{{{versionNamespace}}}Version='" + version + "']"
                elementContainingReferenceXPath = f".//{{{variableGroupNamespace}}}VariableGroup"
                #xmlTree=defusedxml.ElementTree.fromstring(referencingItem)
                itemWithoutReference = removeReferenceFromItem(referencingItem, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                updatedRefs2.append(y['Item1']['Item1'])
                if ([x[0] for x in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x1[0] for x1 in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier)
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier))
            elif y['Item2'] == '683889c6-f74b-4d5e-92ed-908c0a42bb2d':
                agencyXPath = f".//{{{sourceVariableReferenceNamespace}}}SourceVariableReference[{{{agencyNamespace}}}Agency='" + agencyId + "']"
                identifierXPath = f".//{{{sourceVariableReferenceNamespace}}}SourceVariableReference[{{{idNamespace}}}ID='" + identifier + "']"
                versionXPath = f".//{{{sourceVariableReferenceNamespace}}}SourceVariableReference[{{{versionNamespace}}}Version='" + version + "']"
                elementContainingReferenceXPath = f".//{{{variableNamespace}}}Variable" 
                itemWithoutReference = removeReferenceFromItem(xmlTree, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                if ([x1[0] for x1 in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x1[0] for x1 in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier)
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier))


)
            variableGroupNamespace = ''
            variableReferenceNamespace = ''    
            agencyNamespace = ''
            idNamespace = ''
            versionNamespace = ''
            sourceVariableReferenceNamespace = ''
            variableNamespace = ''
            questionReferenceNamespace = ''
    
            namespaceLookup={}
            for elem in referencingItem.findall(".//"):
                startOfTagName = elem.tag.index("}")+1
                tagName = elem.tag[startOfTagName:]
                namespace = getNamespace(elem.tag)
                namespaceLookup[tagName] = namespaceLookup[tagName].append(namespace) if tagName in namespaceLookup else [namespace]

                if tagName == 'VariableGroup':
                    variableGroupNamespace = getNamespace(elem.tag)
                if tagName == 'VariableReference':
                    variableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Agency':
                    agencyNamespace = getNamespace(elem.tag)   
                if tagName == 'ID':
                    idNamespace = getNamespace(elem.tag)
                if tagName == 'Version':
                    versionNamespace = getNamespace(elem.tag)
                if tagName == 'SourceVariableReference':
                    sourceVariableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Variable':
                    variableNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionGroup':
                    questionGroupNamespace = getNamespace(elem.tag)    
                if tagName == 'QuestionReference':
                    questionReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionItemReference':
                    questionItemReferenceNamespace = getNamespace(elem.tag)    

def getNamespaces(elementTagnames):
    variableGroupNamespace = ''
    variableReferenceNamespace = ''    
    agencyNamespace = ''
    idNamespace = ''
    versionNamespace = ''
    sourceVariableReferenceNamespace = ''
    variableNamespace = ''
    questionReferenceNamespace = ''
    
    namespaceLookup={}
    for elem in referencingItem.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        namespace = getNamespace(elem.tag)
        namespaceLookup[tagName] = namespaceLookup[tagName].append(namespace) if tagName in namespaceLookup else [namespace]

        if tagName == 'VariableGroup':
            variableGroupNamespace = getNamespace(elem.tag)
            if tagName == 'VariableReference':
                variableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Agency':
                    agencyNamespace = getNamespace(elem.tag)   
                if tagName == 'ID':
                    idNamespace = getNamespace(elem.tag)
                if tagName == 'Version':
                    versionNamespace = getNamespace(elem.tag)
                if tagName == 'SourceVariableReference':
                    sourceVariableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Variable':
                    variableNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionGroup':
                    questionGroupNamespace = getNamespace(elem.tag)    
                if tagName == 'QuestionReference':
                    questionReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionItemReference':
                    questionItemReferenceNamespace = getNamespace(elem.tag) 


namespaceLookup={}
for elem in referencingItem.findall(".//"):
    startOfTagName = elem.tag.index("}")+1
    tagName = elem.tag[startOfTagName:]
    namespaceLookup[tagName] = getNamespace(elem.tag)

updatedRefs=[]
updatedRefs2=[]
allQuestionItemsInGroups=[]
allQuestionItemsInVariables=[]
allRefs=[]
allRefTypes=[]
referencingItems=[]
questionGroups=[]
referencingVariables=[]
count=0
#for x in orphanUrns:
for x in orphanQuestionItemsList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, []).json()
    for y in referencingItems:
            allRefTypes.append(y['Item2'])
            #fragmentXML=C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item'] 
            #if (y['Item2'] == '5cc915a1-23c9-4487-9613-779c62f8c205' or y['Item2']=='683889c6-f74b-4d5e-92ed-908c0a42bb2d'):
            #    allRefs.append(x) 
            #    allGroupRefs.append(("urn:ddi:" + y['Item1']['Item3'] + ":" + y['Item1']['Item1'] + ":" + str(y['Item1']['Item2'])))             
            variableGroupNamespace = ''
            variableReferenceNamespace = ''    
            agencyNamespace = ''
            idNamespace = ''
            versionNamespace = ''
            sourceVariableReferenceNamespace = ''
            variableNamespace = ''           
            updatedReferencingItem = [x1 for x1 in updatedRefs if x1[0]==y['Item1']['Item1']]
            if (len(updatedReferencingItem)>0):
                referencingItem = updatedReferencingItem[0][3]
            else:
                fragmentXML = C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item']
                referencingItem = defusedxml.ElementTree.fromstring(fragmentXML)
            for elem in referencingItem.findall(".//"):
                startOfTagName = elem.tag.index("}")+1
                tagName = elem.tag[startOfTagName:]
                if tagName == 'VariableGroup':
                    variableGroupNamespace = getNamespace(elem.tag)
                if tagName == 'VariableReference':
                    variableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Agency':
                    agencyNamespace = getNamespace(elem.tag)   
                if tagName == 'ID':
                    idNamespace = getNamespace(elem.tag)
                if tagName == 'Version':
                    versionNamespace = getNamespace(elem.tag)
                if tagName == 'SourceVariableReference':
                    sourceVariableReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'Variable':
                    variableNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionGroup':
                    questionGroupNamespace = getNamespace(elem.tag)    
                if tagName == 'QuestionReference':
                    questionReferenceNamespace = getNamespace(elem.tag)
                if tagName == 'QuestionItemReference':
                    questionItemReferenceNamespace = getNamespace(elem.tag)
            if y['Item2'] == '683889c6-f74b-4d5e-92ed-908c0a42bb2d':
                agencyXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{agencyNamespace}}}Agency='" + agencyId + "']"
                identifierXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{idNamespace}}}ID='" + identifier + "']"
                versionXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{versionNamespace}}}Version='" + version + "']"
                elementContainingReferenceXPath = f".//{{{variableNamespace}}}Variable" 
                itemWithoutReference = removeReferenceFromItem(referencingItem, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                referencingVariables.append("urn:ddi:" + y['Item1']['Item3'] + ":" + y['Item1']['Item1'] + ":" + str(y['Item1']['Item2']))        
                allQuestionItemsInVariables.append(x)
                if ([x1[0] for x1 in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x1[0] for x1 in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier)
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier))
        
            if y['Item2'] == '5cc915a1-23c9-4487-9613-779c62f8c205':
                agencyXPath = f".//{{{questionItemReferenceNamespace}}}QuestionItemReference[{{{agencyNamespace}}}Agency='" + agencyId + "']"
                identifierXPath = f".//{{{questionItemReferenceNamespace}}}QuestionItemReference[{{{idNamespace}}}ID='" + identifier + "']"
                versionXPath = f".//{{{questionItemReferenceNamespace}}}QuestionItemReference[{{{versionNamespace}}}Version='" + version + "']"
                elementContainingReferenceXPath = f".//{{{questionGroupNamespace}}}QuestionGroup"
                #xmlTree=defusedxml.ElementTree.fromstring(referencingItem)
                itemWithoutReference = removeReferenceFromItem(referencingItem, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                questionGroups.append("urn:ddi:" + y['Item1']['Item3'] + ":" + y['Item1']['Item1'] + ":" + str(y['Item1']['Item2']))
                allQuestionItemsInGroups.append(x)
                if ([x[0] for x in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x1[0] for x1 in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier)
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier))
            elif y['Item2'] == '683889c6-f74b-4d5e-92ed-908c0a42bb2d':
                agencyXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{agencyNamespace}}}Agency='" + agencyId + "']"
                identifierXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{idNamespace}}}ID='" + identifier + "']"
                versionXPath = f".//{{{questionReferenceNamespace}}}QuestionReference[{{{versionNamespace}}}Version='" + version + "']"
                elementContainingReferenceXPath = f".//{{{variableNamespace}}}Variable" 
                itemWithoutReference = removeReferenceFromItem(referencingItem, elementContainingReferenceXPath, agencyXPath, identifierXPath, versionXPath)
                referencingVariables.append("urn:ddi:" + y['Item1']['Item3'] + ":" + y['Item1']['Item1'] + ":" + str(y['Item1']['Item2']))        
                allQuestionItemsInVariables.append(x)
                if ([x1[0] for x1 in updatedRefs].count(y['Item1']['Item1']) > 0):
                    indexOfUpdatedRef = [x1[0] for x1 in updatedRefs].index(y['Item1']['Item1'])
                    updatedRefs[indexOfUpdatedRef] = (y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier)
                else:
                    updatedRefs.append((y['Item1']['Item1'], y['Item1']['Item2'], y['Item1']['Item3'], itemWithoutReference, y['Item2'], identifier))



cumulated=[]
count=0
for x in orphanVariablesUrnValuesList:
    print(x)
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, ['91da6c62-c2c2-4173-8958-22c518d1d40d', '683889c6-f74b-4d5e-92ed-908c0a42bb2d']).json()
    for y in referencingItems:
        itemData1 = get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'])
        itemData2 = get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])
        #versionOfReferencingItem=itemData['Version']
        referenceToOrphanPresentInLatestReferencedItem = False
        referenceToOrphanPresentInReferencedItem = False
        if (itemData1['Item'].find(identifier) > -1):
            referenceToOrphanPresentInLatestReferencedItem = True
        if (itemData2['Item'].find(identifier) > -1):
            referenceToOrphanPresentInReferencedItem = True    
        if (not referenceToOrphanPresentInLatestReferencedItem and referenceToOrphanPresentInReferencedItem):
            cumulated.append((y['Item1']['Item3'], y['Item1']['Item1']))
            

        
        if (y['Item1']['Item2'] > 1):
            previousVersion = y['Item1']['Item2'] - 1
        else:
            previousVersion = y['Item1']['Item2']    
        
        
CAN'T COUNT THE NUMBER OF REFERENCING ITEMS CORRECTLY?


len(set([x['Item1']['Item1'] for x in cumulated]))

count=0
for x in updatedRefs:
    print(count)
    count = count +1
    fragmentString = defusedxml.ElementTree.tostring(x[3], encoding='unicode')
    addItemToTransaction(x[2], x[0], x[1], transactionId, fragmentString, x[4])
                

INCOMPLETE; NEED TO GO FROM VAR-> DATA RELATIONSHIP->PHYSICAL INSTANCE

orphanedVariables=[]
count=1
for x in allVariables: 
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["a51e85bb-6259-4488-8df2-f08cb43485f8"])    
    print(str(count) + ": " + str(len(orphanedVariables)))
    if (len(y.json()) == 0):
        orphanedVariables.append(y.json())
    count=count+1


//datarelationships=[] #we can examine these to see if any have no references after
orphanedVariables2=[]
count=1
for x in allVariables: 
    for y in getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["f39ff278-8500-45fe-a850-3906da2d242b"]).json():    
        z = getRelatedItemsByObject(y['Item1']['Item3'], y['Item1']['Item1'], y['Item1']['Item2'], ["a51e85bb-6259-4488-8df2-f08cb43485f8"])    
        print(str(count) + ": " + str(len(orphanedVariables2)))
        if (len(z.json()) == 0):
            orphanedVariables2.append(y.json())
    count=count+1    

orphanedVariables4=[]
count=1
for x in orphanVariablesUrnValuesList:
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4] 
    dataRelationships=getRelatedItemsByObject(agencyId, identifier, version, ["a51e85bb-6259-4488-8df2-f08cb43485f8"]).json()
    if(len(dataRelationships) == 0):
        orphanedVariables4.append(x)
    print(str(count) + ": " + str(len(orphanedVariables4)))    
    count=count+1    


orphanedVariables5=[]
orphanedVariables6=[]
count=1
for x in allVariables[85966:]:
    dataRelationships=getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["f39ff278-8500-45fe-a850-3906da2d242b"]).json()
    for y in dataRelationships:    
        z = getRelatedItemsByObject(y['Item1']['Item3'], y['Item1']['Item1'], y['Item1']['Item2'], ["a51e85bb-6259-4488-8df2-f08cb43485f8"])    
        print(str(count) + ": " + str(len(orphanedVariables5)))
        if (len(z.json()) == 0):
            orphanedVariables5.append(x)
    if(len(dataRelationships) == 0):
        orphanedVariables5.append(x)
    #physicalInstances = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], "a51e85bb-6259-4488-8df2-f08cb43485f8")    
    #if (len(physicalInstances.json())==0):
    #    orphanedVariables6.append(x)
    print(count)
    count=count+1    


        


def getNamespace(tag):
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)
