#!/usr/bin/env python3

"""
Python 3
    Try to get all questions from uk.cls.nextsteps
"""
import colectica
from colectica import ColecticaObject
import api
import pprint
import pandas as pd

pp = pprint.PrettyPrinter(depth=4)

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

# Instrument
#agency = "uk.cls.nextsteps"

#Id_instrument = "a6f96245-5c00-4ad3-89e9-79afaefa0c28"
#df, info = C.item_info_set(agency, Id_instrument)

#print(df_instrument.head(2))
#pp.pprint(instrument_info)

# Question Item
# codelist
#Id_question = '0260e016-9610-4bea-9527-002107d642bf'
#question_info = C.get_question_info(agency, Id_question)
#pp.pprint(question_info)

#df_question, df_codelist = C.get_question_all(agency, Id_question)
#print(df_question.transpose())
#print(df_codelist.head(2))

# text response
#Id_question_text = '981c5dd5-6f88-4f44-b94f-135341f78938'
#df_question, df_text = C.get_question_all(agency, Id_question_text)
#print(df_text)

# numeric response
#Id_question_numeric = 'f4417dc3-46a4-432a-87db-7ad95d04e5f4'
#df_question, df_numeric = C.get_question_all(agency, Id_question_numeric)
#print(df_numeric)

#Id_sequence = '6b89e69c-cb04-4d07-a1a0-dea4a2d29284'
#df, info = C.item_info_set(agency, Id_sequence)

#print(df_sequence.head(2))
#pp.pprint(sequence_info)

#Id_statement = '79bb5136-ba5f-4422-951c-f03058520bac'
#r = C.get_statement_info(agency, Id_statement)
#pp.pprint(r)

#Id_questiongroup = 'a6f96245-5c00-4ad3-89e9-79afaefa0c28'
#temp = C.get_an_item('uk.closer', Id_questiongroup)

# question group
#Id_qg = '75465b39-e1c6-416c-ab42-345af36ef889'
#Agency_qg = 'uk.closer'
#pp.pprint(C.get_an_item(Agency_qg, Id_qg))

#Id_concept = '8e610654-dd7c-4516-9d43-1935fb38a3f9'
#pp.pprint(C.get_an_item(Agency_qg, Id_concept))

# all question group
#r  = C.general_search('5cc915a1-23c9-4487-9613-779c62f8c205', '')
#print(r['TotalResults'])
#pp.pprint(r['Results'][0])

#ID = 'f026f9ab-91c7-410c-a4a4-b389e3f72078'
#r = C.item_to_dict('uk.closer', ID)

# question group
#agency = 'uk.closer'
#Id = '9b6a88e1-2cd2-47a2-a71d-69c8a10949ad'
#df, info = C.item_info_set(agency, Id)

# concept
#df, info = C.item_info_set('uk.closer', '09263728-048e-48c5-b735-32d3d70f4533')

# question item
#df, info = C.item_info_set('uk.iser', 'ca2992f6-e049-478a-9e05-c1ff81aff9aa')

# datetime response
#df, info = C.item_info_set('uk.iser', '34ed32b0-7176-4c43-b114-d51f8d8bdee8')

# Mode of Data Collection for a study
#d = C.item_to_dict('uk.cls.bcs70', 'f3a09755-23db-45df-bab3-387f1fa66790')
#print(d['CollectionEvent']['ModeOfCollection'])

# Series
#d = C.item_to_dict('uk.cls.bcs70', '75fe4705-0c94-4f75-b1e6-ad9c61ffde26')
#print(d)

d = C.item_to_dict('uk.cls.bcs70', 'e9e9853d-639c-4c9b-bab1-94b22b84f506')
print(d)
