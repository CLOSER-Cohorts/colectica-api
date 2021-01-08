#!/usr/bin/env python3

"""
Python 3
    Try to get all question groups
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd


def main():

    hostname = "discovery-pp.closer.ac.uk"
    username = None
    password = None
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)

    # get all question groups
    L = C.general_search("5cc915a1-23c9-4487-9613-779c62f8c205", '', 10) 

    appended_df = []
    for i in range(L['ReturnedResults']): 
        agency = L['Results'][i]['AgencyId']
        Id = L['Results'][i]['Identifier']
        df, info = C.item_info_set(agency, Id)

        if info['QuestionItemRef'] != []:
            df_qi = pd.DataFrame(info['QuestionItemRef'])
            df_qi['QI_Name'] = df_qi.apply(lambda row: C.get_question_info(row['Agency'], row['ID'])['QuestionItemName'], axis=1)
            df_qi['QG_URN'] = info['URN']
            df_qi['QG_Agency'] = info['AgencyId']
            df_qi['QG_Id'] = info['Identifier']
            df_qi['QG_Version'] = info['Version']
            df_qi['QG_Name'] = info['Name']
            df_qi['QG_Label'] = info['Label']
            appended_df.append(df_qi)

    appended_data = pd.concat(appended_df)
    appended_data.to_csv('QG_10.csv', sep=';', index=False)


if __name__ == '__main__':
    main()

