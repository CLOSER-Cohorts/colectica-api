#!/usr/bin/env python3

"""
find all studies.
for each study, the numbers for each top level topic and each lifestage

study -> variables?

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


def get_all_Series(C):
    """
    return result from item search on Series
    """
    r  = C.search_item("4bd6eef6-99df-40e6-9b11-5b8f64e5cb23", '', 0)
    return r
    
    
def Series_to_StudyUnits(C, AgencyId, Identifier):
    """
    return all studies from Series
    """
    d = C.get_an_item_json(AgencyId, Identifier)
    return d['StudyUnits']
    

def main():
    outdir = 'Study_Variable'
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
 

    list_df_s = []
    # find all series
    series = get_all_Series(C)
    i = 1
    for s in series['Results']:

        series_name = s['ItemName']['en-GB']
        agency_name = s['AgencyId']
        
        print(series_name)
        studies = Series_to_StudyUnits(C, s['AgencyId'], s['Identifier'])
        list_df = []
        for study in studies:
            
            study_AgencyId = study['AgencyId']
            study_Identifier = study['Identifier']
            study_Version = study['Version']
            
            d_study = C.get_an_item_json(study_AgencyId, study_Identifier)
            # Stuey name
            study_name = d_study['ItemName']['en-GB']
            print(study_name)
            
            # Life Stage
            # 'LIfeStageDescription': for ("uk.cls.ncds",  "913c215c-1dc9-4df8-a893-e85890f1af5b")
            CustomFields = d_study['CustomFields']
            # life = [{key: item[key] for key in ['DisplayLabel', 'StringValue']} for item in l ]
            # [LifeStage_d, LifeStageDescription_d] = [{item['DisplayLabel']: item['StringValue']} for item in CustomFields]
            
            if len(CustomFields) == 2:
                [LifeStage, LifeStageDescription] = [item['StringValue'] for item in CustomFields]
            elif len(CustomFields) == 1:
                LifeStage = CustomFields[0]['StringValue']
                LifeStageDescription = ''
            else:
                print('Check CustomFields')
                print(CustomFields)
  
            # all Variables
            
            l = C.get_a_set_typed(study_AgencyId, study_Identifier, str(study_Version))
            if l is not None:
                df = pd.DataFrame([C.item_code_inv(l[i]["Item2"]), l[i]["Item1"]["Item3"], l[i]["Item1"]["Item1"], l[i]["Item1"]["Item2"]] for i in range(len(l)))
                df.columns = ['Type', 'Variable_Agency', 'Variable_Id', 'Variable_Version']
                df_variable = df[df['Type'] == 'Variable']
            
                df_variable['Study_Agency'] = study_AgencyId
                df_variable['Study_Id'] = study_Identifier
                df_variable['Study_Version'] = study_Version
            
                df_variable['LifeStage'] = LifeStage
                df_variable['LifeStageDescription'] = LifeStageDescription
            
                df_variable['Study_Agency'] = study_AgencyId
                df_variable['Study_Id'] = study_Identifier
                df_variable['Study_Version'] = study_Version  
                df_variable['Study_Name'] = study_name
            
                df_variable['Series_Name'] = series_name
            
                list_df.append(df_variable)
                list_df_s.append(df_variable)
        
        appended_data = pd.concat(list_df)
        appended_data.to_csv(os.path.join(outdir, '{}_{}.csv'.format(i, agency_name)), sep='\t', index=False)
        i = i + 1
        print(appended_data.groupby(['Series_Name','Study_Name', 'LifeStage']).size())
        
    
    df_all = pd.concat(list_df_s)
    df_all.to_csv(os.path.join(outdir, 'study_variables.csv'.format(i, agency_name)), sep='\t', index=False)
    

if __name__ == '__main__':
    main()
