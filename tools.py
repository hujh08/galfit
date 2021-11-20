#!/usr/bin/env python3

'''
    some convenient tools to run galfit
'''

import os

# get gf filename from int
def gfname_from_int(num, dirname=None):
    '''
        get gf filename from int

        Parameters:
            num: int
                return galfit.NN

            dirname: str, or Path object, optional
                dirname to store galfit file
    '''
    fname='galfit.%02i' % num
    if dirname!=None:
        fname=os.path.join(dirname, fname)
    return fname
