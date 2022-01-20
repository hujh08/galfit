#!/usr/bin/env python3

'''
    base classes for curve and sampling
'''

import numpy as np
from scipy.ndimage import map_coordinates

class BaseCurve:
    '''
        base class for 1d directed curve,
            along which sampling points is placed

        Sampling in image is done by interpolation
            in some points placed along the curve
    '''
    def __init__(self, bpoint, direction, lrange=None):
        '''
            init 1d directed curve
            
            neccessay attributions:
                - base point
                    coordinates in image
                - direction
                    unit vector for a direction

            optional:
                - range of lengths
                    use it when lrange not given for sampler
        '''
        self._bpoint=bpoint
        self._direction=direction
        self._lrange=lrange

    def has_lrange(self):
        '''
            whether has default lrange
        '''
        return self._lrange is not None

    def get_lrange(self):
        '''
            get default lrange
        '''
        return self._lrange

    def get_points_along(self, lengths):
        '''
            get coordinates of points
                with given lengths from base point along the curve

            return coordiates array
                used in `scipy.ndimage.map_coordinates`
        '''
        raise NotImplementedError

    def sampler_along(self, lengths, order=1, **kwargs):
        '''
            return sampler along the curve
                in points with given `lengths`

            Optional parameters:
                order, kwargs:
                    used in `scipy.ndimage.map_coordinates`

                    order: int
                        order of the spline interpolation
                        in the range 0-5

                        in scipy, default is 3
                        here use 1

                    other parameters:
                        see `scipy.ndimage.map_coordinates` for detail
        '''
        coords=self.get_points_along(lengths)
        return CurveSampler(lengths, coords, curve=self, order=order, **kwargs)

    ## frequently used sampler
    def sampler_num(self, s0, s1, n, endpoint=True, **kwargs):
        '''
            sample in n points in length range [s0, s1]
        '''
        if s0 is None or s1 is None:
            l0, l1=self._lrange
            if s0 is None:
                s0=l0
            if s1 is None:
                s1=l1

        lengths=np.linspace(s0, s1, n, endpoint=endpoint)
        return self.sampler_along(lengths, **kwargs)

    def sampler_step(self, s0, s1, ds, **kwargs):
        '''
            uniformly sample in a interval
                for a given `step`
        '''
        if s0 is None or s1 is None:
            l0, l1=self._lrange
            if s0 is None:
                s0=l0
            if s1 is None:
                s1=l1
                
        lengths=np.arange(s0, s1, ds)
        return self.sampler_along(lengths, **kwargs)

    def sampler_num_bpoint(self, s, n, **kwargs):
        '''
            sample in a symmetrical interval
                respecting to base point
        '''
        return self.sampler_num(-s, s, n, **kwargs)

    def sampler_step_bpoint(self, s, ds, bpoint=True, **kwargs):
        '''
            sample in a symmetrical interval
                respecting to base point

            :param bpoint: bool
                whether to include bpoint
        '''
        if not bpoint:
            return self.sampler_step(-s, s, ds, **kwargs)

        lengths=np.arange(0, s, ds)
        lengths=np.concatenate([np.flip(-lengths[1:]), lengths])
        return self.sampler_along(lengths, **kwargs)

class CurveSampler:
    '''
        callable class for sampling along a curve
    '''
    def __init__(self, lengths, coords, curve=None, **kwargs):
        '''
            init

            Parameters:
                lengths: 1d array
                    lengths of sampling points along the curve

                coords: ndarray
                    coordinates of points in image
                    used in `scipy.ndimage.map_coordinates`

                kwargs: optional keyword args
                    used in `scipy.ndimage.map_coordinates`
        '''
        self._lengths=np.array(lengths)
        self._coords=np.array(coords)

        self._curve=curve

        self._kwargs=kwargs

    def __call__(self, image):
        '''
            interpolation in points
        '''
        return map_coordinates(image, self._coords, **self._kwargs)

    # properties
    @property
    def lengths(self):
        '''
            lengths along curve of sampling points
        '''
        return np.array(self._lengths)

    @property
    def coords(self):
        '''
            array of coords,

            each column is for a point
            each row is for a dim
        '''
        return np.array(self._coords)
    
    @property
    def curve(self):
        '''
            curve object holding the sampler
        '''
        return self._curve