#!/usr/bin/env python3

"""
Python 3
    Try to get all questions from an instrument
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

    # From an instrument get all questions, all response, print to file
    agency = "uk.cls.nextsteps"
    Id_instrument = 'a6f96245-5c00-4ad3-89e9-79afaefa0c28'
    df_instrument_set, instrument_info = C.instrument_info_set('uk.cls.nextsteps', Id_instrument)

    with open('instrument.txt', 'w') as f:
        print(instrument_info, file=f)

    df_question = df_instrument_set.loc[(df_instrument_set.ItemType == 'Question') , :]

    question_df_list = []
    codelist_df_list = []
    response_df_list = []
    for question_id in df_question['Identifier']:
        print(question_id)
        df_question, df_response = C.get_question_all(agency, question_id)
        # store DataFrame in list
        question_df_list.append(df_question)

        if df_question['response_type'][0] == 'CodeList':
            codelist_df_list.append(df_response)
        else:
            response_df_list.append(df_response)
    
    df_question_all = pd.concat(question_df_list)
    df_question_all.to_csv('question.csv', index=False, sep=';')

    df_codelist_all = pd.concat(codelist_df_list)
    df_codelist_all.to_csv('codelist.csv', index=False, sep=';')

    df_response_all = pd.concat(response_df_list)
    df_response_all.to_csv('response.csv', index=False, sep=';')


if __name__ == '__main__':
    main()

