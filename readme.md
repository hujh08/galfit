Toolkit to facilitate running galfit

# Introduction
The most frequently way to run galfit is to feed it a formatted input file. This package is developed to cope with this file, mainly creating new file and modifying an existed one.

# Constraint file
In galfit input file, parameter `G` is a file which gives the constraint of fitting parameters, like fixing centers of two components to be same.

There are different ways to handle constraint file. In previous version, such a file is loaded and parsed semantically. The constraint information is followed when modifying the components.

But this is complex, and is not so frequently used for photometrical fitting. At present, a much simpler way is adopted, where treatment of contraint file is indenpendent on the galfit input file. The constraint file is just a string, like input image, mask file and so on. It is not concerned what is in the file.

In current version, a compromising way is used. Constraint file is loaded and parsed, semantically and optically, but independent with parsing of galfit input file. Semantical parsing is helpful to create and modify constraint file.

# Install
configure: `./configure  --libdir path/to/libdir`, where `libdir` path is folder to contain the package

Then `make install`

# Examples

## start from rough measurement

Rough measurements of galaxy, including center `x0, y0`, magnitude `mag`, effective radius `r_e`, axis ratio `ba` and position angle `pa`, could be obtained by hand or through some automatic routines, like `sextractor`. This could used as initial guess to start `GALFIT`

- create galfit.00

```python
from galfit.galfit import GalFit

# create galfit file
gf=GalFit()

## header
gf.input='init.fits'   # observed FITS file
gf.output='img.fits'
gf.sigma='sigma.fits'        # sigma fits
gf.mask='mask.fits'          # mask file
gf.psf='psf.fits'            # psf file
gf.region=[rx0, rx1, ry0, ry1]   # fit region
gf.conv=[sx, sy]             # convolution size

## single Sersic model
gf.add_sersic([x0, y0, mag, re, 2, ba, pa])  # use n=2 as default Sersic index

gf.add_sky([sky, 0, 0])   # add flat sky

## freeze mode pars
gf.freeze()
gf[0].free(['mag'])       # free mag, in 0th component to fit at first
                          # 'x0, y0, mag, re, n, ba, pa' for pars in Sersic model
                          # or just '1, 2, 3, 4, 5, 9, 10', the digit in GALFIT file

# save file
fname=os.path.join(dir_work, 'galfit.00')
gf.writeto(fname)
```

- run GALFIT

```python
from galfit.tools import rungf

# first run, return number of result file, 'galfit.NN'
fno=rungf(0)

# free Sersic component, then run again
fno=rungf(fno, change=lambda g: [g[0].free()])
```

