#!/usr/bin/env python3

'''
    io of image file
'''

import numpy as np
from astropy.io import fits

def load_mask_txt(fname, shape=None):
    '''
        load text mask file

        if shape is None, return list of xy coordinates
        otherwise mask array with bad pixel > 0
    '''
    coords=[]
    with open(fname) as f:
        for line in f:
            x, y=[int(i) for i in line.split()]
            coords.append((x, y))

    if shape is None:
        return coords

    # to mask array
    ny, nx=shape
    return coords_to_mask_array(coords, nx, ny)

def load_mask_fits(fname):
    return fits.getdata(fname)

def load_mask(fname, **kwargs):
    '''
        load mask file

        determine fits or txt based on suffix of `fname`
    '''
    if fname.endswith('.fits'):
        return load_mask_fits(fname)
    else:
        return load_mask_txt(fname, **kwargs)

def coords_to_mask_array(coords, nx, ny):
    '''
        convert coords to mask array
    '''
    mask=np.zeros((ny, nx), dtype=int)

    coords=np.asarray(coords)
    if np.size(coords):
        xs, ys=coords.T-1  # -1 to array index, starting from 0, not 1
        mask[ys, xs]=1

    return mask


