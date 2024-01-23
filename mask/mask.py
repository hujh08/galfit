#!/usr/bin/env python3

'''
    module to handle mask
'''

from astropy.io import fits

import pyregion

# ds9 region file
class RegMask:
    '''
        class to create mask from region file(s)
    '''
    def __init__(self, fname=None):
        '''
            init with optional ds9 reg file
        '''
        self._shapes=pyregion.ShapeList([])

        if fname is not None:
            self.add_reg(fname)

    # add reg file
    def add_reg(self, fname):
        '''
            add ds9 reg file
        '''
        reg=pyregion.open(fname)
        self._shapes.extend(reg)

    # add shape individually
    def add_shape(self, name, params, coord_format='image'):
        '''
            add shape

            Parameters:
                name: name of shape
                params: params of shape

                see `pyregion.Shape` for detail
        '''
        shape=pyregion.Shape(name, params)
        shape.coord_format=coord_format

        self._shapes.append(shape)

    ## frequently used shape
    def add_circile(self, x0, y0, r):
        '''
            add circle
        '''
        params=[pyregion.region_numbers.SimpleNumber(i)
                    for i in (x0, y0, r)]

        self.add_shape('circle', params)

    # add FITS file
    def set_hdu(self, fname, ext=0):
        self._hdu=fits.open(fname)[ext]

    # get mask
    def get_mask(self, hdu=None, header=None, shape=None):
        '''
            return bool array with masked pixel True

            if header given
                shape is also needed
        '''
        if all([k is None for k in [hdu, header, shape]]):
            hdu=self._hdu

        return self._shapes\
                   .get_mask(hdu=hdu, header=header, shape=shape)

    def get_mask_by_header(self, header, shape=None):
        '''
            create mask array by header
        '''
        if shape is None:
            shape=(header['NAXIS2'], header['NAXIS1'])

        return self.get_mask(header=header, shape=shape)

    def get_mask_by_wcs(self, wcs, shape=None):
        '''
            create mask array by WCS object and shape
        '''
        if not wcs.is_celestial:
            raise ValueError('not celestial wcs')

        header=wcs.to_header()

        # add NAXISi
        if shape is None:
            nxy=wcs.pixel_shape
            if nxy is None:
                raise ValueError('no shape given')
            shape=tuple(nxy[::-1])

        ny, nx=shape
        header['NAXIS']=2
        header['NAXIS1']=nx
        header['NAXIS2']=ny

        return self.get_mask(header=header, shape=shape)

    ## save to fits
    def write_gf_mask(self, path, overwrite=True, **kwargs):
        '''
            write mask used in galfit
        '''
        mask=self.get_mask(**kwargs).astype(int)

        fits.writeto(path, mask, overwrite=overwrite)
