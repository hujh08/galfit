#!/usr/bin/env python3

'''
    io for FITS file

    support extended FITS file name
    for example,
        example.fits[3]               # locate 3rd HDU (0 for Primary)
        example.fits[1:256:2,1:512]   # image section
        example.fits[2][1:256,1:256]  # section in 2nd HDU

        !example.fits                 # overwrite example.fits if it exists
'''

import os

import numpy as np
from astropy.io import fits

from .fitsname import parse_ext_fitsname
from .core import locate_hdu, image_section

__all__=['gethdu', 'getdata', 'getheader',
         'writeto', 'imcopy']

# hdu
def gethdu(fitsname, skip_none=True):
    '''
        get HDU for given extended file name

        skip empty HDU by default,
            like `astropy.io.fits.getdata`
    '''
    fname, ext, sect=parse_ext_fitsname(fitsname)

    # hdulist
    hdulist=fits.open(fname)

    # locate HDU
    hdu=locate_hdu(hdulist, ext, skip_none=skip_none)

    # image section
    if sect is not None:
        hdu=image_section(hdu, sect)

    return hdu

## get data or header individually
def getdata(fitsname, **kwargs):
    '''
        get data for extended FITS name

        skip empty HDU by default,
            like `astropy.io.fits.getdata`
    '''
    return gethdu(fitsname, **kwargs).data

def getheader(fitsname, **kwargs):
    '''
        get header for extended FITS name
    '''
    return gethdu(fitsname, **kwargs).header

# write fits: support overwrite syntax, !example.fits
def writeto(fname, data, extfname=True, **kwargs):
    '''
        write data to fits
        support overwrite syntax, !example.fits

        :param extfname: bool
            if False, close overwrite syntax

        :param data: ndarary or HDU
    '''
    # overwrite syntax, !example.fits
    if extfname:
        dname, bname=os.path.split(fname)
        if bname[0]=='!':
            if 'overwrite' in kwargs:
                raise ValueError('repeated set for arg `overwrite` '
                             'in `fname` and kwargs')

            fname=os.path.join(dname, bname[1:])
            kwargs['overwrite']=True

    # write
    if isinstance(data, np.ndarray):
        fits.writeto(fname, data, **kwargs)
    else:   # write hdu
        if not isinstance(data, fits.hdu.base.ExtensionHDU):
            raise TypeError('only support ndarray or ExtensionHDU')

        hdu=data
        hdu.writeto(fname, **kwargs)

## frequently used
def imcopy(fitsname, output, extfname=True):
    '''
        copy a HDU in FITS file to new file,
            not all HDUs
        work like `IRAF.imcopy`

        support extended file name and image section

        Parameters:
            output: fitsname of output
                support '!' in begining of file name to overwrite

            extfname: bool
                whether to support extended file name

                if False, copy 1st HDU
    '''
    if not extfname:
        hdu=fits.open(fitsname)[0]
    else:
        hdu=gethdu(fitsname)

    if output is None:
        return hdu

    writeto(output, hdu, extfname=extfname)
