#!/usr/bin/env python3

"""
Following datasets and questionnaires, grab the variables, or questions and the code lists and categories, check IsDeprecated field.
"""

import colectica
from colectica import ColecticaObject
import api
from pathlib import Path
import pandas as pd
import json
import os

def IsDeprecated_data(URN_list, out_dir):
    """
    From a given list of data URNs, for each URN, find all related set, check individual element is deprecated or not.
    Output one file for one URN.
    """
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

    # data list
    for n, URN in enumerate(URN_list):
        [Agency, ID, Version] = URN.split(':')

        # Gets the set of all items under the specified root.
        set_list = C.get_a_set(Agency, ID, Version)

        out_list = []
        # df_list = []
        for i, item in enumerate(set_list):
            set_dict = C.item_to_dict(item['Item3'], item['Item1'], str(item['Item2']))

            element = dict((k, set_dict[k]) for k in ('ItemType', 'AgencyId', 'Identifier', 'Version', 'IsDeprecated')) 
            element['set_order'] = i + 1
            element['top_URN'] = URN
            element['num'] = n
            out_list.append(element)

        df = pd.DataFrame(out_list)
        df.to_csv(os.path.join(out_dir, URN + '.tsv'), sep = '\t', index=False)


def gather_summary(input_dir, summary_dir):
    """
    Concatenate all files from input_dir
    """

    dir = Path(input_dir)
    df = (pd.read_csv(f, sep='\t') for f in dir.glob("*.tsv"))
    df_all = pd.concat(df)
    df_all.to_csv(os.path.join(summary_dir, dir.name + '_all.tsv'), sep = '\t', index=False)

    df_summary = df_all.groupby(['top_URN', 'IsDeprecated']).size().reset_index(name='count')
    df_summary.to_csv(os.path.join(summary_dir, dir.name + '_summary.tsv'), sep = '\t', index=False)


def main():
    outdir = 'IsDeprecated'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    data_dir = os.path.join(outdir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    question_dir = os.path.join(outdir, 'question')
    if not os.path.exists(question_dir):
        os.makedirs(question_dir)

    # data URN list
    data_URN_list = [
                     'uk.cls.ncds:1f329e29-a732-4134-94aa-58ce3d36df51',
                     'uk.cls.ncds:d7f8f2b8-f691-40c9-88c8-0d6f3d9c2c5b:1'
                     ]

    IsDeprecated_data(data_URN_list, data_dir)
    gather_summary(data_dir, outdir)

    # question list
    question_URN_list = ['uk.alspac:b3944b6d-2148-4791-b8dd-73837ad37bbc:1']

    IsDeprecated_data(question_URN_list, question_dir)
    gather_summary(question_dir, outdir)


if __name__ == '__main__':
    main()
