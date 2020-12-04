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


hostname = "discovery-pp.closer.ac.uk"
username = None
password = None
if not username:
    username = input("enter your username: ")
if not password:
    password = input("enter your password: ")

C = ColecticaObject(hostname, username, password)

# Instrument 
agency = "uk.cls.nextsteps"
Id_instrument = "a6f96245-5c00-4ad3-89e9-79afaefa0c28"
df_instrument, instrument_info = C.instrument_info_set(agency, Id_instrument)
print(df_instrument.head(2))
pp.pprint(instrument_info) 

# Question Item
# codelist
Id_question = '0260e016-9610-4bea-9527-002107d642bf'
question_info = C.get_question_info(agency, Id_question)
pp.pprint(question_info) 
    
df_question, df_codelist = C.get_question_all(agency, Id_question)
print(df_question.transpose())
print(df_codelist.head(2))

# text response
Id_question_text = '981c5dd5-6f88-4f44-b94f-135341f78938'
df_question, df_text = C.get_question_all(agency, Id_question_text) 
print(df_text)

# numeric response
Id_question_numeric = 'f4417dc3-46a4-432a-87db-7ad95d04e5f4'
df_question, df_numeric = C.get_question_all(agency, Id_question_numeric) 
print(df_numeric)

