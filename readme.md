Toolkit to facilitate running galfit

# Introduction
The most frequently way to run galfit is to feed it a formatted input file. This package is developed to cope with this file, mainly creating new file and modifying an existed one.

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

# Constraint file
In galfit input file, parameter `G` is a file which gives the constraint of fitting parameters, like fixing centers of two components to be same.

There are different ways to handle constraint file. In previous version, such a file is loaded and parsed semantically. The constraint information is followed when modifying the components.

But this is complex, and is not so frequently used for photometrical fitting. At present, a much simpler way is adopted, where treatment of contraint file is indenpendent on the galfit input file. The constraint file is just a string, like input image, mask file and so on. It is not concerned what is in the file.

In current version, a compromising way is used. Constraint file is loaded and parsed, semantically and optically, but independent with parsing of galfit input file. Semantical parsing is helpful to create and modify constraint file.

## examples

- bulge/disk decomposition

```python
fname=os.path.join(dir_work, 'galfit.NN')  # start from previous result, single-Sersic
gf=GalFit(fname)

# gf.add_sersic([x0d, y0d, magd, red, 1, bad, pad], index=1)  # add disk after Sersic
# gf[1].freeze(['n'])

# add disk based on previous
gf.dup_comp(0)  # duplicate 0th comp
gf[1].n=1       # n=1 for exponential disk
gf[1].freeze(['n'])
```

- create constraint file

```python
from galfit.constraint import Constraints

constrs=Constraints()

# add rules
constrs.add_hard_cons_to_xy(1, 2)  # keep offset between centers
                                   #     concentric if same initial values given
                                   # comp index starting from 1 here, not 0

constrs.add_range_to_par(1, 'n', [0.5, 10])  # 0.5 <= n <= 10
constrs.add_offset_range_to_pair(1, 2, 'mag', [-5, 5])  # -5 <= mag1-mag2 <= 5
                                                        #     not allow too faint comp

constrs.add_ratio_range_to_pairs(1, 2, 're', [0.1, 10]) # 0.1 <= re1/re2 <= 10
                                                        #     not allow too small comp


# save constraint file
fconstrs=os.path.join(dir_work, 'constraints')
constrs.writeto(fconstrs)
```

- add contraint file to galfit file

```python
gf.set_constraints(fconstrs)

# then save and run as previous
gf.writeto(fgf)
rungf(fgf)
```