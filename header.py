#!/usr/bin/env python3

'''
    Header of galfit file
'''

from .collection import GFSlotsDict, register_method_to
from .dtype import is_int_type, is_str_type

class Header(GFSlotsDict):
    '''
        class to handle header of galfit file

        some parameters in header relate to a file in system
            like input image, mask file, sigma fits, et al.
        In `Header`, they are only treated as normal string,
            and properties related with file system are managed by top `GalFit` object
    '''
    # default set up
    ## keys
    keys_sorted='ABCDEFGHIJKOP'  # file writed in this order
    # keys_valid=set(keys_sorted)

    ## user-friendly name of keys
    keys_name=dict(
        A='input image',
        B='output image block',
        C='sigma file',
        D='psf file',
        E='psf sampling factor',
        F='mask file',
        G='constraint file',
        H='fit region',
        I='convolution box',
        J='magnitude zeropoint',
        K='pixel size',   # plate scale (dx, dy), [arcsec per pixel]
        O='display type',
        P='fit mode',
    )

    ## comments of parameters
    keys_comment=dict(
        A='Input data image (FITS file)',
        B='Output data image block',
        C='Sigma image',
        D='Input PSF image',
        E='PSF fine sampling factor relative to data',
        F='Bad pixel mask',
        G='File with parameter constraints (ASCII file)',
        H='Image region',
        I='Size for convolution (x y)',
        J='Magnitude photometric zeropoint',
        K='Plate scale (dx dy)   [arcsec per pixel]',
        O='Display type (regular, curses, both)',
        P='0=optimize, 1=model, 2=imgblock, 3=subcomps',
    )

    ## alias of keys
    keys_alias=dict(  # {key: [alias_names]}
        A=['input'],
        B=['output'],
        C=['sigma'],
        D=['psf'],
        E=['psfFactor'],
        F=['mask'],
        G=['constraints', 'cons'],
        H=['region', 'fitregion', 'xyminmax'],
        I=['conv'],
        J=['zerop'],
        K=['pscale', 'psize'],
        O=['disp'],
        P=['mod'],
    )
    # constructed in metaclass now
    # map_keys_alias=funcs.inverse_alias(keys_alias)

    ## default values
    # values_example
    values_example=dict(
        A='none',
        B='none',        # must give explicitly
        C='none',
        D='none',
        E=1,             # can only be an integer, see readme of galfit
        F='none',
        G='none',
        H=[0, 0, 0, 0],  # must give explicitly
        I=[0, 0],        # must give explicitly
        J=20.,
        K=[1.0, 1.0],    # required for some profiles, but only a shift of mag, like J
        O='regular',
        P='0',
    )
    keys_required=set('BHI')
    # keys_optional=set(keys_sorted).difference()

    ## parameter 'P': mode parameter
    ## 0=optimize, 1=model, 2=imgblock, 3=subcomps
    mode_valid=set('0123')

    ### alias of mode
    mode_alias={
        '0': ['optimize', 'opt', 'o'],
        '1': ['model', 'mod', 'm'],
        '2': ['imgblock', 'block', 'b'],
        '3': ['subcomps', 'sub', 's'],
    }

    #### user-friendly mode
    mode_names={k: a[0] for k, a in mode_alias.items()}

    ## parameter 'O': display parameter
    disp_valid={'regular', 'curses', 'both'}

    ## collect of valid values
    values_valid=dict(
        O=disp_valid,
        P=mode_valid,
    )

    ## collect of value alias
    values_alias=dict(
        P=mode_alias,
    )

    # init: just use super().__init__

    def reset(self):
        '''
            reset header
        '''
        super().reset()

    # parameters related with file system
    @classmethod
    def get_file_pars(cls):
        '''
            return list of parameters related with file system
        '''
        return list('ACDFG')

    @classmethod
    def is_file_par(cls, par):
        '''
            whether a param is a parameter related with file system
        '''
        return cls.get_std_key(par) in 'ACDFG'

    def is_par_none(self, par):
        '''
            whether a param is setted to 'none'

            'none' means not set for the parameter
        '''
        return self.get_val(par)=='none'

    # methods registered to be accessible by top `GalFit` object
    _METHODS_GF=set()

    @classmethod
    def _is_gf_method(cls, funcname):
        '''
            whether a method is expected to be accessed by `GalFit` object
        '''
        return is_str_type(funcname) and funcname in cls._METHODS_GF

    # Parameter P (galfit runing mode)
    @register_method_to(_METHODS_GF)
    def set_gf_mod(self, mod):
        '''
            set Parameter P (galfit runing mode)

            support mod to be string or int
                0=optimize, 1=model, 2=imgblock, 3=subcomps
        '''
        if is_int_type(mod):
            assert 0<=mod<=3
            mod='%i' % mod
        self.set_prop('P', mod)

    @register_method_to(_METHODS_GF)
    def use_fit_mod(self):
        '''
            set optimize mode for galfit input file
        '''
        self.set_gf_mod(0)

    @register_method_to(_METHODS_GF)
    def use_create_mod(self, block=False, subcomps=False):
        '''
            no optimizing, just create images
                1=model, 2=imgblock, 3=subcomps

            2 bool arguments: block, subcomps
                if `subcomps` is true, mode=3 (ignoring `block`)
                otherwise, if `block` is true, mode=2
                           otherwise, mode=1
        '''
        if subcomps:
            mod=3
        elif block:
            mod=2
        else:
            mod=1
        self.set_gf_mod(mod)

    # Parameter H: region
    @register_method_to(_METHODS_GF)
    def get_region_shape(self, xy=True):
        '''
            get shape of region

            Parameters:
                xy: bool, or str
                    what type of shape to return, xy or yx

                    for str, only 'yx' or 'xy'
        '''
        if is_str_type(xy):
            assert xy=='xy' or xy=='yx'

            xy=(xy=='xy')
        else:
            assert isinstance(xy, bool)

        x0, x1, y0, y1=self.get_val('region')
        nx, ny=x1-x0+1, y1-y0+1

        if xy:
            return nx, ny

        return ny, nx