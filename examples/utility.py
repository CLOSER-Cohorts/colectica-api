EXAMPLE: FIND ORPHAN QUESTIONS (NOTE THAT IT'S MORE EFFICIENT TO SEARCH FOR ITEMS
REFERENCING QUESTIONS AND CHECK IF NO QUESTION CONSTRUCTS REFER TO IT, AS DEMONSTRATED FURTHER DOWN
THIS FILE)

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

CHECK IF VARIABLES ARE ORPHANS, USING GENERIC METHOD

def followRelationship(agencyId, identifier, version, referencingItemType):
    d={}	
    dataRelationships=getRelatedItemsByObject(agencyId, identifier, version, [referencingItemType])
    if (len(dataRelationships.json()) > 0):
        firstMatchingItem=dataRelationships.json()[0] 
        d= {'AgencyId': firstMatchingItem['Item1']['Item3'], 'Identifier': firstMatchingItem['Item1']['Item1'], 'Version': firstMatchingItem['Item1']['Item2'], 'ItemType': firstMatchingItem['Item2'] }
    return d

CHECK FOR ORPHANS IN LIST OF VARIABLES (CONTAINED IN ITEMS VAR)

items=['urn:ddi:uk.cls.bcs70:53da65fa-e82e-452b-8a91-f8f05003f9e6:3', 'urn:ddi:uk.alspac:7c0b8846-7161-4a12-aa1c-dbcd90801ef4:5']
orphanedItems=[]
count=0
referencingItemTypes=["f39ff278-8500-45fe-a850-3906da2d242b", "a51e85bb-6259-4488-8df2-f08cb43485f8"]
for x in items:
    print(count)
    count=count+1
    currentItemInChain={'AgencyId': x.split(":")[2], 'Identifier': x.split(":")[3], 'Version': x.split(":")[4], 'ItemType': '683889c6-f74b-4d5e-92ed-908c0a42bb2d' }
    for referencingItemType in referencingItemTypes:
        nextItemInChain = followRelationship(currentItemInChain['AgencyId'], currentItemInChain['Identifier'], currentItemInChain['Version'], referencingItemType)
        if nextItemInChain!={}:
             currentItemInChain=nextItemInChain
        else:
             break
    if currentItemInChain['ItemType'] != referencingItemTypes[-1]:
        orphanedItems.append(x)

CHECK FOR ORPHANS IN LIST OF QUESTIONS (CONTAINED IN ITEMS VAR)

questionItemIdentifier = 'a1bb19bd-a24a-4443-8728-a6ad80eb42b8'
allQuestionItemsMetadata=C.search_item(questionItemIdentifier, '', 0)

items=['urn:ddi:uk.alspac:d9f3fd06-161c-42f8-9dfb-5755fb159c08:1', 'urn:ddi:uk.iser.ukhls:f46f6542-cf63-4599-9bdf-17fba2af8bbf:2', 'urn:ddi:uk.lha:bc19fa2e-bb53-4d73-a015-ff93ef0b40ba:1']
count=0
orphanedItems=[]
referencingItemTypes=['f433e43d-29a4-4c25-9610-9dd9819a0519']
for x in items:
    print(count)
    count=count+1    
    currentItemInChain={'AgencyId': x.split(":")[2], 'Identifier': x.split(":")[3], 'Version': x.split(":")[4], 'ItemType': '683889c6-f74b-4d5e-92ed-908c0a42bb2d' }
    for referencingItemType in referencingItemTypes:
        nextItemInChain = followRelationship(currentItemInChain['AgencyId'], currentItemInChain['Identifier'], currentItemInChain['Version'], referencingItemType)
        if nextItemInChain!={}:
             currentItemInChain=nextItemInChain
        else:
             break
    if currentItemInChain['ItemType'] != referencingItemTypes[-1]:
        orphanedItems.append(x)



def findNamespaceText(elementType, referencingItem):
    elementNamespace = ''
    for elem in referencingItem.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementType:
            elementNamespace = getNamespace(elem.tag)
    return elementNamespace        
        


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


NEED TO REPLACE GETALLITEMSOFATYPE WITH SEARCH_ITEM

DASHBOARD 1
count=1
orphanCount=0
allDataSets=getAllItemsOfAType("a51e85bb-6259-4488-8df2-f08cb43485f8")
for x in allDataSets.json()['Results']:
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["30ea0200-7121-4f01-8d21-a931a182b86d"])    
    print(str(count) + ": " + str(len(y.json())))
    if len(y.json())<1:
        orphanCount=orphanCount+1
    count=count+1

NEED TO REPLACE GETRELATEDITEMSBYOBJECT WITH search_relationship_byobject. W

DASHBOARD 2
count=1
orphanCount=0
for x in allDataSets.json()['Results']:
    print(count)
    fragmentXML=C.get_item_xml(x['AgencyId'], x['Identifier'])['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    z=len(xmlTree.findall(".//{ddi:physicalinstance:3_2}DataFileURI[@isPublic='true']"))
    if z<1:
       orphanCount=orphanCount+1
    count=count+1

    FOUND 2 ORPHANS HERE

 DASHBOARD 3

 3. Variables which are not within datasets

5 minutes to get all variable ITEMS

count=1
allVariables=getAllItemsOfAType("683889c6-f74b-4d5e-92ed-908c0a42bb2d")
for x in allVariables.json()['Results']: 
    y = getRelatedItemsByObject(x['AgencyId'], x['Identifier'], x['Version'], ["    88-8df2-f08cb43485f8", "f39ff278-8500-45fe-a850-3906da2d242b"])    
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

def elemToString(xmlTree):
    return defusedxml.ElementTree.tostring(xmlTree, encoding='unicode')

GET RELATED ITEMS

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


FILE INPUT/OUTPUT

with open('orphanedVariablesUrns.txt', encoding="utf-8") as f:
    orphanVariableItems = f.read()
orphanVariablesList=orphanVariableItems.split("\n")   


with open('questionItemsUrns.txt', encoding="utf-8") as f:
    orphanQuestionItems = f.read()
orphanQuestionItemsList=orphanQuestionItems.split("\n")

f = open('orphanVariables.txt', 'w', encoding="utf-8")
f.write('\n'.join(orphanedItems))
f.close()


EXAMPLE DEPRECATING ITEMS

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

def getDeprecateBodyFromList(itemList):
    listOfIds=[]
    for x in itemList:
        listOfIds.append({"agencyId": x.split(":")[2], "identifier": x.split(":")[3], "version": x.split(":")[4]})
    
    return {
        "ids": listOfIds,
        "state": True,
        "applyToAllVersions": True
        }

def deprecateListOfItems(items):
    query=getDeprecateBodyFromList(items)
    response = requests.post(
            "https://" + C.host + "/api/v1/item/_updateState",
            headers=C.token,
            json=query,
            verify=False
        )
    return response

def deprecateItem(agency_id, item_id, version):    
    query=getDeprecateBody(agency_id, item_id, version)
    response = requests.post(
            "https://" + C.host + "/api/v1/item/_updateState",
            headers=C.token,
            json=query,
            verify=False
        )
    return response

count=0
for x in orphanQuestionItemsList:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    variableId=x.split(":")[3]
    version=x.split(":")[4]
    deprecateItem(agencyId, variableId, version)
    print(count)


REMOVE REFERENCES FROM QUESTION GROUPS AND VARIABLES THAT REFER TO THE ORPHAN QUESTIONS


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


CREATE TRANSACTION

def createTransaction():
    return requests.post(
            "https://" + C.host + "/api/v1/transaction",
            headers=C.token,
            json= {"transactionType": "CommitAsLatestWithLatestChildrenAndPropagateVersions"},
            verify=False
        )

transactionResponse = createTransaction()
transactionId = transactionResponse.json()['TransactionId']
print("TRANSACTION ID: ")
print(transactionId)



        
ADD ITEMS TO A TRANSACTION

def getJsonQueryForTransaction(agency_id, item_id, version, fragment, itemType):
        return {
            "transactionId": transactionId,
            "items": [
                {
                "itemType": itemType,
                "agencyId": agency_id,
                "version": version,
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

count=0
for x in updatedRefs:
    print(count)
    count = count +1
    fragmentString = defusedxml.ElementTree.tostring(x[4], encoding='unicode')
    addItemToTransaction(x[1], x[0], x[2], transactionId, fragmentString, x[3])

        
GET NAMESPACE FOR AN ELEMENT

for elem in referencingItem.findall(".//"):
startOfTagName = elem.tag.index("}")+1
tagName = elem.tag[startOfTagName:]
namespace = getNamespace(elem.tag)

def getNamespace(tag):
    m = re.search('{(.+?)}', tag)
    if m:
        return m.group(1)

REMOVE REFERENCES TO ITEMS  

def getTriple(tripleElem):
    triple = {}
    for elem in tripleElem.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        triple[elem.tag[startOfTagName:]] = elem.text
    return(triple)

def getElement(xmlTree, elementName, agency, identifier, version):
    retElem=None
    for elem in xmlTree.findall(".//"):
        startOfTagName = elem.tag.index("}")+1
        tagName = elem.tag[startOfTagName:]
        if tagName == elementName:
            triple= getTriple(elem)
            if (triple['ID']==identifier and triple['Agency']==agency and triple['Version']==version):
               retElem=elem            	
    return retElem

def getCurrentStateOfReferencingItem(storedStateofReferencingItem):
    updatedReferencingItem = [x for x in updatedRefs if x[0]==storedStateofReferencingItem['Item1']['Item1']]
    if (len(updatedReferencingItem)>0):
        referencingItem = updatedReferencingItem[0][4]
    else:
        fragmentXML = C.get_item_xml(storedStateofReferencingItem['Item1']['Item3'], storedStateofReferencingItem['Item1']['Item1'], version=storedStateofReferencingItem['Item1']['Item2'])['Item']
        referencingItem = defusedxml.ElementTree.fromstring(fragmentXML)
    return referencingItem

def updateListofReferencingItems(itemWithoutReference, agency, identifier, version, itemType, updatedRefsCopy):
    if ([x[0] for x in updatedRefsCopy].count(identifier) > 0):
        indexOfUpdatedRef = [x[0] for x in updatedRefsCopy].index(identifier)
        updatedRefsCopy[indexOfUpdatedRef] = (identifier, agency, version, itemType, itemWithoutReference)
    else:
        updatedRefsCopy.append((identifier, agency, version, itemType, itemWithoutReference))            

referencingElementNames = {
    "a1bb19bd-a24a-4443-8728-a6ad80eb42b8":  {
      "5cc915a1-23c9-4487-9613-779c62f8c205": "QuestionItemReference",
      "683889c6-f74b-4d5e-92ed-908c0a42bb2d": "QuestionReference",
      "91da6c62-c2c2-4173-8958-22c518d1d40d": "VariableReference"
    }
}

GET VARIABLE STATISTICS THAT REFERENCE VARIABLES

referencingItemTypes= ['91da6c62-c2c2-4173-8958-22c518d1d40d']
referencedItemType = "a1bb19bd-a24a-4443-8728-a6ad80eb42b8"
updatedRefs=[]
count=0
totalItemReferences=0
for x in orphanVariableItems:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, referencingItemTypes).json()
    for y in referencingItems:
            totalItemReferences=totalItemReferences+1
            updatedRefs.append(x)


#QUESTION
#referencingItemTypes= ['5cc915a1-23c9-4487-9613-779c62f8c205', '683889c6-f74b-4d5e-92ed-908c0a42bb2d']
#referencedItemType = "a1bb19bd-a24a-4443-8728-a6ad80eb42b8"
#VARIABLE
referencingItemTypes= ['3b438f9f-e039-4eac-a06d-3fa1aedf48bb']
referencedItemType = "a1bb19bd-a24a-4443-8728-a6ad80eb42b8"
updatedRefs=[]
count=0
totalItemReferences=0
for x in orphanVariableItems:
    print(count)
    count = count + 1
    agencyId=x.split(":")[2]
    identifier=x.split(":")[3]
    version=x.split(":")[4]
    referencingItems=getRelatedItemsByObject(agencyId, identifier, version, referencingItemTypes).json()
    for y in referencingItems:
            totalItemReferences=totalItemReferences+1
            fragmentXML=C.get_item_xml(y['Item1']['Item3'], y['Item1']['Item1'], version=y['Item1']['Item2'])['Item']
            referencingItem = getCurrentStateOfReferencingItem(y)
            referenceElementName=referencingElementNames[referencedItemType][y['Item2']]
            referenceToRemove = getElement(referencingItem, referenceElementName, agencyId, identifier, version)
            referencingItem[0].remove(referenceToRemove)
            updateListofReferencingItems(referencingItem, y['Item1']['Item3'], y['Item1']['Item1'], y['Item1']['Item2'], y['Item2'], updatedRefs)


# VALIDATE THE REMOVAL OF REFERENCES

allReferencesToOrphansBefore = []
allReferencesToOrphansAfter = []
changedVarGroups=[]
differenceInNumberOfReferences=0
totalNumOrphanRefs=0
count=0
numberOfGroupsAltered=0
numberOfOrphanIdsBefore=0
numberOfOrphanIdsAfter=0
allOrphanRefs=[]

totalReferences=0
totalNumberOfOrphanIdsBefore=0
for x in updatedRefs:
    count = count + 1
    print(count)
    referenceElementName=referencingElementNames[referencedItemType][x[3]]
    agencyId=x[1]
    identifier=x[0]
    version=x[2]
    # GET THE VERSION OF THE ITEM FROM BEFORE THE TRANSACTION THAT REMOVED ORPHAN REFS
    fragmentXML=C.get_item_xml(agencyId, identifier, version=version)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    referencesBefore=getReferences(xmlTree, referenceElementName)
    totalReferences=totalReferences+len(referencesBefore)
    
    orphanRefsBefore = getOrphans(referencesBefore)
    totalNumberOfOrphanIdsBefore = totalNumberOfOrphanIdsBefore + len(orphanRefsBefore)
    allReferencesToOrphansBefore = allReferencesToOrphansBefore + orphanRefsBefore
    
    # NOW GET LATEST VERSION OF ITEM
    fragmentXML=C.get_item_xml(agencyId, identifier)['Item']
    xmlTree=defusedxml.ElementTree.fromstring(fragmentXML)
    
    referencesAfter=getReferences(xmlTree, referenceElementName)
    orphanRefsAfter = getOrphans(referencesAfter)        
    numberOfOrphanIdsAfter = numberOfOrphanIdsAfter + len(orphanRefsAfter)
     
    print("BEFORE: " + str(len(referencesBefore)) + ", AFTER: " + str(len(referencesAfter)))    
    if (len(referencesBefore)!=len(referencesAfter)):
        changedVarGroups.append(x)
        differenceInNumberOfReferences=differenceInNumberOfReferences+(len(orphanRefsBefore)-len(orphanRefsAfter))
        totalNumOrphanRefs=totalNumOrphanRefs+len(orphanRefsBefore)

def getElementName(element):
    startOfTagName = element.tag.index("}")+1
    return element.tag[startOfTagName:]
    
def getOrphans(referencesBefore):
    allOrphans=[]
    for y2 in referencesBefore: 
        triple=getTriple(y2)
        referenceUri= ("urn:ddi:" + triple['Agency'] + ":" + triple['ID'] + ":" + triple['Version'])    
        if (orphanVariableItems.count(referenceUri)>0):
            allOrphans.append(referenceUri)
    return(allOrphans)
                

def getReferences(xmlTree, referenceElementName):
    references=[]
    for y2 in xmlTree.findall(".//"):
        if getElementName(y2)==referenceElementName:
            references.append(y2)
    return(references)            

