#!/usr/bin/env python3

'''
    class of models

    Transforming between some models is also allowed
        like from 'expdisk' to 'sersic'

    Note:
        some transforamtions allowed here are not reversible
            like from 'sersic' to 'expdisk'
        these are just empirical treating
'''

import warnings

from .collection import GFSlotsDict
from .dtype import is_str_type, is_vec_type
from .parameter import Parameter

class Model(GFSlotsDict):
    '''
        basi class to handle model of galfit
    '''

    # some setups, see metaclass `MetaSlotsDict` for detail
    keys_sorted=[*'0123456789', '10', 'Z']
    keys_optional=set('0Z')

    keys_alias={
        '0': ['name', 'modname'],
        '1': ['x0'],
        '2': ['y0'],
        '3': ['mag'],
        '4': ['re'],
        '5': ['n'],
        '9': ['ba'],
        '10': ['pa'],
        'Z': ['skip']
    }

    keys_comment={
        '0' : 'Component type',
        '1' : 'Position x, y',
        '3' : 'Integrated magnitude',
        '4' : 'R_e (effective radius) [pix]',
        '5' : 'Sersic index n (de Vaucouleurs n=4)',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
        'Z' : 'Skip this model? (yes=1, no=0)'
    }

    ## values example for all models
    values_example={i: Parameter(0) for i in keys_sorted[1:-1]}
    values_example['0']=''
    values_example['Z']=0

    ## str format
    _fmt_float='%.4f'
    _line_fmt2='%2s) %s'            # formt for 2 fields
    _line_fmt3='%2s) %-22s #  %s'   # formt for 3 fields

    # reload init_class
    @classmethod
    def init_class(cls):
        '''
            reload init_class to do additional action to class

            like copy some existed setup in Model
        '''
        # some check 
        assert cls.keys_sorted[0]=='0' and cls.keys_sorted[-1]=='Z'

        # copy attrs
        if cls.__name__!='Model':  # no do to :class Model
            cls.copy_to_subclass()

        super().init_class()

    @classmethod
    def copy_to_subclass(cls):
        '''
            copy default setup from parent to subclass
        '''
        # values default of mode name
        cls.values_default={'0': cls.get_model_name()}

        # copy default setup from parent
        props_copy=['keys_alias', 'values_example', 'keys_comment',
                    'values_default']
        parent=cls.__bases__[0]   # only copy from first bases

        for prop in props_copy:
            if prop not in cls.__dict__:
                continue

            val=getattr(cls, prop)
            val0=getattr(parent, prop)

            for k in cls.keys_sorted:
                if k not in val and k in val0:
                    val[k]=val0[k]

    # methods about model
    ## special model
    @classmethod
    def is_sky(cls):
        '''
            wheter the model is for sky

            there would be some special treatment for sky model
        '''
        return cls.get_model_name()=='sky'

    @classmethod
    def need_psize(cls):
        '''
            wheter the model need pixel size (Parameter P in header of galfit file)
                to calculate suface brightness in Parameter (3)
                    instead of integrated magnitude
        '''
        mods=set(['nuker', 'ferrer', 'king', 'edgedisk'])
        name=cls.get_model_name()
        return name in mods

    ## general way for transformation between models
    def _gen_to_other_model(self, mod, warn=True):
        '''
            a general way to transform to other models

            Parameter:
                mod: galfit model class, or str
        '''
        assert self.is_gf_model_class(mod) or is_str_type(mod)
        if is_str_type(mod):
            mod=self.get_model_class(mod)

        if warn:
            m0=self.get_model_name()
            m1=mod.get_model_name()
            # warnings.warn('CAVEAT: general transform from \'%s\' to \'%s\'. '
            #               'Use it cautiously' % (m0, m1))
            print('WARNING: general transform from \'%s\' to \'%s\'. '
                        'Use it cautiously' % (m0, m1))

        m=mod()
        m.Z=self.Z

        # keys
        keys_now=self.get_all_modvars()
        keys_set=[i for i in keys_now if self.is_val_known_key(i)]

        keys_new=m.get_all_modvars()

        if warn:
            # keys not found in current object
            notfound=[i for i in keys_new if i not in set(keys_now)]

            # unset fitting pars
            keys_unset=[i for i in keys_now if not self.is_val_known_key(i)]

            # keys to be discarded in new object
            discarded=[i for i in keys_set if i not in set(keys_new)]

            if notfound:
                # warnings.warn('fitpars not found in current: [%s]' % (','.join(notfound)))
                print('WARNING: fitpars not found in current: [%s]' % (','.join(notfound)))

            if keys_unset:
                # warnings.warn('fitpars to discard in new: [%s]' % (','.join(discarded)))
                print('WARNING: unest pars in current: [%s]' % (','.join(keys_unset)))

            if discarded:
                # warnings.warn('fitpars to discard in new: [%s]' % (','.join(discarded)))
                print('WARNING: fitpars to discard in new: [%s]' % (','.join(discarded)))

        # set coincident keys
        keys=[i for i in keys_new if i in set(keys_set)]
        if keys:
            vals=self.get_modvars(keys, return_dict=True)
            m.set_modvars_val(vals)

        return m

    ### graph algorithm to find method for implicit models transform
    @classmethod
    def has_direct_trans(cls, mod):
        '''
            whether having direct transformation to a model
                that means a method developed explicitly
        '''
        assert is_str_type(mod)
        return hasattr(cls, 'to_'+mod)

    def mod_trans_to(self, mod, **kwargs):
        '''
            transform to a mod

            besides the explicitly designed method,
                implicit transforming is also supported based on graph algorithm
                    e.g. from sersic to edgedisk through expdisk

            Parameter:
                mod: str, galfit model class or instance
        '''
        if not is_str_type(mod):
            if is_gf_model_instance(mod) or is_gf_model_class(mod):
                mod=mod.get_model_name()
            else:
                raise Exception('only support str, galfit model class or instance, '
                                'but got '+type(mod).__name__)

        mod_now=self.get_model_name()

        if mod==mod_now:
            self.copy()

        if self.has_direct_trans(mod):
            return getattr(self, 'to_'+mod)(**kwargs)

        # find a path from one model to another
        ## explicit developed
        mods=list(self.get_all_models().keys())
        funcs={}
        to_mod=False

        for m in mods:
            c=self.get_model_class(m)
            for n in mods:
                if n==m:
                    continue

                if c.has_direct_trans(n):
                    if m not in funcs:
                        funcs[m]={}
                    funcs[m][n]=getattr(c, 'to_'+n)

                    if n==mod:
                        to_mod=True

        if not to_mod: # no method from a model
            raise Exception('cannot transform from %s to %s' % (mod_now, mod))

        ## Dijkstra algorithm to find path from self to mod

        funcslist={mod_now: []}  # functions list starting from current
        tovisit=[mod_now]
        visited=set()

        while tovisit:
            m=tovisit[0]
            del tovisit[0]

            visited.add(m)

            if m not in funcs:
                continue

            fs=funcslist[m]
            if mod in funcs[m]:  # found mod
                funcslist[mod]=fs+[funcs[m][mod]]
                break

            for t in funcs[m]:
                if t in visited:
                    continue

                tovisit.append(t)
                funcslist[t]=fs+[funcs[m][t]]

        if mod not in funcslist:  # no path to mod
            raise Exception('cannot transform from %s to %s' % (mod_now, mod))

        m=self
        for f in funcslist[mod]:
            m=f(m, **kwargs)

        return m

    ## model name
    @classmethod
    def get_model_name(cls):
        '''
            model name
        '''
        return cls.__name__.lower()

    ## implemented models
    @staticmethod
    def get_all_models():
        '''
            return a map between model name and its class
        '''
        return {m.__name__.lower(): m for m in Model.__subclasses__()}

    @staticmethod
    def get_model_class(name):
        '''
            return a class for a given model name
        '''
        return Model.get_all_models()[name.lower()]

    @staticmethod
    def is_gf_model_instance(obj):
        '''
            whether `obj` is an instance of galfit model
                but it could not be the instance of Model
        '''
        return isinstance(obj, Model) and type(obj) is not Model

    @staticmethod
    def is_gf_model_class(cls):
        '''
            whether `obj` is a class for galfit model
                but it could not be Model
        '''
        # issubclass() arg 1 must be a class
        return isinstance(cls, type) and \
               issubclass(cls, Model) and cls is not Model

    # string representation
    def line_for_print_model_name(self):
        '''
            line for model name
        '''
        key='0'
        name=self.name
        comments='Component type'

        return self._line_fmt3 % (key, name, comments)

    def strprint_of_val_key(self, key, ignore_unset=False):
        '''
            reload function for val str for key
        '''
        if not self.is_sky():
            if key=='2':  # merge '2' to '1'
                return None
            if key=='1':
                if (not ignore_unset) or \
                   (self.is_val_known_key('1') and self.is_val_known_key('2')):

                    x0=self.get_val('1')
                    y0=self.get_val('2')

                    sx=x0.str_val()
                    sy=y0.str_val()

                    s='%s %s  %i %i' % (sx, sy, x0.state, y0.state)

                    return s

        return super().strprint_of_val_key(key, ignore_unset=ignore_unset)

    # model variants to fit via GalFit program
    def get_all_modvars(self):
        '''
            return a list of key, each for a model variant
        '''
        keys=[]
        for k in self.keys_sorted:
            if self.is_modvar_key(k):
                keys.append(k)
        return keys

    def is_modvar_key(self, key):
        '''
            determine whether a key is a model variant
        '''
        key=self.get_std_key(key)
        return self.is_valid_key(key) and key not in '0Z'

    def is_xyvar_key(self, key):
        '''
            if key is '1' (not alias x0), it might mean setting to both xy
        '''
        return (not self.is_sky()) and key=='1'

    ## set methods
    def set_modvar_val(self, key, val):
        '''
            set a model variant

            when key='1' and `val` is of str type with 4 fields after `split`,
                set both xy
            This is frequently used when loading galfit standard file
        '''
        assert self.is_modvar_key(key)

        # for xy parameters
        if self.is_xyvar_key(key) and is_str_type(val):
            val=val.split()
            if len(val)==4:
                self.set_modvar_val('1', val[::2])
                self.set_modvar_val('2', val[1::2])
                return

        if not self.is_set_key(key):
            if not self.is_opt_key(key):
                return super().set_prop(key, val)
            self.touch_opt_key(key)

        self.get_val(key).update(val)

    def update_modvar(self, key, **kwargs):
        '''
            update state (value, state, uncertainty)
                of a model variant
        '''
        assert self.is_modvar_key(key)

        if not self.is_set_key(key):
            if not self.is_opt_key(key):
                raise Exception('cannot update missing required parameter: '
                                +self.get_key_name(key))
            self.touch_opt_key(key)
        self.get_val(key).update(**kwargs)

    ## batch set of values
    def set_modvars_val(self, vals, keys=None):
        '''
            batch set to model variants' value

            Parameters:
                vals: dict, vector
                    if dict, it has form {key: val}
                    if vector, use `keys` as key for corresponding value
                        if keys is None, use all model variants
        '''
        if is_vec_type(vals):
            if keys is None:
                keys=self.get_all_modvars()
            assert len(keys)==len(vals)
            vals=dict(zip(keys, vals))
        elif not isinstance(vals, dict):
            raise Exception('only support vector or dict for vals, but got '
                            +type(vals).__name__)

        for k, v in vals.items():
            self.set_modvar_val(k, v)

    def get_modvars(self, keys=None, fetch_val=False, return_dict=False):
        '''
            return list of model variants

            if not `fetch_val`, return list of objects for parameters
                otherwise, only fetch its value

            `return_dict`: return dict
        '''
        if keys is None:
            keys=self.get_all_modvars()

        pars=[]
        for k in keys:
            assert self.is_modvar_key(k)
            
            v=self.get_val(k)
            if fetch_val:
                v=v.val

            pars.append(v)

        if return_dict:
            pars=dict(zip(keys, pars))

        return pars

    # reload `set_prop` to handle model variants
    def set_prop(self, key, val):
        '''
            reload `set_prop` for model variants
        '''
        if self.is_modvar_key(key):
            return self.set_modvar_val(key, val)
        super().set_prop(key, val)

    # state of model variant: free or frozen during fit of GalFit
    ## set methods
    def set_modvar_state(self, state, pars=None):
        '''
            set fit state (free/freeze to fit) for model variants

            if `pars` is None, do to all model variants

            `state` could be int or str
                for str, it could be str of int, or 'free'/'freeze'
        '''
        if pars is None:
            pars=self.get_all_modvars()

        for k in pars:
            self.update_modvar(k, state=state)

    def free(self, pars=None):
        '''
            free part/all model variants
                if `pars` not given or None, all free
        '''
        self.set_modvar_state('free', pars)

    def freeze(self, pars=None):
        '''
            freeze part/all model variants
                similar as method `free`
        '''
        self.set_modvar_state('freeze', pars)

    ## get methods
    def get_free_modvars(self):
        '''
            get model variants free to fit

            return list of user-friendly key name
        '''
        return [self.get_key_name(k)
                    for k, v in self.get_modvars(return_dict=True).items()
                        if v.is_free()]


## frequently used models
class Sersic(Model):
    '''
        Sersic Profile
    '''
    # setup for model
    keys_sorted=[*'0123459', '10', 'Z']

    # transform to other models
    def to_devauc(self, warn=True):
        '''
            to De Vaucouleurs model
        '''
        name='devauc'
        if warn:
            if self.is_val_known_key('n') and self.n.val!=4:
                name0=self.get_model_name()
                print('WARNING: irreversible transform from \'%s\' to \'%s\''
                        % (name0, name))

        return self._gen_to_other_model(name, warn=False)

    def to_expdisk(self, warn=True):
        '''
            to Exponential disk model
        '''
        name='expdisk'
        if warn:
            if self.is_val_known_key('n') and self.n.val!=1:
                name0=self.get_model_name()
                print('WARNING: irreversible transform from \'%s\' to \'%s\''
                        % (name0, name))

        m=self._gen_to_other_model(name, warn=False)
        if m.is_val_known_key('rs'):
            m.rs*=1/1.678   # re to rs

        return m

class Sky(Model):
    '''
        Background Sky
    '''
    # setup for model
    keys_sorted='0123Z'
    keys_optional=set('0123Z')

    keys_alias={
        '1': ['bkg'],
        '2': ['dbdx'],
        '3': ['dbdy'],
    }

    keys_comment={
        '1' : 'Sky background [ADUs]',
        '2' : 'dsky/dx [ADUs/pix]',
        '3' : 'dsky/dx [ADUs/pix]',
    }

    ## str format
    _fmt_float='%.3e'

class Expdisk(Model):
    '''
        Exponential Disk Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

    keys_alias={
        '4': ['rs'],
    }

    keys_comment={
        '4' : 'R_s (disk scale-length) [pix]',
    }

    # transform to other models
    def to_sersic(self, n_free=False, warn=False):
        '''
            to Sersic model

            it compatible from expdisk to sersic
        '''
        name='sersic'
        if warn:
            name0=self.get_model_name()
            # destructive, but not irreversible
            print('Notation: transform from \'%s\' to \'%s\''
                    % (name0, name))

        m=self._gen_to_other_model(name, warn=False)
        if m.is_val_known_key('rs'):
            m.re*=1.678   # rs to re (effective radius)
        m.n=1
        m.n.freeze()  # explicitly freeze

        # state of n is 0 by default
        if n_free:
            m.n.free()

        return m

    def to_edgedisk(self, warn=True):
        '''
            to Edge-on disk model

            inverse operation is `Edgedisk.to_expdisk`
        '''
        name='edgedisk'
        if warn:
            name0=self.get_model_name()
            # destructive, but not irreversible
            print('WARNING: destructive transform from \'%s\' to \'%s\''
                    % (name0, name))

        m=self._gen_to_other_model(name, warn=False)

        # scale length is '5' in edgedisk, but '4' in expdisk
        rs=self.rs
        m.set_prop('5', rs)

        # scale height ('4' in edgedisk) from ba ('9' in expdisk) and scale length
        ba=self.ba

        hs=rs.val*ba.val
        shs=Parameter.state_of_comb_pars(rs, ba)  # free/freeze

        ## free to fit if rs or ba is free
        m.set_prop('4', (hs, shs))

        return m

class Edgedisk(Model):
    '''
        Edge-On Disk Profile
    '''
    # setup for model
    keys_sorted=[*'012345', '10', 'Z']
    keys_alias={
        '3': ['mu', 'sb'],
        '4': ['hs', 'dh'],  # scale height
        '5': ['rs', 'dl'],  # scale length
    }

    keys_comment={
        '3' : 'central surface brightness [mag/arcsec^2]',
        '4' : 'disk scale-height [Pixels]',
        '5' : 'disk scale-length [Pixels]',
    }

    def to_expdisk(self, warn=True):
        '''
            to Exponential disk model

            inverse operation is `Expdisk.to_edgedisk`
        '''
        name='expdisk'
        if warn:
            name0=self.get_model_name()
            # destructive, but not irreversible
            print('WARNING: destructive transform from \'%s\' to \'%s\''
                    % (name0, name))

        m=self._gen_to_other_model(name, warn=False)

        # scale length is '4' in expdisk, but '5' in edgedisk
        rs=self.rs
        m.set_prop('4', rs)

        # ba ('9' in expdisk) from scale height ('4' in edgedisk) and scale length
        hs=self.hs

        assert hs.val>0
        ba=hs.val/rs.val
        sba=Parameter.state_of_comb_pars(rs, hs)  # free/freeze

        ## free to fit if rs or ba is free
        m.set_prop('9', (ba, sba))

        return m

class Devauc(Model):
    '''
        de Vaucouleurs Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

    # transform to other models
    def to_sersic(self, n_free=False, warn=False):
        '''
            to Sersic model

            it compatible from de Vaucouleurs to sersic
        '''
        name='sersic'
        if warn:
            name0=self.get_model_name()
            # destructive, but not irreversible
            print('Notation: transform from \'%s\' to \'%s\''
                    % (name0, name))

        m=self._gen_to_other_model(name, warn=False)
        m.n=4
        m.n.freeze()  # explicitly freeze

        # state of n is 0 by default
        if n_free:
            m.n.free()

        return m

class PSF(Model):
    '''
        PSF Profile
    '''
    # setup for model
    keys_sorted=[*'0123', 'Z']

## other models, not used so frequently for me
class Nuker(Model):
    '''
        Nuker Profile
    '''
    # setup for model
    keys_sorted=[*'012345679', '10', 'Z']

    keys_alias={
        '3': ['ub'],  # mu at Rb
        '4': ['rb'],
        '5': ['alpha'],
        '6': ['beta'],
        '7': ['gamma'],
    }

    keys_comment={
        '3' : 'mu(Rb) [surface brightness mag. at Rb]',
        '4' : 'Rb [pixels]',
        '5' : 'alpha (sharpness of transition)',
        '6' : 'beta (outer powerlaw slope)',
        '7' : 'gamma (inner powerlaw slope)',
    }

class Moffat(Model):
    '''
        Moffat Profile
    '''
    # setup for model
    keys_sorted=[*'0123459', '10', 'Z']

    keys_alias={
        '4': ['fwhm'],
        '5': ['pl'],
    }

    keys_comment={
        '4' : 'FWHM [Pixels]',
        '5' : 'powerlaw',
    }

class Ferrer(Model):
    '''
        Modified Ferrer Profile
    '''
    # setup for model
    keys_sorted=[*'01234569', '10', 'Z']

    keys_alias={
        '3': ['mu', 'sb'],  # sb for surface brightness
        '4': ['tr'],
        '5': ['alpha'],
        '6': ['beta'],
    }

    keys_comment={
        '3' : 'Central surface brightness [mag/arcsec^2]',
        '4' : 'Outer truncation radius [pix]',
        '5' : 'Alpha (outer truncation sharpness)',
        '6' : 'Beta (central slope)',
    }

class Gaussian(Model):
    '''
        Gaussian Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

    keys_alias={
        '4': ['fwhm'],
    }

    keys_comment={
        '4' : 'FWHM [Pixels]',
    }

class King(Model):
    '''
        Empirical (Modified) King Profile
    '''
    # setup for model
    keys_sorted=[*'01234569', '10', 'Z']

    keys_alias={
        '3': ['mu', 'sb'],
        '4': ['rc'],
        '5': ['rt'],
        '6': ['alpha'],
    }

    keys_comment={
        '3' : 'Central surface brightness [mag/arcsec^2]',
        '4' : 'Rc',
        '5' : 'Rt',
        '6' : 'alpha',
    }
