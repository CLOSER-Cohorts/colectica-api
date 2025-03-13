"""This code demonstrates how to find concordant questions (and their associated variables)
and concordant variables in the Understanding Society (Usoc) study, and write details
of these concordant items to CSV files.

The set of commands that need to be executed in order to achieve this are:

from colectica_api import ColecticaObject
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)
import examples.find_concordant_items
variablesAcrossWavesNotAllInSameTopic=examples.find_concordant_items.getConcurrentVariablesNotInSameTopic(
    examples.find_concordant_items.searchSets, HOSTNAME, C)
examples.find_concordant_items.createFileWithConcurrentVariablesNotInSameTopic(variablesAcrossWavesNotAllInSameTopic)
examples.find_concordant_items.createFileWithConcurrentQuestionsAndTheirRelatedVariables(
    examples.find_concordant_items.searchSets, C)
"""

import os
import re
import defusedxml
from xml.etree import ElementTree as ET
from defusedxml.ElementTree import parse
from colectica_api import ColecticaObject
from examples.lib.utility import get_element_by_name, get_url_from_item, get_urn_from_item

# USERNAME = "INSERT USERNAME HERE"
# PASSWORD = "INSERT PASSWORD HERE"
# HOSTNAME = "INSERT HOSTNAME HERE"
# C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)

# Array containing object identifying the USoc study
searchSets = [
    {
        "agencyId": "uk.iser.ukhls",
        "identifier": "44a7a09e-4703-498c-96f7-0131b296c917",
        "version": 77
    }]


def addVariableStemToObject(obj, variableName):
    obj['variableStem'] = variableName
    return obj

def addQuestionNameToObject(obj, questionName):
    obj['questionName'] = questionName
    return obj

def getMappingFrequencies(variableTopicMapping):
    uniqueTopics = set([topicMapping["variableTopicName"] for topicMapping in variableTopicMapping])
    topicCounts = []
    maxOccurrences = 0
    for topicName in uniqueTopics:
        topicFrequency = len([mapping for mapping in variableTopicMapping if mapping["variableTopicName"] == topicName])
        if topicFrequency > maxOccurrences:
            maxOccurrences = topicFrequency
        topicCounts.append({"topicName": topicName, "topicFrequency": topicFrequency})
    return topicCounts

def getMostCommonMapping(variableTopicMapping):
    uniqueTopics = set([topicMapping["variableUrl"] for topicMapping in variableTopicMapping])
    topicCounts = []
    maxOccurrences = 0
    for topicName in uniqueTopics:
        topicFrequency = len([mapping for mapping in variableTopicMapping if mapping["variableUrl"] == topicName])
        if topicFrequency > maxOccurrences:
            maxOccurrences = topicFrequency
        topicCounts.append({"topicName": topicName, "topicFrequency": topicFrequency})
    return [topic for topic in topicCounts if topic["topicFrequency"] == maxOccurrences]

def getRelatedVariables(questionMapping):
    relatedVariables = []
    for question in questionMapping:
        relatedVariable = C.search_relationship_byobject(question[2].split(":")[2], question[2].split(
            ":")[3], item_types=C.item_code('Variable'), Version=str(question[2].split(":")[4]), Descriptions=True)
        if len(relatedVariables) > 0:
            relatedVariables.append(relatedVariable[0]['ItemName']['en-GB'])
    return relatedVariables

def getConcurrentVariablesNotInSameTopic(searchSets, hostname, C):
    """Code for creating an array of concurrent variables where all the variables in the
    concurrent set aren't assigned to the same topic.
    """
    # We read all the variable identifiers into memory because it's
    # easier to perform operations on data that's already in memory than to perform multiple
    # search queries against the API.
    variables = C.search_items(C.item_code('Variable'),
                               SearchSets=searchSets,
                               ReturnIdentifiersOnly=False)['Results']
    variablesAcrossWavesNotAllInSameTopic = []
    variablesWithExtraStemField = [addVariableStemToObject(
        x, "_".join(x['ItemName']['en-GB'].split("_")[1:])) for x in variables]
    uniqueVariableStems = list(set(
        [x['variableStem']
            for x in variablesWithExtraStemField if x['variableStem'] != '']
    ))
    # The 'count' variable is used to display a progress indicator
    count = 0
    for variableStem in uniqueVariableStems:
        count = count + 1
        print(f"Examining variable stem {variableStem}, {count} of {len(uniqueVariableStems)}")
        concurrentVariableDetails = []
        concurrentVariablesAcrossWaves = [
            x for x in variablesWithExtraStemField if x['variableStem'] == variableStem]
        for variable in concurrentVariablesAcrossWaves:
            if variable['Label'] != {}:
                variableLabel = variable['Label']['en-GB']
            else:
                variableLabel = ""
            dataset = C.query_set(variable['AgencyId'],
                                  variable['Identifier'],
                                  item_types=[
                                      'a51e85bb-6259-4488-8df2-f08cb43485f8'],
                                  reverseTraversal=True)
            datasetItems = [{"AgencyId": x['Item1']['Item3'], "Identifier": x['Item1']['Item1']} for x in dataset]
            uniqueDatasetItems = list(set([(x['Item1']['Item3'], x['Item1']['Item1']) for x in dataset]))
            if len(uniqueDatasetItems) > 1:
                print(f"""WARNING: Variable {variable['ItemName']} ({variableLabel}) is present in two datasets.
                   This variable will be excluded from the list.""")
            else:
                latestDatasetVersion = C.get_item_json(datasetItems[0]['AgencyId'],
                                                   datasetItems[0]['Identifier'])
                dataset_alternate_title = latestDatasetVersion['DublinCoreMetadata']['AlternateTitle']['en-GB']
                topicGroups = C.search_relationship_byobject(variable['AgencyId'],
                                                         variable['Identifier'],
                                                         item_types=C.item_code(
                                                             'Variable Group'),
                                                         Version=variable['Version'],
                                                         Descriptions=True)
                topicGroupsCurrentlyReferencingVariable = []
                # The topicGroups objects might contain groups that used to reference a variable; we have to
                # check if a reference to the variable item is present in the most recent version of the
                # topicGroup.
                for topicGroup in topicGroups:
                    topicGroupMostRecentVersion = C.get_item_xml(topicGroup['AgencyId'],
                                                             topicGroup['Identifier'])
                    if (variable['Identifier'] in topicGroupMostRecentVersion['Item']):
                        topicGroupsCurrentlyReferencingVariable.append(topicGroup)
                # If a variable is not assigned to a topic, we add an entry to concurrentVariableDetails
                # indicating this.
                if (len(topicGroupsCurrentlyReferencingVariable) == 0):
                    concurrentVariableDetails.append({
                                                  "variableName": variable['ItemName']['en-GB'],
                                                  "variableLabel": variableLabel,
                                                  "variableUrn": get_urn_from_item(variable),
                                                  "variableUrl": get_url_from_item(
                                                      variable, hostname),
                                                  "variableTopicName": "no_topic",
                                                  "variableTopicLabel": "no_topic_label",
                                                  "variableDatasetAlternateTitle": dataset_alternate_title
                                                  })
                for topicGroupReferencingVariable in topicGroupsCurrentlyReferencingVariable:
                    concurrentVariableDetails.append({"variableName": variable['ItemName']['en-GB'],
                                                  "variableLabel": variableLabel,
                                                  "variableUrn": get_urn_from_item(variable),
                                                  "variableUrl": get_url_from_item(
                                                      variable, hostname),
                                                  "variableTopicName": topicGroupReferencingVariable['ItemName']['en-GB'],
                                                  "variableTopicLabel": topicGroupReferencingVariable['Label']['en-GB'],
                                                  "variableDatasetAlternateTitle": dataset_alternate_title
                                                  })
        if len(set([variable["variableTopicName"] for variable in concurrentVariableDetails])) != 1:
            variablesAcrossWavesNotAllInSameTopic.append(
                {"variableStem": variable["variableStem"], "concurrentVariables": concurrentVariableDetails})
    return variablesAcrossWavesNotAllInSameTopic


def createFileWithConcurrentVariablesNotInSameTopic(variablesAcrossWavesNotAllInSameTopic):
    """Open the input files in the data/variablesData directory, and get the names of the 
    variables contained in those files. Check if those variables are present in the
    'variablesAcrossWavesNotAllInSameTopic' object created by the
    getConcurrentVariablesNotInSameTopic method, and if they are write them to a file
    along with some additional information."""
    variableInputFiles = ["examples/data/variablesData/" +
                          x for x in os.listdir("examples/data/variablesData/")]
    fw = open('concordantVariableTopicMismatches.csv', 'w', encoding="utf-8")
    fw.write("Dataset,Variable stem,Variable,Variable label,Current topic,Topic label,New topic,Columns from here are topic frequencies across all sweeps\n")
    allVarsInInputFiles = []
    for inputFile in variableInputFiles:
        print(inputFile)
        with open(inputFile, encoding="utf-8") as f:
            inputVariables = f.read()
        inputVariablesList = inputVariables.split("\n")
        for inputVariable in inputVariablesList:
            if len(inputVariable.strip()) > 0:
                allVarsInInputFiles.append(
                    inputVariable.split("\t")[0].split(" ")[1])
    for var in set(allVarsInInputFiles):
        indexOfFirstUnderscore = var.find("_")
        variableStem = var[indexOfFirstUnderscore+1:]
        variableInfo = [
            concurrentVariable for concurrentVariable in variablesAcrossWavesNotAllInSameTopic 
               if concurrentVariable['variableStem'] == variableStem]
        if len(variableInfo) == 1:
            variableTopicMappings = variableInfo[0]["concurrentVariables"]
            mappingFrequencies = getMappingFrequencies(variableTopicMappings)
            mappingOccurrences = ""
            for mappingFrequency in mappingFrequencies:
                mappingOccurrences = mappingOccurrences + \
                    str(mappingFrequency["topicName"])+", " + str(mappingFrequency["topicFrequency"])+", "
            for variableTopicMapping in variableTopicMappings:
                fw.write(variableTopicMapping["variableDatasetAlternateTitle"] + ", " 
                   + variableStem + ", "
                   + variableTopicMapping["variableName"] + ",\""
                   + variableTopicMapping["variableLabel"] + "\", " 
                   + variableTopicMapping["variableTopicName"] + ",\""
                   + variableTopicMapping["variableTopicLabel"] + "\",,"
                   + mappingOccurrences + "\n")
        elif len(variableInfo) > 1:
            print(f"""WARNING: Multiple entries in variablesAcrossWavesNotAllInSameTopic object found 
               for variable stem {variableStem}. The concurrent variables for this variable stem will 
               not be written to the output file.""")
    fw.close()

def createFileWithConcurrentQuestionsAndTheirRelatedVariables(searchSets, C):
    """Open the input files in the data/questionsData directory, and get the names of the 
    questions contained in those files. Get the variables related to those questions and
    write some details about those questions and variables to a file."""
    questionInputFiles = ["examples/data/questionsData/" +
                          x for x in os.listdir("examples/data/questionsData")]
    fw = open('concordantQuestionVariablePairs.csv', 'w', encoding="utf-8")
    fw.write("Questionnaire,Question,Question label,Question stem,Question summary,Related variable,Related variable label,Dataset\n")
    allQuestionsInInputFiles = []
    for inputFile in questionInputFiles:
        print(inputFile)
        with open(inputFile, encoding="utf-8-sig") as f:
            inputQuestions = f.read()
        inputQuestionsList = inputQuestions.split("\n")
        for inputQuestion in inputQuestionsList:
            if len(inputQuestion.strip()) > 0:
                allQuestionsInInputFiles.append(inputQuestion.split("\t")[
                                                0].split(" ")[0].strip())
    questions = C.search_items(C.item_code(
        'Question'), SearchSets=searchSets, ReturnIdentifiersOnly=False)['Results']
    questionsWithExtraNameField = []
    for question in questions:
        positionOfWaveIdentifier = re.search(
            "_w[0-9]+_", question['ItemName']['en-GB'])
        if positionOfWaveIdentifier is not None:
            questionsWithExtraNameField.append(addQuestionNameToObject(
                question, question['ItemName']['en-GB'][positionOfWaveIdentifier.span()[1]:]))
    # The 'count' variable is used to display a progress indicator
    count = 0
    for question in allQuestionsInInputFiles:
        count = count + 1
        questionStemList = [x['questionName'] for x in questionsWithExtraNameField if x['ItemName']
                        ['en-GB'] == question.replace("qc_", "qi_")]
        if len(questionStemList) == 0:
            questionStem = "QUESTION STEM UNAVAILABLE"
        elif len(questionStemList) > 1:
            questionStem = "MULTIPLE QUESTION STEMS FOUND"
        else:
            questionStem = questionStemList[0]
        print(f"Examining question stem {questionStem}, {count} of {len(allQuestionsInInputFiles)}")
        questionItems = C.search_items(
            [],
            SearchTerms=str(question.replace("qc_", "qi_")).strip(),
            SearchLatestVersion=True)['Results']
        for questionItem in questionItems:
            latestQuestionVersionJSON = C.get_item_json(
                questionItem['AgencyId'], questionItem['Identifier'])
            positionOfWaveIdentifier = re.search(
                "_w[0-9]+_", latestQuestionVersionJSON['ItemName']['en-GB'])
            questionName = latestQuestionVersionJSON['ItemName']['en-GB'][positionOfWaveIdentifier.span()[
                1]:]
            concordantQuestions = [
                x for x in questionsWithExtraNameField if x['questionName'] == questionName]
            for concordantQuestionItem in concordantQuestions:
                questionnaire = C.query_set(concordantQuestionItem['AgencyId'], concordantQuestionItem['Identifier'], item_types=[
                                            'f196cc07-9c99-4725-ad55-5b34f479cf7d'], reverseTraversal=True)
                if len(questionnaire) == 1:
                    latestQuestionnaireVersion = C.get_item_json(
                        questionnaire[0]['Item1']['Item3'], questionnaire[0]['Item1']['Item1'])
                    questionnaireName = latestQuestionnaireVersion['ItemName']['en-GB']
                elif len(questionnaire > 1):
                    questionnaireName = "MULTIPLE QUESTIONNAIRES"
                else:
                    questionnaireName = "NOT IN QUESTIONNAIRE"
                relatedVariables = C.search_relationship_byobject(concordantQuestionItem['AgencyId'], concordantQuestionItem['Identifier'], item_types=C.item_code(
                    'Variable'), Version=concordantQuestionItem['Version'], Descriptions=True)
                for relatedVariable in relatedVariables:
                    latestVariableVersion = C.get_item_xml(
                        relatedVariable['AgencyId'], relatedVariable['Identifier'])
                    latestVariableVersionJSON = C.get_item_json(
                        relatedVariable['AgencyId'], relatedVariable['Identifier'])
                    if concordantQuestionItem['Identifier'] in latestVariableVersion['Item']:
                        datasets = C.query_set(latestVariableVersion['AgencyId'],
                                              latestVariableVersion['Identifier'],
                                              item_types=[
                                                  'a51e85bb-6259-4488-8df2-f08cb43485f8'],
                                              reverseTraversal=True)
                        if len(datasets) > 1:
                            print(f"""WARNING: Variable in study {latestVariableVersion['AgencyId']}, with 
                               identifier {latestVariableVersion['Identifier']} is present in two datasets.""")
                        for dataset in datasets:
                            datasetItem = C.get_item_xml(dataset['Item1']['Item3'],
                                                     dataset['Item1']['Item1'],
                                                     version=dataset['Item1']['Item2'])
                            datasetTitle = get_element_by_name(
                                defusedxml.ElementTree.fromstring(datasetItem['Item']), 'Title')
                            variableName = latestVariableVersionJSON['ItemName']['en-GB']
                            if len(datasets) > 1:
                                variableName = variableName + " - DUPLICATED ACROSS MULTIPLE DATASETS"
                            variableLabel = latestVariableVersionJSON['Label']['en-GB']
                            questionLabel = concordantQuestionItem['Label']['en-GB']
                            questionSummary = concordantQuestionItem['Summary']['en-GB']
                            fw.write(questionnaireName + "," + concordantQuestionItem['ItemName']['en-GB'] + ",\"" + questionLabel + "\"" + ",\"" + questionStem + "\"" +
                                 ",\"" + questionSummary + "\"" + ",\"" + variableName + "\"" + ",\"" + variableLabel + "\"" + ",\"" + datasetTitle['String'] + "\"\n")
                            print(questionnaireName + "," + concordantQuestionItem['ItemName']['en-GB'] + ",\"" + questionLabel + "\"" + ",\"" + questionStem + "\"" +
                              ",\"" + questionSummary + "\"" + ",\"" + variableName + "\"" + ",\"" + variableLabel + "\"" + ",\"" + datasetTitle['String'] + "\"\n")
    fw.close()
