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
from .constraint import Constraints
from .fitlog import FitLogs

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

        self.__dict__['comments']=[]  # comments, one entry for a line

        self.__dict__['_attrs']={}    # some attributes, like Chi^2/nu

        # load file
        if fname is None:
            return

        self.load_file(fname, **kwargs)

    def reset(self):
        '''
            reset the object
        '''
        self.header.reset()
        self.clear_comps()
        self.workdir=''

        self.clear_comments()
        self.clear_attrs()

    # attributes:
    @property
    def attrs(self):
        '''
            return copy of attributes

            not expected to modify attrs in object directly
        '''
        return self._attrs.copy()

    def add_attr(self, k, v):
        '''
            add an attribute
        '''
        self._attrs[k]=v

    def get_attr(self, k):
        '''
            get attribute
        '''
        return self._attrs[k]

    def has_attr(self, k):
        '''
            whether or not to have an attribute
        '''
        return k in self._attrs

    def clear_attrs(self):
        self._attrs.clear()

    ## frequently used
    ### attr about src file
    _ATTR_SRCFNAME='srcfname'
    def add_attr_srcfname(self, v):
        '''
            add attribute for src file name
        '''
        self.add_attr(self._ATTR_SRCFNAME, v)

    def get_attr_srcfname(self):
        '''
            return src file name
        '''
        return self.get_attr(self._ATTR_SRCFNAME)

    def has_attr_srcfname(self):
        '''
            whether having src file name
        '''
        return self.has_attr(self._ATTR_SRCFNAME)

    ### attr about menu file
    _ATTR_INITFNAME='initfname'
    def add_attr_initfname(self, v):
        self.add_attr(self._ATTR_INITFNAME, v)

    def get_attr_initfname(self):
        return self.get_attr(self._ATTR_INITFNAME)

    def has_attr_initfname(self):
        return self.has_attr(self._ATTR_INITFNAME)

    ### attrs about chi square
    _ATTR_CHISQ='chisq'
    _ATTR_NDOF='ndof'
    _ATTR_CHISQNU='reduce_chisq'
    def add_attrs_chisqs(self, chisq, ndof, reduce_chisq):
        '''
            add attributes
                for Chi^2, ndof, Chi^2/nu

            Parameters:
                chisq, ndof, reduce_chisq: str or numbers
        '''
        self.add_attr(self._ATTR_CHISQ, float(chisq))
        self.add_attr(self._ATTR_NDOF, int(ndof))
        self.add_attr(self._ATTR_CHISQNU, float(reduce_chisq))

    def get_attr_reduce_chisq(self):
        '''
            return attribute of reduced chisq
        '''
        return self.get_attr(self._ATTR_CHISQNU)
    def get_attr_chisq(self):
        '''
            return attribute of reduced chisq
        '''
        return self.get_attr(self._ATTR_CHISQ)
    def get_attr_ndof(self):
        '''
            return attribute of reduced chisq
        '''
        return self.get_attr(self._ATTR_NDOF)

    def has_attr_reduce_chisq(self):
        '''
            whether having attr for reduce chisq
        '''
        return self.has_attr(self._ATTR_CHISQNU)
    def has_attr_chisq(self):
        '''
            whether having attr for chisq
        '''
        return self.has_attr(self._ATTR_CHISQ)
    def has_attr_ndof(self):
        '''
            whether having attr for reduce chisq
        '''
        return self.has_attr(self._ATTR_NDOF)

    ## implement frequently-used attributes as property
    @property
    def srcfname(self):
        return self.get_attr_srcfname()
    @property
    def initfname(self):
        return self.get_attr_initfname()

    @property
    def has_srcfname(self):
        return self.has_attr_srcfname()
    @property
    def has_initfname(self):
        return self.has_attr_initfname()

    @property
    def chisqnu(self):
        return self.get_attr_reduce_chisq()
    @property
    def chisq(self):
        return self.get_attr_chisq()
    @property
    def ndof(self):
        return self.get_attr_ndof()

    @property
    def has_chisqnu(self):
        return self.has_attr_reduce_chisq()
    @property
    def has_chisq(self):
        return self.has_attr_chisq()
    @property
    def has_ndof(self):
        return self.has_attr_ndof()

    # load galfit file

    ## re pattern for line of variants: N) xxx ... # comments
    _PATTERN_VARLINE=re.compile(r'^\s*([0-9a-zA-Z.]+)\)\s+'
                                r'([^#]+?)(?:\s+#|\s*$)')

    ## re pattern for line of Chi^2
    _S_PAIR=r'(Chi\^2/nu|Chi\^2|Ndof)\s*=\s*([\d\.+\-]+)'
    _PATTERN_CHISQLINE=re.compile((r'^#\s*' '{0}{1}{0}{1}{0}' '$')
                                            .format(_S_PAIR, r',\s*'))

    ## re pattern for input menu file
    _PATTERN_INPUTLINE=re.compile(r'^#\s*Input menu file:\s*(.*)$')

    def load_file(self, fname,
                        ignore_dirname=False, force_wd_abspath=False,
                        reset_before_load=True,
                        remember_srcfname=True,
                        parse_chisq=False, parse_input=False,
                        parse_all=False):
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

                remember_srcfname: bool
                    if true, remember file name of this source file as an attribute
                        in which its absolute path is stored

                parse_chisq: bool
                    whether to parse chisq line
                        which exists for result file of galfit

                parse_input: bool
                    whether to parse line for input menu file

                parse_all: bool
                    if True, overwrite previous 'parse_*' args to True
        '''
        # kwargs
        if parse_all:
            parse_chisq=True
            parse_input=True

        # reset
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

        # source file name
        if remember_srcfname:
            self.add_attr_srcfname(os.path.abspath(fname))

        # load file
        ptn_varline=self._PATTERN_VARLINE
        ptn_chisqline=self._PATTERN_CHISQLINE
        ptn_inputline=self._PATTERN_INPUTLINE
        with open(fname) as f:
            for line in f:
                # chi square line
                if parse_chisq:
                    m=ptn_chisqline.match(line)
                    if m:
                        pairs=m.groups()
                        items=dict(zip(pairs[::2], pairs[1::2]))

                        self.add_attrs_chisqs(
                            *[items[k] for k in 'Chi^2 Ndof Chi^2/nu'.split()])
                        continue

                # input menu file line
                if parse_input:
                    m=ptn_inputline.match(line)
                    if m:
                        initf=m.groups()[0]
                        self.add_attr_initfname(initf)
                        continue

                # parameter line
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
    def __str__(self, print_comments=True):
        '''
            user-friendly string

            Parameters:
                print_comments: bool
                    whether to print comments
        '''
        lines=[]

        if print_comments and self.comments:
            lines.append('')
            
            for entry in self.comments:
                lines.append('# %s' % entry)

            lines.append('')

        lines.append('='*80)
        lines.append('# IMAGE and GALFIT CONTROL PARAMETERS')
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
    def writeto(self, fname, print_comments=True):
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
            f.write(self.__str__(print_comments=print_comments))

    # comments to galfit file
    def add_comment(self, s):
        '''
            add a comment

            in output print, it would be shown as a line
        '''
        assert is_str_type(s)  # only support string type

        self.comments.append(s)

    def clear_comments(self):
        '''
            clear comments
        '''
        self.comments.clear()

    ## frequently-used comments
    def add_comment_item(self, key, val):
        '''
            add comment with pair form (key, val)
        '''
        assert is_str_type(key) and is_str_type(val)

        s='%s: %s' % (key, val)
        self.add_comment(s)

    def add_comment_srcfile(self, src=None, relpath=True, prefix='source file'):
        '''
            add comment for source galfit file

            Parameters:
                src: str, None
                    path of source file

                    if None, use attribute `srcfname`

                relpath: bool
                    if True, use path relative to work dir

                prefix: str
                    key name of the comment
        '''
        if src is None:
            src=self.get_attr_srcfname()

        assert is_str_type(src) and is_str_type(prefix)

        if relpath:
            src=os.path.relpath(src, self.workdir)

        self.add_comment_item(prefix, src)

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

        # super().__getattr__(prop)
        raise AttributeError('unsupported prop for __getattr__: %s' % prop)

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

    # add header params to components
    def set_psize_to_comps(self, force=False):
        '''
            set pixel size to models which need it
                e.g. edgeon disk
        '''
        psize=self.header.psize
        for comp in self.comps:
            if not comp.need_psize():
                continue

            comp.set_psize(psize, force=force)

    def set_psize_to_comp(self, index, force=False):
        '''
            set psize to ith comp
        '''
        comp=self.comps[index]
        psize=self.header.psize

        comp.set_psize(psize, force=force)

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

    def clear_comps(self):
        '''
            clear all components
        '''
        self.comps.clear()

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
    def trans_comp_to(self, index, mod, warn=True, inplace=True):
        '''
            transform component to a given model

            Parameter:
                index: int
                    index of component to transform

                mod: str, galfit model class or instance
                    see `Model:mod_trans_to` for detail

                inplace: bool, default True
                    whether to change comp in-place

                    if not,
                        return changed comp
        '''
        comp=self.comps[index]

        # set psize
        psize=self.header.psize
        if comp.need_psize():
            comp.set_psize(psize, force=False)

        # trans
        comp=comp.mod_trans_to(mod, warn=warn, psize=psize)
        if comp.need_psize():
            comp.set_psize(psize, force=False)

        if not inplace:
            return comp

        self.comps[index]=comp

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

    # work dir
    def chdir_to(self, dest, keep_header=False, skip_output=True):
        '''
            change work dir to new one `dest`

            Parameters:
                dest: str
                    new work directory

                keep_header: bool
                    whether to change header parameters

                    if not, all header parameters related with file system would
                        be changed to follow location in file system

                skip_output: bool
                    if True, not change path of output image
        '''
        assert is_str_type(dest)

        oldwd=self.workdir
        newwd=dest

        if not keep_header:
            for par in self.header.get_file_pars(skip_output=skip_output):
                if self.header.is_par_none(par):
                    continue

                oldfname=self.header.get_val(par)

                path=os.path.join(oldwd, oldfname)
                newfname=os.path.relpath(path, newwd)

                self.header.set_prop(par, newfname)

        self.workdir=newwd

    def force_wd_abspath(self):
        '''
            force work dir to abspath
        '''
        self.workdir=os.path.abspath(self.workdir)

    # header params related to file system
    def get_path_of_file_par(self, par, abspath=False):
        '''
            get path of a file par

            if 'none', return None

            Parameters:
                abspath: bool
                    if True, return abspath
        '''
        assert self.header.is_file_par(par)

        if self.header.is_par_none(par):
            return None

        p=os.path.join(self.workdir, self.header.get_val(par))
        if abspath:
            p=os.path.abspath(p)

        return p

    def set_path_to_file_par(self, par, path, relpath=True):
        '''
            set path to a param related with file system

            Parameters:
                par: str
                    parmeter name

                path: str
                    path name to set for the parameter

                relpath: bool
                    if True, use path relative to work dir `self.workdir`
                    otherwise, just use `path` given
        '''
        assert self.header.is_file_par(par)

        if relpath:
            path=os.path.relpath(path, self.workdir)

        self.header.set_prop(par, path)

    ## handle different file
    def load_constraints(self):
        '''
            load constraints file to `Constraints` object

            if 'none', return empty object
        '''
        fname=self.get_path_of_file_par('constraints')

        if fname is None:
            return Constraints()

        return Constraints(fname)

    def set_constraints(self, path, relpath=True):
        '''
            set constraints param with a path
        '''
        self.set_path_to_file_par('constraints', path, relpath=relpath)

    # fitlog file
    def load_fitlogs(self, path=None):
        '''
            load fit.log in work dir of galfit

            Parameters:
                path: str or None
                    if str, it means path for file 'fit.log'
                    if None, use file in work dir
        '''
        if path is None:
            path=self.workdir
        return FitLogs(path)

    def get_fitlog(self, fitlogs=None, as_init_file=False,
                        return_last=True, **kwargs):
        '''
            get related fitlog from list of fit logs
                which might be load from file 'fit.log' in work dir
                    or an Fitlogs object

            Parameters:
                fitlog: str, FitLogs isntance, or None
                    if str, it means path for file 'fit.log'
                    if None, use file in work dir

                as_init_file: bool
                    whether to use filename being loaded, i.e. `srcfname`
                        as init file to query in fitlogs

                    by default, `srcfname` is used as result file

                return_last: bool
                    whether to return last log

                    if False, return list of logs
                        see `FitLogs.get_logs_by_filename` for detail

                optional kwargs: used in method
                    `FitLogs.get_logs_by_filename`
        '''
        if not isinstance(fitlogs, FitLogs):
            fitlogs=self.load_fitlogs(fitlogs)

        if not self.has_attr_srcfname():
            raise Exception('unknown src filename')

        srcf=os.path.basename(self.get_attr_srcfname())

        if as_init_file:
            kws=dict(init=srcf)
        else:
            kws=dict(result=srcf)

            # if has attr `initfname`
            if self.has_attr_initfname():
                initf=self.get_attr_initfname()
                initf=os.path.basename(initf)

                kws['init']=initf

        if return_last:
            kws['index']=-1

        return fitlogs.get_logs_by_filename(**kws, **kwargs)