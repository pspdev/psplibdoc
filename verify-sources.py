#!/usr/bin/python3

import glob
import psp_libdoc

fail = False
for csv in glob.glob('PSPLibDoc/kd/*.csv') + glob.glob('PSPLibDoc/vsh/module/*.csv'):
    for line in open(csv, 'r').read().split('\n')[:-1]:
        lib = line.split(',')[0]
        nid = line.split(',')[2]
        name = line.split(',')[3]
        source = line.split(',')[4]
        if nid == psp_libdoc.compute_nid(name):
            if source != 'matching':
                print('not marked as matching:', csv, line)
                fail = True
        else:
            if source == 'matching':
                print('wrongly marked as matching:', csv, line)
                fail = True
        if source == '' and name != lib + '_' + nid:
            print('modified without comment:', csv, line)
        if source != 'matching' and source != '':
            print('info:', csv, line)
        # all the rest is considered guesses so is ok

if fail:
    exit(1)

