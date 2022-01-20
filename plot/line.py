#!/usr/bin/env python3

'''
    class of line to placing points,
        used to sample in 2d image
'''

import numpy as np

from .bases import BaseCurve

class BaseLine(BaseCurve):
    '''
        class for line
            along which sampling is done
    '''
    def __init__(self, bpoint, direction, lrange=None):
        '''
            init a line
        '''
        bpoint=np.array(bpoint)
        direction=np.array(direction)
        assert bpoint.ndim==1 and direction.ndim==1, \
               len(bpoint)==len(direction)

        super().__init__(bpoint, direction, lrange=lrange)

    def get_points_along(self, lengths):
        '''
            compute coordinates for given `lengths`
        '''
        lengths=np.asarray(lengths)
        assert lengths.ndim==1

        lengths=lengths.reshape(1, -1)
        bpoint=self._bpoint.reshape(-1, 1)
        direction=self._direction.reshape(-1, 1)

        return bpoint+lengths*direction

class Line2D(BaseLine):
    '''
        class of line in 2d image
    '''
    def __init__(self, x0, y0, angle, deg=True, scale=1, lrange=None):
        '''
            init 2d line

            Parameters:
                x0, y0: float
                    coordinates of center

                angle: float
                    angle from x-axis

                deg: bool
                    whether `angle` is given in unit of degree

                    if False, in radian

                scale: float
                    scale of lengths in curve
        '''
        if deg:
            angle=np.deg2rad(angle)

        vx, vy=scale*np.sin(angle), scale*np.cos(angle)

        super().__init__((y0, x0), (vx, vy), lrange=lrange)

    # length range in rect
    def get_length_range_in_rect(self, x0, x1, y0, y1):
        '''
            compute range of length for this line within given rect

            current line:
                center (xc, yc),
                direction vector (vx, vy)
            Its parameter function
                x=xc+l*vx
                y=yc+l*vy
        '''
        yc, xc=self._bpoint       # center
        vy, vx=self._direction    # direction vector

        # section within plane y=y0, y=y1
        lys=self._range_intersect(yc, vy, y0, y1)
        if lys is None:
            raise ValueError('line not insect with the rect')
        ly0, ly1=lys

        # section within plane y=y0, y=y1
        lxs=self._range_intersect(xc, vx, x0, x1)
        if lxs is None:
            raise ValueError('line not insect with the rect')
        lx0, lx1=lxs

        l0=max(lx0, ly0)
        l1=min(lx1, ly1)
        if l0>l1:
            raise ValueError('line not insect with the rect')

        return l0, l1

    # auxiliary functions
    @staticmethod
    def _range_intersect(xc, vx, x0, x1):
        '''
            get range of s satisified
                xc+s*vc in interval [x0, x1]

            if not intersect, return None
        '''
        if vx==0:
            # not intersect
            if not (xc-x0)*(x1-xc)>=0:
                return None

            return -np.inf, np.inf

        lx0=(x0-xc)/vx
        lx1=(x1-xc)/vx

        if lx1<lx0:
            lx0, lx1=lx1, lx0

        return lx0, lx1
