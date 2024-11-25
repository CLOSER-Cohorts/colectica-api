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
import json


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

    if codelist_df_list == []:
        df_codelist_all = pd.DataFrame()
    else:
        df_codelist_all = pd.concat(codelist_df_list)

    if response_df_list == []:
        df_response_all = pd.DataFrame()
    else:
        df_response_all = pd.concat(response_df_list)

    return instrument_info, df_question_all, df_codelist_all, df_response_all


def from_instrument_get_statement(C, Agency, ID):
    """
    From an instrument get all Statement
    """
    df_instrument_set, instrument_info = C.item_info_set(Agency, ID)

    df_statement = df_instrument_set.loc[(df_instrument_set.ItemType == 'Statement') , :]

    statement_df_list = []
    for statement_id in df_statement['Identifier']:
        dict_statement = C.item_to_dict(Agency, statement_id)
        df_statement = pd.DataFrame([dict_statement], columns=dict_statement.keys()) 
        statement_df_list.append(df_statement)
    if not statement_df_list == []:
        df_statement_all = pd.concat(statement_df_list)
    else:
        df_statement_all = pd.DataFrame(columns=['AgencyId', 'Version', 'Identifier', 'URN', 'SourceId', 'Instruction', 'Label', 'Literal'])
    return df_statement_all


def main():
    outdir = 'instrument'
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


    # get all instruments
#    L = C.search_items(C.item_code('Instrument'))
#    print(L['TotalResults'])

#    json.dump(L, open(os.path.join(outdir, 'all_instrument.txt'),'w'))

    L = json.load(open(os.path.join(outdir, 'all_instrument.txt')))
#    print(L)

    all_idx = np.array(range(L['TotalResults']))
    # split into 10 chunks
    chunks = np.array_split(all_idx, 10)

    this_chunk = 9

    for i in chunks[this_chunk]:
        print(i)
        Agency = L['Results'][i]['AgencyId']
        ID = L['Results'][i]['Identifier']
        Version = L['Results'][i]['Version']

        instrument_name = '_'.join(' '.join(L['Results'][i]['ItemName'].values()).split(' '))
        instrument_dir = os.path.join(outdir, instrument_name)
        if not os.path.exists(instrument_dir):
            os.makedirs(instrument_dir)

        # From an instrument get all questions, all response, print to file
        instrument_info, df_question_all, df_codelist_all, df_response_all = from_instrument_get_question_response(C, Agency, ID)

        with open(os.path.join(instrument_dir, 'instrument.txt'), 'w') as f:
            print(instrument_info, file=f)

        df_question_all.to_csv(os.path.join(instrument_dir, 'question.csv'), index=False, sep='\t')
        df_codelist_all.to_csv(os.path.join(instrument_dir, 'codelist.csv'), index=False, sep='\t')
        df_response_all.to_csv(os.path.join(instrument_dir, 'response.csv'), index=False, sep='\t')

        # From an instrument get all statements
        df_statement_all = from_instrument_get_statement(C, Agency, ID)
        df_statement_out = df_statement_all.loc[:, ['AgencyId', 'Version', 'Identifier', 'URN', 'SourceId', 'Instruction', 'Label', 'Literal']]
        df_statement_out.to_csv(os.path.join(instrument_dir, 'statement.csv'), index=False, sep='\t')


if __name__ == '__main__':
    main()

