#!/usr/bin/env python3

"""
Python 3
    Using output from instrument_to_dict.py
    Combine to ESRC format
"""
import colectica
import api
import pandas as pd
import os
import numpy as np
from pandas.io.json import json_normalize
import json


def root_to_dict_interviewer_instruction(root):
    """
    Part of parse xml, item_type = Interviewer Instruction
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    info['UserID'] = root.find('.//UserID').text
    info['InstructionText'] = root.find('.//InstructionText/LiteralText/Text').text
    return info


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


def get_one_study(study_dir):
    """
    output for one study
    """
    df_columns = ['item_type', 'item_urn', 'content']
    df = pd.DataFrame(columns=df_columns)

    # category urn and label
    list_files = os.listdir(study_dir)

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

    for input_file in list_files:

        filename = os.path.splitext(input_file)[0]

        L = json.load(open(os.path.join(study_dir, input_file)))

        if filename == 'Question':
            for dict_item in L:
                item = item_to_dict(dict_item)
                if not item['QuestionLiteral'] is None:
                    literal = item['QuestionLiteral'].replace('\n', '')
                else:
                    literal = None
                df.loc[len(df)] = ['question',  item['QuestionURN'], literal]
                df.loc[len(df)] = ['question name', None, item['QuestionLabel']]

                if item['Response'] != {} and item['Response']['response_type'] != 'CodeList':
                    df.loc[len(df)] = [item['Response']['response_type'], None, item['Response']['response_label']]

        elif filename == 'Interviewer Instruction':
            for dict_item in L:
                item = item_to_dict(dict_item)
                df.loc[len(df)] = ['instruction', item['InstructionURN'], item['InstructionText']]

        elif filename == 'Code Set' and category_dict != []:
            for dict_item in L:
                item = item_to_dict(dict_item)
                for code in item['Code']:
                    if code['Value'] is None:
                        code['Value'] = ''
                    cat_urn = 'urn:ddi:' + code['CategoryReference']['Agency'] + ':' + code['CategoryReference']['ID'] + ':' + code['CategoryReference']['Version']
                    df.loc[len(df)] = ['codelist', code['URN'], code['Value'] + ', ' + category_dict[cat_urn]]

        elif filename == 'Statement':
            for dict_item in L:
                item = item_to_dict(dict_item)
                df.loc[len(df)] = ['statement', item['StatementURN'], item['Literal']]

        elif filename == 'Conditional':
            for dict_item in L:
                item = item_to_dict(dict_item)
                df.loc[len(df)] = ['conditional', item['URN'], item['IfCondition']['Description'] + item['IfCondition']['CommandContent'] if not item['IfCondition']['CommandContent'] is None else item['IfCondition']['Description']]

        elif filename == 'Loop':
            for dict_item in L:
                item = item_to_dict(dict_item)
                df.loc[len(df)] = ['loop', item['URN'], item['LoopWhile']['CommandContent']]

        else:
            # TODO
            print(filename)

    df = df.drop_duplicates(keep='first')
    df['instrument_name'] = instrument_dict['instrument_name']
    df['instrument_urn'] = instrument_dict['instrument_urn']
    return df


def main():
    top_dir = 'instrument_dict_original'
    dir_list = [os.path.join(top_dir, o) for o in os.listdir(top_dir) if os.path.isdir(os.path.join(top_dir,o))]

    appended_data = []
    for study_dir in dir_list:
        print(study_dir)
        df = get_one_study(study_dir)
        appended_data.append(df)

    df_all = pd.concat(appended_data)

    # remove response domain: Test, Numeric, DateTime
    df_sub = df_all[~df_all['item_type'].isin(['Text', 'Numeric', 'DateTime'])]
    df_sub.to_csv('ESRC_no_response.csv', sep='\t', index=False)

if __name__ == '__main__':
    main()
