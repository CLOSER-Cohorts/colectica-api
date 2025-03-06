"""from colectica_api import ColecticaObject
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)
import examples.find_concordant_items
variablesAcrossWavesNotAllInSameTopic=examples.find_concordant_items.getConcurrentVariablesNotInSameTopic(examples.find_concordant_items.searchSets, HOSTNAME, C)
examples.find_concordant_items.createFileWithConcurrentVariablesNotInSameTopic(variablesAcrossWavesNotAllInSameTopic)
examples.find_concordant_items.createFileWithConcurrentQuestionsAndTheirRelatedVariables(examples.find_concordant_items.searchSets, C)
"""

import os
import re
import defusedxml
from xml.etree import ElementTree as ET
from defusedxml.ElementTree import parse
from colectica_api import ColecticaObject
from examples.lib.utility import get_element_by_name, get_url_from_item, get_urn_from_item
#USERNAME = "USERNAME"
#PASSWORD = "PASSWORD"
#HOSTNAME = "HOSTNAME"

# Array containing object representing the USoc study
searchSets=[
        {
                "agencyId": "uk.iser.ukhls",
                "identifier": "44a7a09e-4703-498c-96f7-0131b296c917",
                "version": 77   
        }]


def addVariableNameToObject(obj, variableName):
   obj['VariableName']=variableName
   return obj

def addQuestionNameToObject(obj, questionName):
   obj['QuestionName']=questionName
   return obj    

def getMappingFrequencies(variableTopicMapping):
   uniqueTopics=set([x[4] for x in variableTopicMapping]) 
   topicCounts=[]
   maxOccurrences=0
   for x in uniqueTopics:
      topicFrequency=len([z for z in variableTopicMapping if z[4]==x])
      if topicFrequency>maxOccurrences:
         maxOccurrences=topicFrequency
      topicCounts.append((x,topicFrequency))
   return [x for x in topicCounts]

def getMostCommonMapping(variableTopicMapping):
   uniqueTopics=set([x[3] for x in variableTopicMapping])
   topicCounts=[]
   maxOccurrences=0
   for x in uniqueTopics:
      topicFrequency=len([z for z in variableTopicMapping if z[3]==x])
      if topicFrequency>maxOccurrences:
         maxOccurrences=topicFrequency
      topicCounts.append((x,topicFrequency))
   return [x for x in topicCounts if x[1]==maxOccurrences]      


def getRelatedVariables(questionMapping):
   relatedVariables=[]
   for question in questionMapping:
      relatedVariable=C.search_relationship_byobject(question[2].split(":")[2], question[2].split(":")[3], item_types=C.item_code('Variable'), Version=str(question[2].split(":")[4]), Descriptions=True)
      if len(relatedVariables)>0:
         relatedVariables.append(relatedVariable[0]['ItemName']['en-GB'])
   return relatedVariables

def getConcurrentVariablesNotInSameTopic(searchSets, hostname, C):
    """Code for getting an array containing variables where the concurrent variables aren't all 
    assigned to the same topic. We read all the variable identifiers into memory because it's 
    easier to perform these operations on data that's already in memory than to perform
    search queries against the API."""
    variables = C.search_items(C.item_code('Variable'), SearchSets=searchSets, ReturnIdentifiersOnly=False)['Results']
    variablesAcrossWavesNotAllInSameTopic=[]
    variablesWithExtraNameField=[addVariableNameToObject(x, "_".join(x['ItemName']['en-GB'].split("_")[1:])) for x in variables]
    uniqueVariableNames=list(set([x['VariableName'] for x in variablesWithExtraNameField]))
    # The 'count' variable is used to display a progress indicator
    count=0
    for variableName in uniqueVariableNames[1:]:
        print(count)
        count=count+1
        concurrentVariablesAcrossWaves=[x for x in variablesWithExtraNameField if x['VariableName']==variableName]
        groupNames=[]
        for variable in concurrentVariablesAcrossWaves:
            dataset=C.query_set(variable['AgencyId'], variable['Identifier'], item_types=['a51e85bb-6259-4488-8df2-f08cb43485f8'], reverseTraversal=True)
            latestDatasetVersion=C.get_item_json(dataset[0]['Item1']['Item3'], dataset[0]['Item1']['Item1'])
            datasetAlternateTitle=latestDatasetVersion['DublinCoreMetadata']['AlternateTitle']['en-GB']
            topicGroups=C.search_relationship_byobject(variable['AgencyId'], variable['Identifier'], item_types=C.item_code('Variable Group'), Version=variable['Version'], Descriptions=True)  
            topicGroupsCurrentlyReferencingVariable=[]
            variablesWithNoGroup=[]
            # The topicGroups objects might contain groups that used to reference a variable; we have to
            # check if a reference to the variable item is present in the most recent version of the group.
            for topicGroup in topicGroups:
                topicGroupMostRecentVersion=C.get_item_xml(topicGroup['AgencyId'], topicGroup['Identifier'])
                if (variable['Identifier'] in topicGroupMostRecentVersion['Item']):
                    topicGroupsCurrentlyReferencingVariable.append(topicGroup)
            if (len(topicGroupsCurrentlyReferencingVariable)==0):
                variablesWithNoGroup.append(variable)
            for y in topicGroupsCurrentlyReferencingVariable:
                if variable['Label'] != {}:
                    varLabel=variable['Label']['en-GB']
                else:
                    varLabel=""
                groupNames.append((variable['ItemName']['en-GB'], varLabel, get_urn_from_item(variable), get_url_from_item(variable, hostname), y['ItemName']['en-GB'], y['Label']['en-GB'], datasetAlternateTitle))
        print(str(len(groupNames)) + " " + str(set(groupNames)))        
        if len(set([x[4] for x in groupNames]))!=1 or len(variablesWithNoGroup)>0:
            variablesAcrossWavesNotAllInSameTopic.append((variable, groupNames))
    return variablesAcrossWavesNotAllInSameTopic

def createFileWithConcurrentVariablesNotInSameTopic(variablesAcrossWavesNotAllInSameTopic):    
    """Open the input files in the data directory, and get the names of the variables
    contained in those files. Check if those variables are present in the
    'variablesAcrossWavesNotAllInSameTopic' object created above, and if they are write them
    to a file along with some additional information."""
    variableInputFiles = [ "examples/data/variablesData/" + x for x in os.listdir("examples/data/variablesData/")]
    fw = open('concordantVariableTopicMismatches2.csv', 'w', encoding="utf-8")
    fw.write("Dataset,Variable stem,Variable,Variable label,Current topic,Topic label,New topic,Columns from here are topic frequencies across all sweeps\n")
    allVarsInInputFiles=[]
    for inputFile in variableInputFiles:
        print(inputFile)
        with open(inputFile, encoding="utf-8") as f:
            inputVariables = f.read()
        inputVariablesList=inputVariables.split("\n")
        for inputVariable in inputVariablesList:
            if len(inputVariable.strip()) > 0:
                allVarsInInputFiles.append(inputVariable.split("\t")[0].split(" ")[1])
                print(len(allVarsInInputFiles))
    for var in set(allVarsInInputFiles):        
        indexOfFirstUnderscore=var.find("_")
        variableStem=var[indexOfFirstUnderscore+1:]
        print(variableStem)
        variableInfo=[x for x in variablesAcrossWavesNotAllInSameTopic if x[0]['VariableName']==variableStem]
        if len(variableInfo)>0:
            variableTopicMappings=variableInfo[0][1]
            b=getMappingFrequencies(variableTopicMappings)
            mappingOccurrences=""
            for z in b:
                mappingOccurrences=mappingOccurrences+str(z[0])+", " + str(z[1])+", "
            for variableTopicMapping in variableTopicMappings:
                fw.write(variableTopicMapping[6] + ", " + variableStem + ", " + variableTopicMapping[0] + ",\""  + variableTopicMapping[1] + "\", " + variableTopicMapping[4] + ",\"" + variableTopicMapping[5] + "\",," + mappingOccurrences + "\n")
    fw.close()

# CHECK IF QUESTIONS ARE MAPPED TO VARIABLES CORRECTLY THIS IS THE DEFINITIVE

def createFileWithConcurrentQuestionsAndTheirRelatedVariables(searchSets, C):
    questionInputFiles = [ "examples/data/questionsData/" + x for x in os.listdir("examples/data/questionsData")]
    fw = open('concordantQuestionVariablePairs2.csv', 'w', encoding="utf-8")
    fw.write("Questionnaire,Question,Question label,Question stem,Question summary,Related variable,Related variable label,Dataset\n")
    allQuestionsInInputFiles=[]
    for inputFile in questionInputFiles:
        print(inputFile)
        with open(inputFile, encoding="utf-8-sig") as f:
            inputQuestions = f.read()
        inputQuestionsList=inputQuestions.split("\n")
        for inputQuestion in inputQuestionsList:
            if len(inputQuestion.strip()) > 0:
                allQuestionsInInputFiles.append(inputQuestion.split("\t")[0].split(" ")[0].strip())
    questions=C.search_items(C.item_code('Question'), SearchSets=searchSets, ReturnIdentifiersOnly=False)['Results']
    questionsWithExtraNameField=[]
    for x in questions:
        positionOfWaveIdentifier = re.search("_w[0-9]+_", x['ItemName']['en-GB'])
        if positionOfWaveIdentifier is not None:
                questionsWithExtraNameField.append(addQuestionNameToObject(x, x['ItemName']['en-GB'][positionOfWaveIdentifier.span()[1]:]))
    # The 'count' variable is used to display a progress indicator
    count=0
    for question in allQuestionsInInputFiles:
        questionStem=[x['QuestionName'] for x in questionsWithExtraNameField if x['ItemName']['en-GB']==question.replace("qc_", "qi_")][0]     
        questionItems=C.search_items(
            [],
            SearchTerms=str(question.replace("qc_", "qi_")).strip(),
            SearchLatestVersion=True)['Results']
        print(str(count) + ": " + str(len(questionItems)))
        count = count + 1
        for questionItem in questionItems:
            latestQuestionVersionJSON=C.get_item_json(questionItem['AgencyId'], questionItem['Identifier'])
            positionOfWaveIdentifier = re.search("_w[0-9]+_", latestQuestionVersionJSON['ItemName']['en-GB'])
            questionName=latestQuestionVersionJSON['ItemName']['en-GB'][positionOfWaveIdentifier.span()[1]:]
            concordantQuestions=[x for x in questionsWithExtraNameField if x['QuestionName']==questionName]
            for concordantQuestionItem in concordantQuestions:
                questionnaire=C.query_set(concordantQuestionItem['AgencyId'], concordantQuestionItem['Identifier'], item_types=['f196cc07-9c99-4725-ad55-5b34f479cf7d'], reverseTraversal=True)
                if len(questionnaire) == 1:
                    latestQuestionnaireVersion=C.get_item_json(questionnaire[0]['Item1']['Item3'], questionnaire[0]['Item1']['Item1'])
                    questionnaireName=latestQuestionnaireVersion['ItemName']['en-GB']
                else:
                    questionnaireName="MULTIPLE QUESTIONNAIRES"
                relatedVariables=C.search_relationship_byobject(concordantQuestionItem['AgencyId'], concordantQuestionItem['Identifier'], item_types=C.item_code('Variable'), Version=concordantQuestionItem['Version'], Descriptions=True)
                for relatedVariable in relatedVariables:
                    latestVariableVersion=C.get_item_xml(relatedVariable['AgencyId'], relatedVariable['Identifier'])
                    latestVariableVersionJSON=C.get_item_json(relatedVariable['AgencyId'], relatedVariable['Identifier'])
                    if concordantQuestionItem['Identifier'] in latestVariableVersion['Item']:
                        dataset=C.query_set(latestVariableVersion['AgencyId'],
                           latestVariableVersion['Identifier'],
                           item_types=['a51e85bb-6259-4488-8df2-f08cb43485f8'],
                           reverseTraversal=True)
                        datasetItem=C.get_item_xml(dataset[0]['Item1']['Item3'],
                           dataset[0]['Item1']['Item1'],
                           version=dataset[0]['Item1']['Item2'])
                        datasetTitle=get_element_by_name(defusedxml.ElementTree.fromstring(datasetItem['Item']), 'Title')
                        variableName=latestVariableVersionJSON['ItemName']['en-GB']
                        variableLabel=latestVariableVersionJSON['Label']['en-GB']
                        questionLabel=concordantQuestionItem['Label']['en-GB']
                        questionSummary=concordantQuestionItem['Summary']['en-GB']
                        fw.write(questionnaireName + "," + concordantQuestionItem['ItemName']['en-GB'] + ",\"" + questionLabel + "\"" + ",\"" + questionStem + "\"" + ",\""  + questionSummary + "\""  + ",\"" + variableName + "\""  + ",\"" + variableLabel + "\"" + ",\"" + datasetTitle['String'] + "\"\n")
                        print(questionnaireName + "," + concordantQuestionItem['ItemName']['en-GB'] + ",\"" + questionLabel + "\"" + ",\"" + questionStem + "\"" + ",\"" + questionSummary + "\""  + ",\"" + variableName + "\""  + ",\"" + variableLabel + "\"" + ",\"" + datasetTitle['String'] + "\"\n")
    fw.close()
