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


def generate_sequence_d(sequence_file):
    """
    Generate a dictionary for Sequence and QuestionConstruct (Statement / IfThenElse etc.) 
    """
    L_seq = json.load(open(sequence_file))

    d_seq = {}
    for dict_item in L_seq:
        item = item_to_dict(dict_item)

        for ref_item in item['references']:
            ref_urn = 'urn:ddi:' + ref_item['Agency'] + ':' + ref_item['ID'] + ':' + ref_item['Version']
            d_item = {}
            d_item['RefType'] = ref_item['Type']
            d_item['SequenceURN'] = item['URN']
            d_item['SequenceID'] = item['SourceId']
            d_item['SequenceCCName'] = item['ConstructName']
            d_item['SequenceLabel'] = item['Label']

            d_seq[ref_urn] = d_item

    pd.DataFrame.from_dict(d_seq, orient='index').to_csv('tmp_seq.csv', sep='\t')
    return d_seq


def generate_question_activity(question_activity_file):
    """
    Generate a df for question item / question construct
    """
    L_qa = json.load(open(question_activity_file))

    df_qa_columns = ['QuestionURN', 'QuestionType', 'QCURN', 'QCID', 'QCName', 'QCLabel']
    df_qa = pd.DataFrame(columns=df_qa_columns)

    for dict_item in L_qa:
        item = item_to_dict(dict_item)

        ref_urn = 'urn:ddi:' + item['QuestionReference']['Agency'] + ':' + item['QuestionReference']['ID'] + ':' + item['QuestionReference']['Version']
        df_qa.loc[len(df_qa)] = [ref_urn,
                                 item['QuestionReference']['TypeOfObject'],
                                 item['URN'],
                                 item['UserID'],
                                 item['ConstructName'],
                                 item['Label']
                                ]
    return df_qa


def generate_condition_d(condition_file):
    """
    Generate a dictionary for conditions
    """
    L_con = json.load(open(condition_file))
    d_con = {}

    for dict_item in L_con:
        item = item_to_dict(dict_item)

        for ref in item['IfThenReference']:
            d_item = {}
            if ref != {}:
                ref_urn = 'urn:ddi:' + ref['Agency'] + ':' + ref['ID'] + ':' + ref['Version']
                d_item['ConditionID'] = item['UserID']
                d_item['ConConstructName'] = item['ConstructName']
                d_item['URN'] = item['URN']

                d_con[ref_urn] = d_item
    # pd.DataFrame.from_dict(d_con, orient='index').to_csv('tmp_c.csv', sep='\t')
    return d_con


def generate_loop_d(loop_file):
    """
    Generate a dictionary for loop
    """
    L_loop = json.load(open(loop_file))
    d_loop = {}

    for dict_item in L_loop:
        item = item_to_dict(dict_item)
        ref = item['ControlConstructReference']
        d_item = {}
        if ref != {}:
            ref_urn = 'urn:ddi:' + ref['Agency'] + ':' + ref['ID'] + ':' + ref['Version']
            d_item['LoopConstructName'] = item['ConstructName']
            d_item['URN'] = item['URN']

            d_loop[ref_urn] = d_item
    # pd.DataFrame.from_dict(d_loop, orient='index').to_csv('tmp_loop.csv', sep='\t')
    return d_loop


def get_question_nearest_section(sequence_file, condition_file, loop_file, question_activity_file):
    """
    Generate a df for question item and it's nearest section label
    """
    d_seq = generate_sequence_d(sequence_file)
    if os.path.isfile(condition_file):
        d_con = generate_condition_d(condition_file)
    else:
        d_con = {}
    if os.path.isfile(loop_file):
        d_loop = generate_loop_d(loop_file)
    else:
        d_loop = {}

    # find nearest section
    # if it is condition, then keep looking
    d_section = d_seq
    for k in d_seq.keys():
        seq_name = d_section[k]['SequenceCCName']

        while seq_name is not None and seq_name.startswith(('else', 'then')):
            for key, value in d_con.items():
                if d_section[k]['SequenceURN'] == key:
                    c_urn = value['URN']
                    d_section[k] = d_seq[c_urn]
                    seq_name = d_section[k]['SequenceCCName']

        while seq_name is not None and seq_name.startswith('loop'):
            for key, value in d_loop.items():
                if d_section[k]['SequenceURN'] == key:
                    l_urn = value['URN']
                    d_section[k] = d_seq[l_urn]
                    seq_name = d_section[k]['SequenceCCName']

    df_seq_nearest = pd.DataFrame.from_dict(d_section, orient='index')
    # replace tab with space in Sequence Label
    df_seq_nearest['SequenceLabel'] = df_seq_nearest['SequenceLabel'].replace('\t', ' ', regex=True)

    df_qa = generate_question_activity(question_activity_file)
    df = df_qa.merge(df_seq_nearest, how='left', left_on='QCURN', right_index=True)
    return df.loc[:, ['QuestionURN', 'SequenceLabel', 'SequenceURN']]


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
        instrument_label = item['InstrumentLabel']

    df_seq = get_question_nearest_section(os.path.join(study_dir, 'Sequence.txt'),
                                          os.path.join(study_dir, 'Conditional.txt'),
                                          os.path.join(study_dir, 'Loop.txt'),
                                          os.path.join(study_dir, 'Question Activity.txt'))

    # if the nearest section is the instrument, then make it None
    def remove_instrument_id(row, instrument_label): #row is the value of row.
        if row['SequenceLabel'] == instrument_label:
            row['SequenceLabel'] = None
            row['SequenceURN'] = None
        return row
    df_seq = df_seq.apply(lambda row: remove_instrument_id(row, instrument_label), axis=1)

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

    # merge with sequence
    df_new = df.merge(df_seq, how='left', left_on='QuestionURN', right_on='QuestionURN')
    df_new.rename(columns={'SequenceLabel': 'SectionLabel',
                           'SequenceURN': 'SectionURN'}, inplace=True)

    # re order columns
    df_new = df_new[['InstrumentURN', 'Instrument', 'SectionURN', 'SectionLabel', 'QuestionGroupURN', 'QuestionGroupName', 'QuestionGroupLabel',
                     'QuestionURN', 'QuestionLiteral', 'ResponseType', 'Response']]

    return df_new


def main():

    # question group
    df_qg = pd.read_csv('question_group/question_group_all.csv', sep='\t')

    # rename covid name / label
    df_qg_name = df_qg.loc[:, ['QG_Name', 'QG_Label']].drop_duplicates()
    name_dict = dict(zip(df_qg_name.QG_Name, df_qg_name.QG_Label))

    def modify_qg_name(row, name_dict):
        """
        modify covid ones to be with original type
        i.e. 11601 -> 101, 11602 -> 102
        also 10809 -> 10405
        """
        if (11600 <= row['QG_Name']) & (row['QG_Name'] < 11700):
            new_name = row['QG_Name'] - 11500
            new_label = name_dict[new_name]
        elif row['QG_Name'] == 10809:
            new_name = 10405
            new_label = name_dict[new_name]
        else:
            new_name = row['QG_Name']
            new_label = row['QG_Label']
        return pd.Series([new_name, new_label])

    df_qg[['new_name', 'new_label']] = df_qg.apply(lambda row: modify_qg_name(row, name_dict), axis=1)

    # delete old / rename new columns
    df_qg.drop(['QG_Name', 'QG_Label'], axis=1, inplace=True)
    df_qg.rename(columns={'new_name': 'QG_Name', 'new_label': 'QG_Label'}, inplace=True)


    top_dir = 'instrument_dict_20210421'
    dir_list = [os.path.join(top_dir, o) for o in os.listdir(top_dir) if os.path.isdir(os.path.join(top_dir,o))]

    appended_data = []
    #dir_list = ['instrument_dict_20210421/nshd_52_iwm-in-001211']
    for study_dir in dir_list:
        print(study_dir)
        df = get_one_study(study_dir, df_qg)
        appended_data.append(df)

    df_all = pd.concat(appended_data)
    df_all.to_csv('RCNIC.csv', sep='\t', index=False)


if __name__ == '__main__':
    main()
