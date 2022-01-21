Module to handle FITS file

# Introduction

`Astropy` seems not supporting extended FITS file name. This module provide a solution, as a supplement.

# Extended file name
Extend file name syntax is supported by many libraries, e.g. `IRAF`, `CFTISIO`. It is convenient to specify HDU or image section in one single string.

Examples:
```
    example.fits[3]               # locate 3rd HDU following primary (0 for Primary HDU)
    example.fits[EVENTS]          # extenstion with EXTNAME='EVENTS'
    example.fits[EVENTS, 2]       # same as above, but also with EXTVER=2
    example.fits[EVENTS, 2, b]    # same as above, but also with XTENSION='BINTABLE'
    example.fits[1:256:2,1:512]   # image section, image[0:512,0:256:2] in numpy ndarray index syntax
    example.fits[*,1:512]         # image[0:512,:]
    example.fits[*:2,1:512]       # image[0:512,::2]
    example.fits[-*,*]            # image[:,::-1], flip in x axis
    example.fits[2][1:256,1:256]  # section in 2nd HDU after primary
```

Besides these, there are other complex syntax. See document of [`CFITSIO`](https://heasarc.gsfc.nasa.gov/docs/software/fitsio/c/c_user/node83.html) for detail. In this package, simple syntax, as above examples, is implemented.

Syntax to locate a HDU is to attach, following file name, with square brackets enclosing
    
    - number (e.g. `[1]`)
    - name of HDU (value of EXTNAME or HDUNAME keyword, e.g. `[EVENTS]`), and optionally, separated by commas,
        - extension version number (value of EXTVER keyword, imset number)
        - extensin type (value of XTENSION keyword: IMAGE, ASCII or TABLE, or BINTABLE, data type for extension), or abbreviated to single letter (I, A or T, or B respectively)

Syntax to specify image section is similar as numpy ndarray, but with inversed axis order, that is x, y. There are two differences: asterisk, `*`, is used to mean entire axis (similar as `:` in numpy), and `-` in the begining would flip the axis (only support combining with `*`, that is `-*`). Such section string could be appended after a HDU one (e.g. `example.fits[2][1:256,1:256]`)

In the combining cases, HDU+section or extname+extver+xtension, field order is fixed. That means if both hdu and section are specified, hdu must be before sect. Same for the extname.