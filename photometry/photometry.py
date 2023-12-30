#!/usr/bin/env python3

'''
    functions for photometry via GalFit
'''

import numpy as np

__all__=['mag_to_ftot',
         'mag_to_mu', 'mu_to_mag']

def mag_to_ftot(mag, texp=1, zpt=20):
    '''
        use 'exponential disk model' as example
            I(r) = I0 exp(-r/rs)

        Then
            Ftot = 2*pi*rs^2*q * I0, q: axis ratio of galaxy
            mag = -2.5 log10 (Ftot/texp) + mag zpt

        In GalFit, use parameters `mag`, instead of I0, intensity at center

        In image fit task, an observed image I[i, j] is given
            and goal is find model image M[i, j] to approximate I[i, j]
        `Ftot` would be Sumij M[i,j] if its region is large enough
            So the unit of returned value is same as that of input image pixel

        ===============
        
        Parameters:
            mag: float
                magnitude from galfit file

            texp: float, default: 1
                exposure time in sec

            zpt: float, default: 20
                zero point
    '''
    return 10**(-(mag-zpt)/2.5)*texp

# magnitude and surface brightness
def mu_to_mag(mu, rs, hs, psec2=1):
    '''
        parameters is used in models, like 'edge-on disk'
            F(r, h) = F0 * (r/rs)*K1(r/rs) * sech^2(h/hs)
        then
            mu = -2.5 log10(F0/(texp*dx*dy)) + mag zpt,
                dx, dy: platescale in arcsec (item K in GALFIT input file)

        Both 'exponential' and 'edge-on' disk could correspond to a 3D model
            L(r, h) = L0 * exp(-r/rs) * sech^2(h/hs)
        Then its face-on and edge-on surface brightness are
            - face-on: I(r) = I0 * exp(-r/rs)
                with I0=2*hs*L0
            - face-on: F(r, h) = F0 * (r/rs)*K1(r/rs) * sech^2(h/hs)
                with F0=2*rs*L0
        And total luminosity is
            Ltot = 4*pi*rs^2*hs * L0
                 = 2*pi*rs^2 * I0 (q=1 for totally face-on)
                 = Ftot
        See van der Kruit & Searle, 1981 for detail

        From above,
            mag - mu = -2.5 log10 (Ftot/(F0/dxy)), dxy=dx*dy, pixel area
            Ftot/F0  = 2*pi*rs*hs
        So
            mag - mu = -2.5 log10 (2*pi*rs*hs*dxy)

        ===============

        Parameters:
            mu, rs, hs: float
                input surface brightness, scale radius and scale height

            psec2: float, default 1
                pixel area in unit of 'arcsec^2'

                default 1 is always used
                    same as zeropoint,
                        not actually used in model building
    '''
    d=corr_mu_from_mag(rs, hs, psec2=psec2)
    return mu-d

def mag_to_mu(mag, rs, hs, psec2=1):
    '''
        reverse of `mu_to_mag`
    '''
    d=corr_mu_from_mag(rs, hs, psec2=psec2)
    return mag+d

## correct of mu from rs, hs, mu
def corr_mu_from_mag(rs, hs, psec2=1):
    d_rhs=2.5*np.log10(2*np.pi*rs*hs)
    d_psec2=corr_mu_by_psec2(psec2)
    return d_rhs+d_psec2

def corr_mu_by_psec2(psec2, psec2_old=1):
    '''
        correct to mu by change of `psec2`
    '''
    return 2.5*np.log10(psec2/psec2_old)
