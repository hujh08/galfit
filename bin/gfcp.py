#!/usr/bin/env python3

'''
    copy image within fit region

    name from IRAF task `imcopy`
'''

import os
import argparse

from astropy.io import fits

from galfit.galfit import GalFit
import galfit.fits as gfits
from galfit.tools import gfname_from_int

# arguments
parser=argparse.ArgumentParser()
parser.add_argument('gfile', help='galfit file')
parser.add_argument('output', help='output file',
                        nargs='?', default='cp.fits')
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

print()

# load gf file
print('load gf file')
gf=GalFit(gfile)

fimg=gf.get_path_of_file_par('input')
print('input image:', fimg)

if not os.path.isfile(fimg):
    print('Error: image file not exists:', fimg)
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

# write to file
print('save to:', fout)
fits.writeto(fout, img[(y0-1):y1, (x0-1):x1], overwrite=overwrite, header=hdr)
