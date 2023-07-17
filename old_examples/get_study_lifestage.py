#!/usr/bin/env python3

"""
find all studies.
for each study, the numbers for each top level topic and each lifestage

study -> variables?

study -> instrument

question group -> question item/ question group

instrument to question item??
"""

import colectica
from colectica import ColecticaObject
import api
from pathlib import Path
import pandas as pd
import json
import os
import pprint

pp = pprint.PrettyPrinter(depth=4)


def get_all_Variable_Group(C, VG_text_file):
    """
    return a text file contains all studies
    """
    r  = C.search_item("91da6c62-c2c2-4173-8958-22c518d1d40d", '', 0)
    # print(r['TotalResults'])
    json.dump(r, open(VG_text_file, 'w'))
    
    
def get_top_level_Variable_Group(C, VG_text_file, VG_text_file_name):
    """
    loop over all Variable group, find the top level ones
    """
    L = json.load(open(VG_text_file))
    
    #pp.pprint(L)
    print(L['TotalResults'])
    
    # subset to contains ItemName
    L_name = [obj for obj in L['Results'] if(obj['ItemName'] != {})]
    # too level only
    L_top = [obj for obj in L_name if (len(obj['ItemName']['en-GB']) == 3)]

    json.dump(L_top, open(VG_text_file_name, 'w'))
        
       
def get_all_studies(C, study_text_file):
    """
    return a text file contains all studies
    """
    study = "30ea0200-7121-4f01-8d21-a931a182b86d"
    r  = C.search_item(study, '', 0)
    # print(r['TotalResults'])
    json.dump(r, open(study_text_file, 'w'))


#def get_info_from_VG(C, row):
def get_info_from_VG(C, AgencyId, Identifier):
    """
    For each Variable Group, get 
    """
   # d = C.get_an_item_json(row['AgencyId'], row['Identifier'])
    d = C.get_an_item_json(AgencyId, Identifier)
    
    VariableAgency = AgencyId
    VariableId = Identifier
    print(AgencyId, Identifier)
    
    # uk.cls.mcs f2665066-c11f-48dd-a52b-c90d4f40fb6d returns nothing?
    
    VariableName = ''
    VariableLabel = ''
    VariableVersion = None

    if d is not None:
        if d['ItemName'] != {}:
            VariableName = d['ItemName']['en-GB']
        if d['Label'] != {}:
            VariableLabel = d['Label']['en-GB']
        if d['Version'] is not None:
            VariableVersion = d['Version']

    QuestionAgency = ''
    QuestionId = ''
    QuestionVersion = None
    QuestionName = ''
    QuestionLabel = ''
    
    col_name = ['VariableAgency', 'VariableId', 'VariableVersion', 'VariableName', 'VariableLabel', 'QuestionAgency', 'QuestionId', 'QuestionVersion', 'QuestionName', 'QuestionLabel']
                
    df = pd.DataFrame(columns = col_name)
    if d is not None:
        if d['SourceQuestions'] != []:
            # print("SourceQuestions")
            d_prepare = []
            for i, QI in enumerate(d['SourceQuestions']):
                d_question = C.get_an_item_json(QI['AgencyId'], QI['Identifier'])
                QuestionAgency = d_question['AgencyId']
                QuestionId = d_question['Identifier']
                QuestionVersion = d_question['Version']
                QuestionName = d_question['ItemName']['en-GB']
                QuestionLabel = d_question['Label']['en-GB']
                d_prepare.append(
                    {
                    'VariableAgency': VariableAgency,
                    'VariableId': VariableId,
                    'VariableVersion': VariableVersion,
                    'VariableName': VariableName,
                    'VariableLabel': VariableLabel,
                    'QuestionAgency':  QuestionAgency,
                    'QuestionId': QuestionId,
                    'QuestionVersion': QuestionVersion,
                    'QuestionName': QuestionName,
                    'QuestionLabel': QuestionLabel
                    }
                )

            df = pd.DataFrame(d_prepare)
    
        elif d['SourceQuestionGrids'] != []:
            print('SourceQuestionGrids')
            #pp.pprint(C.get_an_item_json(d['SourceQuestions']['AgencyId'], d['SourceQuestions']['Identifier']))
        
        elif d['SourceQuestionBlocks'] != []:
            print('SourceQuestionBlocks')
            #pp.pprint(C.get_an_item_json(d['SourceQuestions']['AgencyId'], d['SourceQuestions']['Identifier']))
        else:
            print('ELSE')
            #pp.pprint(d)
    
    #return [VariableName, VariableLabel, QuestionAgency, QuestionId, QuestionVersion, QuestionName, QuestionLabel]
    return df


def append_files_from_dir(indir):
    """
    Append all files in a directory
    """
    input_files = [i for i in os.listdir(indir) if i.startswith('VG')]
    appended_df = []
    for input_file in input_files:
        df = pd.read_csv(os.path.join(indir, input_file), sep='\t')
        appended_df.append(df)
    appended_data = pd.concat(appended_df)
    appended_data.to_csv(os.path.join(indir, 'variable_group_all.csv'), sep='\t', index=False)


def main():
    outdir = 'Study_lifestage'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    hostname = 'clsr-ppcolw01n.addev.ucl.ac.uk'
    username = None
    password = None

    if not hostname:
        hostname = input ("enter the url of the site: ")
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)
    """

    VG_text_file = os.path.join(outdir, 'Variable_Group.txt')
    get_all_Variable_Group(C, VG_text_file)
    L = json.load(open(VG_text_file))
    pp.pprint(L)

    """
    VG_text_file = os.path.join(outdir, 'Variable_Group.txt')
    VG_text_file_name = os.path.join(outdir, 'Variable_Group_top_level.txt')
    """
    # get all Variable Group
    # get_all_Variable_Group(C, VG_text_file)
    # filter to top level Variable Group
    # get_top_level_Variable_Group(C, VG_text_file, VG_text_file_name)
    """
    L = json.load(open(VG_text_file_name))
    print(len(L))
    #pp.pprint(L)
    
    import numpy as np
    all_idx = np.array(range(len(L)))
    # split into 10 chunks
    chunks = np.array_split(all_idx, 10)

    this_chunk = 3

    appended_df = []
    
    for i in chunks[this_chunk] :
        print(i)
        agency = L[i]['AgencyId']
        Id = L[i]['Identifier']
        # print(agency)
        # print(Id)
        df, info = C.item_info_set_json(agency, Id)
        
        if info['Items'] != []:
            if len(info['ItemName']['en-GB']) == 3:
                
                df_VG = pd.DataFrame(info['Items'])
                                
                df_VG['VG_Agency'] = info['AgencyId']
                df_VG['VG_Id'] = info['Identifier']
                df_VG['VG_Version'] = info['Version']
                df_VG['VG_Name'] = info['ItemName']['en-GB']
                df_VG['VG_Label'] = info['Label']['en-GB']
                
                d_concept = C.get_an_item_json(info['Concept']['AgencyId'], info['Concept']['Identifier'])
                ConceptName = ''
                ConceptLabel = ''
                if d_concept is not None:
                    df_VG['ConceptName'] = d_concept['ItemName']['en-GB']
                    df_VG['ConceptLabel'] = d_concept['Label']['en-GB']
                
                appended_df_q = []
                for index, row in df_VG.iterrows():
                    df_q = get_info_from_VG(C, row['AgencyId'], row['Identifier'])
                    appended_df_q.append(df_q)
                    
                appended_df_q_data = pd.concat(appended_df_q)
                new_df = pd.merge(df_VG, appended_df_q_data,  how='left', left_on=['AgencyId', 'Identifier'], right_on = ['VariableAgency','VariableId'])
                appended_df.append(new_df)
    appended_data = pd.concat(appended_df)
    appended_data.drop(['VariableAgency', 'VariableId', 'VariableVersion'] , axis=1, inplace=True)

    appended_data.to_csv(os.path.join(outdir, 'VG_{}.csv'.format(this_chunk)), sep='\t', index=False)
    
    # combine all VG files
    #append_files_from_dir(outdir)

if __name__ == '__main__':
    main()
