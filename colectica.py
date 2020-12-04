""" 
    Pull information using python ColecticaPortal api
"""

from io import StringIO
import xml.etree.ElementTree as ET
import pandas as pd
import api


def remove_xml_ns(xml):
    """
        Read xml from string, remove namespaces, return root
    """
    it = ET.iterparse(StringIO(xml))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix  # strip all namespaces
    root = it.root
    return root


class ColecticaObject(api.ColecticaLowLevelAPI):
    """Ask practical questions to Colectica."""

    def from_id_get_study(self, AgencyId, Identifier):
        """
        From an agency ID and an identifier, get information about a study

        example, AgencyId = 'uk.cls.nextsteps', Identifier='78572059-2541-4ce6-813f-10250a53c91b'

        Returns:
            dict: TODO words
        """
        study_result = self.get_an_item(AgencyId, Identifier)

        root = remove_xml_ns(study_result["Item"])

        study = {}
        study['version'] = study_result["Version"]
        item_type = study_result["ItemType"]
        # Sweep Description
        study['title'] = root.find(".//Citation/Title/String").text
        study['principal_investigator'] = root.find(".//Creator/CreatorName/String").text
        study['publisher'] = root.find(".//Publisher/PublisherName/String").text
        study['abstract'] = root.find(".//Abstract/Content").text
        population = {}
        population['agency'] = root.find(".//UniverseReference/Agency").text
        population['ID'] = root.find(".//UniverseReference/ID").text 
        study['population'] = population

        return study


    def from_id_get_sequence(self, AgencyId, Identifier):
        """
        From Idenfifier and ItemType Sequence, get info
        """
        sequence_result = self.get_an_item(AgencyId, Identifier)
        root = remove_xml_ns(sequence_result["Item"])
        
        seq = {}
        for k, v in sequence_result.items():
            if k == 'ItemType':
                seq[k] = self.item_code_inv(v)
            elif k == 'Item':
                seq['Sequence_Agency'] = root.find(".//ControlConstructReference/Version").text
                seq['Sequence_ID'] = root.find(".//ControlConstructReference/ID").text
                seq['Sequence_Version'] = root.find(".//ControlConstructReference/Version").text
            else:
                seq[k] = v
        return seq
        

    def get_instrument_info(self, AgencyId, Identifier):
        """
        From an instrument identifier, get information about this instrument
        """
        instrument_result = self.get_an_item(AgencyId, Identifier)
        root = remove_xml_ns(instrument_result["Item"])
        
        instrument = {}
        for k, v in instrument_result.items():
            if k == 'ItemType':
                instrument[k] = self.item_code_inv(v)
            elif k == 'Item':
                if root.findall(".//*[@typeOfUserID='colectica:sourceId']") != []:
                    instrument['InstrumentSourceID'] = root.findall(".//*[@typeOfUserID='colectica:sourceId']")[0].text 
                if root.findall(".//*[@typeOfUserID='closer:sourceFileName']") != []:
                    instrument['InstrumentLabel'] = root.findall(".//*[@typeOfUserID='closer:sourceFileName']")[0].text
                instrument['InstrumentName'] = root.find(".//InstrumentName/String").text
                instrument['ExternalInstrumentLocation'] = root.find(".//ExternalInstrumentLocation").text
                instrument['ref_agency'] = root.find(".//ControlConstructReference/Agency").text
                instrument['ref_agency'] = root.find(".//ControlConstructReference/Agency").text
                instrument['ref_ID'] = root.find(".//ControlConstructReference/ID").text
                instrument['ref_version'] = root.find(".//ControlConstructReference/Version").text
                instrument['ref_type'] = root.find(".//ControlConstructReference/TypeOfObject").text
            else:
                instrument[k] = v
        return instrument


    def get_instrument_set(self, AgencyId, Identifier, Version):
        """
        Fcloser:sourceFileNamerom a study, find all questions
        Example: 
            'ItemType': 'f196cc07-9c99-4725-ad55-5b34f479cf7d', (Instrument)
            'AgencyId': 'uk.cls.nextsteps',
            'Version': 1,
            'Identifier': 'a6f96245-5c00-4ad3-89e9-79afaefa0c28'
        """  

        l = self.get_a_set_typed(AgencyId, Identifier, Version)
        # print(l)
        df = pd.DataFrame( 
             [self.item_code_inv(l[i]["Item2"]), l[i]["Item1"]["Item1"]] for i in range(len(l))
         )
        df.columns = ["ItemType", "Identifier"]
        
        return df


    def instrument_info_set(self, AgencyId, Identifier):
        """
        From an instrument ID, find it's name and set
        """
        info = self.get_instrument_info(AgencyId, Identifier)
        df = self.get_instrument_set(AgencyId, Identifier, str(info['Version']))
        return df, info
   

    def get_question_info(self, AgencyId, Identifier):
        """
        From a question identifier, get information about it
        """
        question_result = self.get_an_item(AgencyId, Identifier)
        root = remove_xml_ns(question_result["Item"])
        
        question = {}
        for k, v in question_result.items():
            if k == 'ItemType':
                question[k] = self.item_code_inv(v)
            elif k == 'Item':
                question['UserID'] = root.find(".//UserID").text
                question['QuestionLabel'] = root.find(".//UserAttributePair/AttributeValue").text
                question['QuestionItemName'] = root.find(".//QuestionItemName/String").text
                question['QuestionLiteral'] = root.find(".//QuestionText/LiteralText/Text").text

                if root.find(".//CodeDomain") is not None:
                    question['response_type'] = 'CodeList'
                    question['CodeList_ID'] = root.find(".//CodeDomain/CodeListReference/ID").text
                    question['CodeList_version'] = root.find(".//CodeDomain/CodeListReference/Version").text
                elif root.find(".//TextDomain") is not None:
                    question['response_type'] = 'Text'
                    question['response_label'] = root.find(".//TextDomain/Label/Content").text
                elif root.find(".//NumericDomain") is not None:
                    question['response_type'] = 'Numeric'
                    question['response_label'] = root.find(".//Label").text
                    question['response_NumericType'] = root.find(".//NumericTypeCode").text
                    if root.find(".//NumberRange/Low") is not None:
                        question['response_RangeLow'] = root.find(".//NumberRange/Low").text
                    else:
                        question['response_RangeLow'] = None
                    if root.find(".//NumberRange/High") is not None:
                        question['response_RangeHigh'] = root.find(".//NumberRange/High").text
                    else:
                        question['response_RangeHigh'] = None
                         

            else:
                question[k] = v
        return question


    def get_question_all(self, AgencyId, Identifier):
        """
        From a question ID, return question info and it's response
        """
        question_info = self.get_question_info(AgencyId, Identifier)
        
        question_data = [ [ question_info['UserID'], 
                            question_info['QuestionLabel'], 
                            question_info['QuestionItemName'],
                            question_info['QuestionLiteral'],
                            question_info['response_type'] ] ]
            
        df_question = pd.DataFrame(question_data, 
                                   columns=['UserID', 'QuestionLabel', 'QuestionItemName', 'QuestionLiteral', 'response_type'])
                

        if question_info['response_type'] == 'CodeList':
            code_result = self.get_an_item(AgencyId, question_info['CodeList_ID'])
            root = remove_xml_ns(code_result["Item"])

            code_list_sourceId = root.find(".//UserID").text
            code_list_label = root.find(".//Label/Content").text

            category = [i.text for i in root.findall(".//Code/CategoryReference/ID")]

            df = pd.DataFrame(columns=["Name", "ID", "Label"])

            for c in category:
                item_result = self.get_an_item(AgencyId, c)
                root = remove_xml_ns(item_result["Item"])
        
                CategoryName = root.find(".//CategoryName/String").text 
                UserID = root.find(".//UserID").text
                Label = root.find(".//Label/Content").text
                df = df.append({"Name": CategoryName,
                                  "ID": UserID,
                               "Label": Label
                               }, ignore_index=True)
            
            df['code_list_sourceId'] = code_list_sourceId
            df['code_list_label'] = code_list_label
            df['Order'] = df.index + 1 
            df['QuestionItemName'] = question_info['QuestionItemName'] 

            df_question['response'] = code_list_label

        elif question_info['response_type'] == 'Text':
            data = [ [ question_info['QuestionItemName'], 
                       question_info['response_type'], 
                       question_info['response_label'] ] ]
            df = pd.DataFrame(data, columns=['QuestionItemName', 'response_type', 'Label'])

            df_question['response'] = question_info['response_label']

        elif question_info['response_type'] == 'Numeric':
            data = [ [ question_info['QuestionItemName'], 
                       question_info['response_type'], 
                       question_info['response_label'],
                       question_info['response_NumericType'],
                       question_info['response_RangeLow'],
                       question_info['response_RangeHigh'] ] ]
            df = pd.DataFrame(data, columns=['QuestionItemName', 'response_type', 'Label', 'response_NumericType', 'response_RangeLow', 'response_RangeHigh'])
                         
            df_question['response'] = question_info['response_label']

        else:
            print(question_info['response_type'])
            df = pd.DataFrame()
        return df_question, df

if __name__ == "__main__":
    raise RuntimeError("don't run this directly")

