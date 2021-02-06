#!/usr/bin/env python3

"""
Python 3
    Try to get all questions from an instrument
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd
import os
import numpy as np


def get_all_series(C):
    """
    Get a list of all series
    """
    all_series = C.general_search(C.item_code('Series'),'',MaxResults=0)['Results']
    return all_series


def from_series_get_study(C, Agency, ID):
    """
    From a series, get list of studies
    """
    d = C.item_to_dict(Agency, ID)
    return d['study'] 


def from_study_get_instrument(C, Agency, ID):
    """
    From a study, get instrument and Mode of Data Collection
    """
    d = C.item_to_dict(Agency, ID)

    c = C.item_to_dict(d['Data Collection']['Agency'], d['Data Collection']['ID'])
    name = c['Name']
    mode_list = [c['CollectionEvent']['ModeOfCollection'][i]['TypeOfMode'] for i in range(len(c['CollectionEvent']['ModeOfCollection']))]

    if 'InstrumentReferences' in c['Ref'].keys():
        instrument_urn = c['Ref']['InstrumentReferences']
    else:
        instrument_urn = None
    return name, instrument_urn, mode_list


def get_instruments_df(C):
    """
    From series, return a dataframe of instrument/mode_list
    """
    all_series = get_all_series(C)

    df = pd.DataFrame(columns=['study_name', 'instrument_name', 'instrument_urn', 'data_collection_mode'])   
    for s in all_series:
        # print("*****")
        study_name = list(s['ItemName'].values())[0]
        # print('series')
        # print(s['AgencyId'], s['Identifier'])
        all_studies = from_series_get_study(C, s['AgencyId'], s['Identifier'])

        for st in all_studies:
            # print("======")
            # print('studies')
            # print(st['Agency'], st['ID'])
            name, instrument_urn, mode_list = from_study_get_instrument(C, st['Agency'], st['ID'])
            df = df.append({'study_name': study_name,
                            'instrument_name': name, 
                            'instrument_urn': instrument_urn,
                            'data_collection_mode': mode_list},
                           ignore_index=True)
    lst_col = 'data_collection_mode'
    df_unlist = pd.DataFrame({col:np.repeat(df[col].values, df[lst_col].str.len()) 
                              for col in df.columns.difference([lst_col])}).assign(**{lst_col:np.concatenate(df[lst_col].values)})[df.columns.tolist()]

    return df_unlist


def from_instrument_get_question_response(C, Agency, ID):
    """
    From an instrument get all questions, all response
    """

    df_instrument_set, instrument_info = C.item_info_set(Agency, ID)

    df_question = df_instrument_set.loc[(df_instrument_set.ItemType == 'Question') , :]

    question_df_list = []
    codelist_df_list = []
    response_df_list = []
    for question_id in df_question['Identifier']:
        # print(question_id)
        df_question, df_response = C.get_question_all(Agency, question_id)
        # store DataFrame in list
        question_df_list.append(df_question)

        if df_question['response_type'][0] == 'CodeList':
            codelist_df_list.append(df_response)
        else:
            response_df_list.append(df_response)

    df_question_all = pd.concat(question_df_list)
    df_codelist_all = pd.concat(codelist_df_list)
    df_response_all = pd.concat(response_df_list)
    return instrument_info, df_question_all, df_codelist_all, df_response_all


def main():
    outdir = 'output'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    hostname = None
    username = None
    password = None
    if not hostname:
        hostname = input ("enter the url of the site: ")
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)

    df = get_instruments_df(C)
    df.to_csv(os.path.join(outdir, 'instrument_mode_data_collection.csv'), index=False, sep=';')

#    df = pd.read_csv(os.path.join(outdir, 'instrument_mode_data_collection.csv'), sep=';')

    # using instrument_mode_data_collection file to filter
    df_face = df.loc[(df.data_collection_mode == 'Interview.FaceToFace.PAPI') & (df.study_name == '1970 British Cohort Study'), :]
    # loop over all instruments here
    for index, row in df_face.iterrows():
        instrument_name = row['instrument_name']
        instrument_dir = os.path.join(outdir, instrument_name)
        if not os.path.exists(instrument_dir):
            os.makedirs(instrument_dir)

        urn = row['instrument_urn'].split(':')
        Agency = urn[2]
        ID = urn[3]
        Version = urn[4]

        # From an instrument get all questions, all response, print to file
        instrument_info, df_question_all, df_codelist_all, df_response_all = from_instrument_get_question_response(C, Agency, ID)

        with open(os.path.join(instrument_dir, 'instrument.txt'), 'w') as f:
            print(instrument_info, file=f)

        df_question_all.to_csv(os.path.join(instrument_dir, 'question.csv'), index=False, sep=';')
        df_codelist_all.to_csv(os.path.join(instrument_dir, 'codelist.csv'), index=False, sep=';')
        df_response_all.to_csv(os.path.join(instrument_dir, 'response.csv'), index=False, sep=';')


if __name__ == '__main__':
    main()

