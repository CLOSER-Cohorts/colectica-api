#!/usr/bin/env python3

"""
Python 3
    Using output from instrument_to_dict.py
    Combine to RCNIC format
"""
import api
import colectica
import pandas as pd
import os
import numpy as np
from pandas.io.json import json_normalize
import json


def item_to_dict(dict_item):
    """
    Flat out item in dict_item
    """
    info = {}
    item_info = None

    for k, v in dict_item.items():
        if k == 'ItemType':
            info[k] = api.item_dict_inv[dict_item['ItemType']]
        elif k == 'Item':
            item_info = colectica.parse_xml(v, api.item_dict_inv[dict_item['ItemType']])
        else:
            info[k] = v
    d = {**info, **item_info}
    return d


def generate_category_dict(category_file):
    """
    Generate a dictionary for code category
    """
    L = json.load(open(category_file))
    d = {}
    for dict_item in L:
        item = item_to_dict(dict_item)
        if not item['Label'] is None:
            d[item['URN']] = item['Label']
        else:
            d[item['URN']] = ''
    return d


def generate_code_dict(code_file, category_dict):
    """
    Generate a dictionary for code
    """
    L = json.load(open(code_file))
    d = {}
    for dict_item in L:
        item = item_to_dict(dict_item)
        a = []
        for code in item['Code']:
            cat_urn = 'urn:ddi:' + code['CategoryReference']['Agency'] + ':' + code['CategoryReference']['ID'] + ':' + code['CategoryReference']['Version']
            if not code['Value'] is None:
                category = code['Value'] + ', ' + category_dict[cat_urn]
            else:
                category = category_dict[cat_urn]
            a.append(category)
        d[item['URN']] = ' | '.join(a)

    return d


def get_one_study(study_dir, df_qg):
    """
    Questions from one study
    """
    list_files = os.listdir(study_dir)

    df_columns = ['InstrumentURN', 'Instrument', 'QuestionURN', 'QuestionLiteral', 'ResponseType', 'Response']
    df_q = pd.DataFrame(columns=df_columns)

    instrument_dict = {}
    if 'Instrument.txt' in list_files:
        L = json.load(open(os.path.join(study_dir, 'Instrument.txt')))
        item = item_to_dict(L[0])
        instrument_dict['instrument_urn'] = item['InstrumentURN']
        instrument_dict['instrument_name'] = item['InstrumentName']

    if 'Category.txt' in list_files:
        category_dict = generate_category_dict(os.path.join(study_dir, 'Category.txt'))
    else:
        category_dict = []

    if 'Code Set.txt' in list_files:
        code_dict = generate_code_dict(os.path.join(study_dir, 'Code Set.txt'), category_dict)
    else:
        code_dict = []

    if 'Question.txt' in list_files:
        L = json.load(open(os.path.join(study_dir, 'Question.txt')))

        for dict_item in L:
            item = item_to_dict(dict_item)
            if not item['QuestionLiteral'] is None:
                literal = item['QuestionLiteral'].replace('\n', '')
            else:
                literal = None

            if item['Response'] == {}:
                response_type = None
                response = None
            elif item['Response']['response_type'] != 'CodeList':
                response_type = item['Response']['response_type']
                response = None
            elif item['Response']['response_type'] == 'CodeList':
                response_type = item['Response']['response_type']
                response = code_dict[item['Response']['code_list_URN']]

            df_q.loc[len(df_q)] = [instrument_dict['instrument_urn'],
                                   instrument_dict['instrument_name'],
                                   item['QuestionURN'],
                                   literal,
                                   response_type,
                                   response]

    # merge with question group
    df = df_q.merge(df_qg.loc[:, ['QI_URN', 'QG_URN', 'QG_Name', 'QG_Label']], how='left', left_on='QuestionURN', right_on='QI_URN')
    df = df.drop('QI_URN', 1)

    df.rename(columns={'QG_URN': 'QuestionGroupURN',
                       'QG_Name': 'QuestionGroupName',
                       'QG_Label': 'QuestionGroupLabel'}, inplace=True)

    # re order columns
    df = df[['InstrumentURN', 'Instrument', 'QuestionGroupURN', 'QuestionGroupName', 'QuestionGroupLabel',
             'QuestionURN', 'QuestionLiteral', 'ResponseType', 'Response']]

    return df


def main():
    # question group
    df_qg = pd.read_csv('question_group/question_group_all.csv', sep='\t')

    top_dir = 'instrument_dict_original'
    dir_list = [os.path.join(top_dir, o) for o in os.listdir(top_dir) if os.path.isdir(os.path.join(top_dir,o))]

    appended_data = []
    for study_dir in dir_list:
        print(study_dir)
        df = get_one_study(study_dir, df_qg)
        appended_data.append(df)

    df_all = pd.concat(appended_data)
    df_all.to_csv('RCNIC.csv', sep='\t', index=False)

if __name__ == '__main__':
    main()
