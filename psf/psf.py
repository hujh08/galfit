#!/usr/bin/env python3

'''
    module to make psf image used by GalFit
'''

import numbers

import numpy as np
from astropy.io import fits

def mk_gauss_psf(p, ptype='fwhm', semiw=None,
                    output=None, overwrite=True, header=True):
    '''
        create Gaussian PSF used in GalFit

        Parameters:
            p: float
                parameter for Gaussian profile
                    sigma or fwhm

            ptype: 'sigma' or 'fwhm'

            semiw: None, int, or 2-tuple
                semiwidth of result array

                if None, use 15 times FWHM
                    suggested by `galfit` doc
                        diameter > 30 x FWHM

            output: None or file name
                output file name

                if None, return array

            header: bool
                whether to write header
    '''
    # param
    assert ptype in ['sigma', 'fwhm']
    # SIGMA_FWHM=1/(np.sqrt(2*np.log(2))*2)
    SIGMA_FWHM=0.42466090014400953  # sigma/fwhm
    if ptype=='fwhm':
        fwhm=p
        sigma=SIGMA_FWHM*fwhm
    else:
        sigma=p
        fwhm=sigma/SIGMA_FWHM

    # shape
    if semiw is None:
        semiw=[int(np.ceil(15*fwhm))]*2
    elif isinstance(semiw, numbers.Number):
        semiw=[semiw, semiw]
    else:
        assert len(semiw)==2

    ysemi, xsemi=semiw
    ny, nx=2*ysemi+1, 2*xsemi+1

    # gausian profile
    xs=np.arange(nx)
    ys=np.arange(ny)

    ys, xs=np.meshgrid(ys, xs, indexing='ij')

    rsqs=(xs-xsemi)**2+(ys-ysemi)**2
    vals=np.exp(-rsqs/(2*sigma**2))/(2*np.pi*sigma**2)

    ## normalize
    vals=vals/np.sum(vals)

    if output is None:
        return vals

    # write to file
    kwargs=dict(overwrite=overwrite)

    ## header
    if header:
        hdr=fits.header.Header()

        hdr['model']='gauss'
        hdr['fwhm']=(fwhm, 'in pixel unit')
        hdr['sigma']=sigma

        kwargs['header']=hdr

    fits.writeto(output, vals, **kwargs)

# general to mk psf
## map of all psf mods
all_psf_mod=dict(
    gauss=mk_gauss_psf,)

def mk_psf(*args, model='gauss', **kwargs):
    '''
        general method to make psf
    '''
    if model not in all_psf_mod:
        raise KeyError('unexpected psf model %s, '
                       'only support %s at current'
                            % (repr(model),
                               repr(list(all_psf_mod.keys()))))
    func=all_psf_mod[model]

    return func(*args, **kwargs)