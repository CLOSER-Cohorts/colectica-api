#!/usr/bin/env python3

"""
Python 3
    This is for Dara's project: to add links to Discovery variables from the CLOSER website
    - get all variables
    - convert list of dictionary to dataframe
    - keep only variable name and http link (agency and Id)
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd
import os


def main():
    outdir = 'variable_2021_08_03'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    hostname = "discovery-pp.closer.ac.uk"
    username = ""
    password = ""
    if not hostname:
        hostname = input ("enter the url of the site: ")
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)

    # get list of variables
    L_variable = C.general_search('683889c6-f74b-4d5e-92ed-908c0a42bb2d', '', 0)

    # convert to data frame
    df_variable = pd.DataFrame(L_variable['Results'])
    
    df = df_variable.loc[:, ['ItemName', 'Label', 'AgencyId', 'Identifier']]
    df['url'] = 'https://discovery.closer.ac.uk/item/' + df['AgencyId'] + '/' + df['Identifier'] 
    
    # normalize the column of dictionaries and join it to df
    df = df.join(pd.json_normalize(df.ItemName)) 
    # drop 
    df.drop(columns=['ItemName'], inplace=True)
    # rename
    df.rename(columns={'en-GB': 'ItemName'}, inplace=True)

    # also need the value from Label
    df = df.join(pd.json_normalize(df.Label)) 
    df.drop(columns=['Label'], inplace=True)
    df.rename(columns={'en-GB': 'Label'}, inplace=True)
    
    df.to_csv(os.path.join(outdir, 'variable_name_url.csv'), index=False, sep='\t')


if __name__ == '__main__':
    main()

