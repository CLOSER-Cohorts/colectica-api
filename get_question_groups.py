#!/usr/bin/env python3

"""
Python 3
    Try to get all question groups
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd
import json
import os

def get_qi(C, row):
    d = C.item_to_dict(row['Agency'], row['ID'])
    QuestionURN = d['QuestionURN']
    QuestionItemName = d['QuestionItemName']
    return [QuestionURN, QuestionItemName]


def main():
    outdir = 'question_group'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    hostname = None
    username = None
    password = None
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)

    # get all question groups
#    L = C.general_search("5cc915a1-23c9-4487-9613-779c62f8c205", '', 0)
#    print(L['TotalResults']) # 35952

#    json.dump(L, open(os.path.join(outdir, 'all.txt'),'w'))

    L = json.load(open(os.path.join(outdir, 'all.txt')))
#    print(L)

    import numpy as np
    all_idx = np.array(range(L['TotalResults']))
    chunks = np.array_split(all_idx, 10)

    this_chunk = 6

    appended_df = []
#    for i in range(L['ReturnedResults']):

    for i in chunks[this_chunk]:
        agency = L['Results'][i]['AgencyId']
        Id = L['Results'][i]['Identifier']
        df, info = C.item_info_set(agency, Id)

        if info['QuestionItemRef'] != []:
            print(i)
            df_qi = pd.DataFrame(info['QuestionItemRef'])
            # df_qi['QI_Name'] = df_qi.apply(lambda row: C.get_question_info(row['Agency'], row['ID'])['QuestionItemName'], axis=1)
            df_qi[['QI_URN', 'QI_Name']] = df_qi.apply(lambda row: pd.Series(get_qi(C, row)), axis=1)
            df_qi['QG_URN'] = info['URN']
            df_qi['QG_Agency'] = info['AgencyId']
            df_qi['QG_Id'] = info['Identifier']
            df_qi['QG_Version'] = info['Version']
            df_qi['QG_Name'] = info['Name']
            df_qi['QG_Label'] = info['Label']
            appended_df.append(df_qi)

    appended_data = pd.concat(appended_df)
    appended_data.to_csv(os.path.join(outdir, 'QG_{}.csv'.format(this_chunk)), sep='\t', index=False)


if __name__ == '__main__':
    main()

