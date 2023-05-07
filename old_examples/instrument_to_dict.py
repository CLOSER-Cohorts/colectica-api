#!/usr/bin/env python3

"""
Python 3
    Try to get all raw items from an instrument
"""
import colectica
from colectica import ColecticaObject
import api
import pandas as pd
import os
import numpy as np
import json
from pandas.io.json import json_normalize


def main():
    outdir = 'instrument_dict_original'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

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

    L = json.load(open('../../colectica_api_get_questions/instrument/all_instrument.txt'))
#    print(L)

    all_idx = np.array(range(L['TotalResults']))
    # split into 10 chunks
    chunks = np.array_split(all_idx, 0)

    this_chunk = 10
    print(chunks[this_chunk])

    for i in chunks[this_chunk]:
        print(i)
        Agency = L['Results'][i]['AgencyId']
        ID = L['Results'][i]['Identifier']
        Version = L['Results'][i]['Version']

        df_instrument_set, instrument_info = C.item_info_set(Agency, ID)

        instrument_name = instrument_info['InstrumentSourceID']
        instrument_dir = os.path.join(outdir, instrument_name)
        if not os.path.exists(instrument_dir):
            os.makedirs(instrument_dir)

        item_types = df_instrument_set.ItemType.unique()
        for item_type in item_types:

            df_part = df_instrument_set.loc[(df_instrument_set.ItemType == item_type) , :]

            dict_list = []
            for part_id in df_part['Identifier']:
                part_dict = C.get_an_item(Agency, part_id)

                if part_dict is not None:
                    dict_list.append(part_dict)

            with open(os.path.join(instrument_dir, item_type + '.txt'), 'w') as outfile:
                json.dump(dict_list, outfile, indent=4)


if __name__ == '__main__':
    main()

