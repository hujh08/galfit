Toolkit to facilitate running galfit

# Introduction
The most frequently way to run galfit is to feed it a formatted input file. This package is developed to cope with this file, mainly creating new file and modifying an existed one.

# Constraint file
In galfit input file, parameter `G` is a file which gives the constraint of fitting parameters, like fixing centers of two components to be same.

There are different ways to handle constraint file. In previous version, such a file is loaded and parsed semantically. The constraint information is followed when modifying the components.

But this is complex, and is not so frequently used for photometrical fitting. At present, a much simpler way is adopted, where treatment of contraint file is indenpendent on the galfit input file. The constraint file is just a string, like input image, mask file and so on. It is not concerned what is in the file.

In current version, a compromising way is used. Constraint file is loaded and parsed, semantically and optically, but independent with parsing of galfit input file. Semantical parsing is helpful to create and modify constraint file.

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

# Install
configure: `./configure  --libdir path/to/libdir`, where `libdir` path is folder to contain the package

Then `make install`
