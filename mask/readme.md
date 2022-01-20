Module to create mask file

# 2 types
2 types of mask file, FITS image or ASCII coord list
    - FITS image: val > 0 for bad pixels
    - ASCII coord: bad pixel coord (x, y) per line, index starting from 1

# pyregion

need package [pyregion](https://github.com/astropy/pyregion)

install: `pip install pyregion`