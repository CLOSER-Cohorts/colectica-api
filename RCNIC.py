#!/usr/bin/env python3

"""
Gather data for RCNIC project
"""

import pandas as pd
import os

def combine_codelist(codelist_file):
    """
    Combine multiple rows into one for codelist
    """
    if os.stat(codelist_file).st_size == 1 :
        df_out = pd.DataFrame(columns=['code_list_URN', 'codelist_response'])
    else:
        df = pd.read_csv(codelist_file, sep='\t')
        df['codelist_response'] = df['Value'].astype('str') + ', ' + df['Label']

        # combine multiple rows
        df_c = df[df['codelist_response'].notna()].groupby(['QuestionURN', 'QuestionItemName', 'response_type', 'code_list_URN', 'code_list_label'])['codelist_response'].apply(' | '.join).reset_index()
        df_out = df_c.loc[:, ['code_list_URN', 'codelist_response']].drop_duplicates(keep='first')

    return df_out


def one_study(study_dir, df_qg):
    """
    Get right format for one study
    """

    df_question = pd.read_csv(os.path.join(study_dir, 'question.csv'), sep='\t')
    df_c = combine_codelist(os.path.join(study_dir, 'codelist.csv'))

    # merge question and codelist
    if 'response_domain' in df_question.columns:
        df_q = df_question.loc[:, ['QuestionURN', 'QuestionLiteral', 'response_type' ,'response', 'response_domain']]
        df_q_c = df_q.merge(df_c, how='left', left_on='response_domain', right_on='code_list_URN')
        df_q_c = df_q_c.drop('response_domain', 1)
    else:
        df_q_c = df_question
        df_q_c['codelist_response'] = None
        df_q_c['code_list_URN'] = None

    # merge with question group
    df = df_q_c.merge(df_qg.loc[:, ['QI_URN', 'QG_URN', 'QG_Name', 'QG_Label']], how='left', left_on='QuestionURN', right_on='QI_URN')
    df = df.drop('QI_URN', 1)

    # combine response
    if 'response' in df.columns:
        df['response_new'] = df.apply(lambda row: row['codelist_response'] if row['response_type'] == 'CodeList' else row['response'], axis=1)
        df = df.drop(['codelist_response', 'response', 'code_list_URN'], 1)
    else:
        df['response_new'] = df.apply(lambda row: row['codelist_response'] if row['response_type'] == 'CodeList' else None, axis=1)
        df = df.drop(['codelist_response', 'code_list_URN'], 1)

    df.rename(columns={'response_new': 'Response',
                       'response_type': 'ResponseType',
                       'QG_URN': 'QuestionGroupURN',
                       'QG_Name': 'QuestionGroupName',
                       'QG_Label': 'QuestionGroupLabel'}, inplace=True)

    # add instrument label
    d = eval(open(os.path.join(study_dir, 'instrument.txt'), 'r').read())
    df['Instrument'] = d['InstrumentLabel']
    df['InstrumentURN'] = d['URN']

    # re order columns
    df = df[['InstrumentURN', 'Instrument', 'QuestionGroupURN', 'QuestionGroupName', 'QuestionGroupLabel',
             'QuestionURN', 'QuestionLiteral', 'ResponseType', 'Response']]

    return df


def fast_scandir(dirname):
    """
    List all subfolder recursively
    """
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


def main():

    outdir= 'RCNIC'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    df_qg = pd.read_csv('question_group/question_group_all.csv', sep='\t')
    indir = 'instrument'
    # all_studies = [ f.path for f in os.scandir(indir) if f.is_dir() ]
    all_studies = fast_scandir(indir)

    # all_studies = ['instrument/NCDS_Age_33_Cohort_Member_Interview']
    appended_df = []
    for study in all_studies:
        if len(os.listdir(study)) == 5:
            print(study)
            df = one_study(study, df_qg)
            appended_df.append(df)
    appended_data = pd.concat(appended_df)
    appended_data.to_csv(os.path.join(outdir, 'RCNIC.csv'), sep='\t', index=False)


if __name__ == '__main__':
    main()

