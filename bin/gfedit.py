#!/usr/bin/env python3

'''
    create image FITS with mask

    name from IRAF task `imedit`
'''

import os
import argparse

import numbers

import numpy as np
from astropy.io import fits

from galfit.galfit import GalFit
import galfit.fits as gfits
from galfit.mask import load_mask
from galfit.tools import gfname_from_int

# arguments
parser=argparse.ArgumentParser()
parser.add_argument('gfile', help='galfit file')
parser.add_argument('output', help='output masked file',
                        nargs='?', default='ed.fits')
parser.add_argument('-n', '--notoverwrite', action='store_false',
                    help='not overwrite exists output file',
                    default=True, dest='overwrite')
args=parser.parse_args()

gfile=args.gfile
if gfile.isdigit():
    gfile=gfname_from_int(int(gfile))
print('input gf file:', gfile)

if not os.path.isfile(gfile):
    print('Error: file not exists:', gfile)
    exit(-1)

fout=args.output  # output file
overwrite=args.overwrite
print('output file:', fout)
print('    overwrite:', overwrite)

if not overwrite and os.path.exists(fout):
    print('Error: output file already exists:', fout)
    print('not use -n/--nooverwrite to overwrite')
    exit(-1)

## other arguments
maskval=np.nan
maskval_int=0    # or 0 for int  

print()

# load gf file
print('load gf file')
gf=GalFit(gfile)

fimg=gf.get_path_of_file_par('input')
fmsk=gf.get_path_of_file_par('mask')
print('input image:', fimg)
print('mask:', fmsk)

if not os.path.isfile(fimg):
    print('Error: image file not exists:', fimg)
    exit(-1)

if fmsk!='none' and not os.path.isfile(fmsk):
    print('Error: mask file not exists:', fmsk)
    exit(-1)

x0, x1, y0, y1=gf.region
print('region:', x0, x1, y0, y1)

print()

# load image fits
print('load image fits')
imghdu=gfits.gethdu(fimg)
img=imghdu.data
hdr=imghdu.header

ny, nx=img.shape
print('image shape:', ny, nx)

hdr=gfits.crop_header(hdr, ((x0, x1), (y0, y1)))

print()

# load mask file
if fmsk!='none':
    print('load mask file')
    mask=load_mask(fmsk, shape=(ny, nx))

    mark=(mask>0)
    if issubclass(img.dtype.type, numbers.Integral):
        img[mark]=maskval_int
    else:
        img[mark]=maskval
else:
    print('no mask')

print()

# write to file
print('save to:', fout)
fits.writeto(fout, img[(y0-1):y1, (x0-1):x1], overwrite=overwrite, header=hdr)
