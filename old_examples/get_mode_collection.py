#!/usr/bin/env python3

"""
Python 3
    Get all study, instrument and Mode of Data Collection
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
    all_series = C.search_items(C.item_code('Series'), MaxResults=0)['Results']
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


if __name__ == '__main__':
    main()

