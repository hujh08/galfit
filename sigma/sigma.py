#!/usr/bin/env python3

'''
    module to make sigma image
'''

import numpy as np
from astropy.io import fits

import galfit.fits as gfits

def mk_sigma(data, gain=1, skymean=0, skyrms=0,
                output=None, overwrite=True, header=True):
    '''
        mk sigma image
            sigma = sqrt((data-skymean)/gain+skyrms^2)

        Parameters:
            data: file name or ndarray
                if file name, support extended file name

            gain, skymean, skyrms: float
                parameter to make sigma

                default value just leads to
                    simga=sqrt(data)

            output: None or file name
                output file name

                if None, return array

            header: bool
                whether to write header
    '''
    if isinstance(data, str):
        data=gfits.getdata(data)

    sigma=np.sqrt((data-skymean)/gain+skyrms**2)

    if output is None:
        return sigma

    # write to file
    kwargs=dict(overwrite=overwrite)

    ## header
    if header:
        hdr=fits.header.Header()

        hdr['gain']=gain
        hdr['skymean']=skymean
        hdr['skyrms']=skyrms

        kwargs['header']=hdr

    fits.writeto(output, sigma, **kwargs)