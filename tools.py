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

# wrap GalFit
def readgf(*args, **kwargs):
    # wrap GalFit to avoid circular dependency
    from .galfit import GalFit
    return GalFit(*args, **kwargs)

# read galfit via file number
def readgf_no(num):
    return readgf(gfname_from_int(num))

# run galfit successively
def rungf(init, change=None, verbose=True):
    '''
    Parameters
    ----------
    init: integer
        the number of initial number

    change: callable or None
        change the given initial template
            and run galfit in new one
        if callable, it only accepts one GalFit-type argument

    verbose: bool
        verbose when running galfit

    Returns
    -------
    number of galfit result file
    '''
    fno=init
    fname=gfname_from_int(fno)

    if change!=None:
        gf=readgf(fname)
        change(gf)

        fno+=1
        fname=gfname_from_int(fno)
        while os.path.isfile(fname):
            fno+=1
            fname=gfname_from_int(fno)
        gf.writeto(fname)

    fno_r=fno+1
    fname_r=gfname_from_int(fno_r)
    if os.path.exists(fname_r):
        os.remove(fname_r)

    if not os.path.isfile(fname):
        raise Exception('Error: init gf file not exists, [%s]' % fname)

    cmd='galfit '+fname
    if not verbose:
        cmd+=' >/dev/null'

    ecode=os.system(cmd)
    if ecode!=0 or not os.path.exists(fname_r):
        raise Exception('galfit failed for %s, exit code: %i'
                            % (fname, ecode))

    return fno_r