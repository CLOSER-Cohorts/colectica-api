#!/usr/bin/env python3

"""
Python 3
    Try to get all dataset 
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd
import json
import os


def main():
    outdir = 'data_file'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    hostname = "discovery-pp.closer.ac.uk"
    username = None
    password = None
    if not hostname:
        hostname = input("enter your hostname: ")
    if not username:
        username = input("enter your username: ")
    if not password:
        password = input("enter your password: ")

    C = ColecticaObject(hostname, username, password)

    # get all data file
    L = C.item_search("a51e85bb-6259-4488-8df2-f08cb43485f8", '', 0)
    print(L['TotalResults']) # 490
    
    appended_df = []
    for item in L['Results']:

        agency = item['AgencyId']
        Id = item['Identifier']

        info = C.item_to_dict(agency, Id)

        new_data = {'URN': info['URN'],
                    'Agency': info['AgencyId'],
                    'Id': info['Identifier'],
                    'Version': info['Version'],
                    'Title': info['Citation']['Title'],
                    'AlternateTitle': info['Citation']['AlternateTitle']
                    }
        df_data = pd.DataFrame(new_data, index=[0])

        appended_df.append(df_data)

    appended_data = pd.concat(appended_df)
    appended_data.to_csv(os.path.join(outdir, 'data_file_all.csv'), sep='\t', index=False)


if __name__ == '__main__':
    main()

