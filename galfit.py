#!/usr/bin/env python3

'''
    top layer to handle the whole formatted input file of galfit

    Such a file contains two parts: header and componets
        which would be handled by different modules

    When loading as a instance, the file is parsing line by line
        during which meaningful lines are labeled by starting chars followed with `)`
'''

import os
import re

from .header import Header
from .model import Model
from .dtype import is_int_type, is_str_type
from .tools import gfname_from_int

class GalFit:
    '''
        class to represent whole input file to galfit

        two parts included in the file: header and components
            header: parameters to run galfit

            components: list of models

        some parameters are related to a file in disk system
            like input image, mask file, sigma fits, et al.
        In `Header` object, they are only treated as normal string

        To relate with file path in system, working directory of galfit is stored in `GalFit` object
            if created from a file, initiated with its `dirname`
            otherwise, like creating empty `GalFit`, initiated with ''
        All actions related with file path is managed in this top object
            leaving `Header` simple work to handle normal string
    '''
    def __init__(self, fname=None, **kwargs):
        '''
            initiation could be done from a galfit file,
                or just return an empty one, waiting to set up

            properties:
                header, comps: information from the galfit
                workdir: work dir to run galfit
        '''
        # two parts: header and components (list of models)
        self.__dict__['header']=Header()
        self.__dict__['comps']=[]     # collection of components

        self.__dict__['workdir']=''   # work dir, where to run galfit

        # load file
        if fname is None:
            return

        self.load_file(fname, **kwargs)

    def reset(self):
        '''
            reset the object
        '''
        self.header.reset()
        self.comps.clear()
        self.workdir=''

    # load galfit file

    ## re pattern for line of variants: N) xxx ... # comments
    _PATTERN_VARLINE=re.compile(r'^\s*([0-9a-zA-Z.]+)\)\s+([^#]+?)(?:\s+#|\s*$)')

    def load_file(self, fname,
                        ignore_dirname=False, force_wd_abspath=False,
                        reset_before_load=True):
        '''
            load a galfit file

            Parameters:
                fname: int, str or Path object
                    filename to load

                    if int,
                        explained as name 'galfit.NN',
                            by function `gfname_from_int`

                ignore_dirname: bool, default False
                    whether to ignore dirname of input file

                    if False, `workdir` would be set to its dirname

                force_wd_abspath: bool, default False
                    whether to force work dir using abspath

                    it works only when not `ignore_dirname`

                reset_before_load: bool
                    if true, all contents are to reset before file loading
        '''
        if reset_before_load:
            self.reset()

        # galfit.NN
        if is_int_type(fname):
            fname=gfname_from_int(fname)

        # workdir
        if not ignore_dirname:
            self.workdir=os.path.dirname(fname)

            if force_wd_abspath:
                self.workdir=os.path.abspath(self.workdir)

        # load file
        ptn_varline=self._PATTERN_VARLINE
        with open(fname) as f:
            for line in f:
                m=ptn_varline.match(line)

                if not m:
                    continue
                
                key, val=m.groups()

                if key in self.header:
                    self.header.set_prop(key, val)
                    continue

                if key=='0':
                    mod=Model.get_model_class(val)()
                    self.comps.append(mod)
                    continue

                if key in self.comps[-1]:
                    self.comps[-1].set_prop(key, val)

    # string representation
    def __str__(self):
        '''
            user-friendly string
        '''
        lines=['='*80,
               '# IMAGE and GALFIT CONTROL PARAMETERS']
        lines.append(str(self.header))
        lines.append('')
        lines.append('# INITIAL FITTING PARAMETERS')
        lines.append('#')
        lines.append('#   For component type, the allowed functions:')
        lines.append('#     sersic, expdisk, edgedisk, devauc,')
        lines.append('#     king, nuker, psf, gaussian, moffat,')
        lines.append('#     ferrer, and sky.')
        lines.append('#')
        lines.append('#   Hidden parameters appear only when specified:')
        lines.append('#     Bn (n=integer, Bending Modes).')
        lines.append('#     C0 (diskyness/boxyness),')
        lines.append('#     Fn (n=integer, Azimuthal Fourier Modes).')
        lines.append('#     R0-R10 (coordinate rotation, for spiral).')
        lines.append('#     To, Ti, T0-T10 (truncation function).')
        lines.append('#')
        lines.append('# '+'-'*78)
        lines.append('#   par)    par value(s)    fit toggle(s)')
        lines.append('# '+'-'*78)
        lines.append('')

        for i, comp in enumerate(self.comps):
            lines.append('# Component number: %i' % (i+1))
            lines.append(str(comp))
            lines.append('')

        lines.append('='*80)

        return '\n'.join(lines)

    ## write to file
    def writeto(self, fname):
        '''
            write to a file

            Parameters:
                fname: int, str or Path object
                    name of file to write

                    if int, write to galfit.NN
        '''
        # galfit.NN
        if is_int_type(fname):
            fname=gfname_from_int(fname)

        with open(fname, 'w') as f:
            f.write(str(self))

    # frequently-used methods to access header parameters or components

    ## getattr/setattr for header params
    def __getattr__(self, prop):
        '''
            direct get of header parameters and some header methods
        '''
        if prop in self.header:
            return getattr(self.header, prop)

        # header methods
        if self.header._is_gf_method(prop):
            return getattr(self.header, prop)

        super().__getattr__(prop)

    def __setattr__(self, prop, val):
        '''
            direct set to header parameters
        '''
        if prop in self.header:
            return setattr(self.header, prop, val)

        super().__setattr__(prop, val)

    ## methods for components
    def __getitem__(self, i):
        '''
            get components
        '''
        assert is_int_type(i) or isinstance(i, slice)
        return self.comps[i]

    def __len__(self):
        '''
            number of components
        '''
        return len(self.comps)

    def __iter__(self):
        '''
            iter along components
        '''
        return iter(self.comps)

    # methods about model components
    ## add/remove/duplicate model
    def add_comp(self, mod, vals=None, index=None, keys=None, Z=None):
        '''
            add a component in `comps` before index `index`
                if `index` is None, insert in the end

            Parameter:
                mod: instance of galfit Model, model class, or str
                    if the latter two,
                        use :param vals, keys, Z to create an instance
        '''
        if not Model.is_gf_model_instance(mod):
            if is_str_type(mod):
                mod=Model.get_model_class(mod)
            elif not Model.is_gf_model_class(mod):
                raise Exception('only accept galfit model instance/class or str as mod, '
                                'but got '+type(mod).__name__)
            mod=mod()
            if vals is not None:
                mod.set_modvars_val(vals, keys=keys)

            if Z is not None:
                mod.Z=Z

        # insert
        if index is None:
            index=len(self.comps)
        self.comps.insert(index, mod)

    def del_comp(self, index):
        '''
            delete comp
        '''
        del self.comps[index]

    def dup_comp(self, index, index_dup=None):
        '''
            duplicate component 
                and then insert just after it by default
                    or other index, given by `index_dup`
        '''
        comp=self.comps[index].copy()

        if index_dup is None:
            if index==-1:
                index_dup=len(self.comps)
            else:
                index_dup=index+1

        self.comps.insert(index_dup, comp)

    ### add particular model
    def add_sersic(self, *args, **kwargs):
        '''
            add sersic model
        '''
        self.add_comp('sersic', *args, **kwargs)

    def add_sky(self, *args, **kwargs):
        '''
            add sky model
        '''
        self.add_comp('sky', *args, **kwargs)

    ## model transform inplace
    def trans_comp_to(self, index, mod, warn=True):
        '''
            transform component to a given model

            Parameter:
                index: int
                    index of component to transform

                mod: str, galfit model class or instance
                    see `Model:mod_trans_to` for detail
        '''
        comp=self.comps[index]

        self.comps[index]=comp.mod_trans_to(mod, warn=warn)

    # methods to handle all model variants of all components
    ## free/freeze state
    def set_modvar_state_comps(self, state, comps=None):
        '''
            set state of model variants of all/part components

            Parameters:
                state: scalar
                    free or freeze state

                comps: None, or list of int
                    components to set state
        '''
        if comps is None:
            objs=self.comps
        else:
            objs=[self.comps[i] for i in comps]

        for obj in objs:
            obj.set_modvar_state(state)

    def free(self, comps=None):
        '''
            free all model variants to all/part components
        '''
        self.set_modvar_state_comps('free', comps)

    def freeze(self, comps=None):
        '''
            freeze all model variants to all/part components
        '''
        self.set_modvar_state_comps('freeze', comps)
